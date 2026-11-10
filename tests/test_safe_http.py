import socket
import unittest
from unittest.mock import Mock, patch

from qa_tools.safe_http import _PinnedHTTPConnection, safe_get, validate_url


PUBLIC_DNS = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]


class SafeHttpTests(unittest.TestCase):
    def test_rejects_private_and_loopback_ip_literals(self):
        for url in ("http://127.0.0.1/", "http://10.1.2.3/", "http://169.254.169.254/"):
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, "non-public"):
                validate_url(url)

    @patch("qa_tools.safe_http.socket.getaddrinfo", return_value=PUBLIC_DNS)
    def test_dns_address_is_pinned_for_socket_connection(self, _dns):
        connection = _PinnedHTTPConnection("public.example", 80, "93.184.216.34", 3)
        fake_socket = Mock()
        with patch("qa_tools.safe_http.socket.create_connection", return_value=fake_socket) as connect:
            connection.connect()
        connect.assert_called_once_with(("93.184.216.34", 80), 3, None)
        self.assertIs(connection.sock, fake_socket)
        connection.close()

    @patch("qa_tools.safe_http.socket.getaddrinfo", return_value=PUBLIC_DNS)
    @patch("qa_tools.safe_http._PinnedHTTPConnection")
    def test_redirect_is_returned_not_followed(self, connection_cls, _dns):
        response = Mock(status=302, read=Mock(return_value=b"redirect"))
        response.getheaders.return_value = [("Location", "http://127.0.0.1/admin")]
        connection = connection_cls.return_value
        connection.getresponse.return_value = response
        status, headers, body = safe_get("http://public.example/start")
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], "http://127.0.0.1/admin")
        self.assertEqual(body, b"redirect")
        connection.request.assert_called_once()
        connection.getresponse.assert_called_once()


if __name__ == "__main__":
    unittest.main()
