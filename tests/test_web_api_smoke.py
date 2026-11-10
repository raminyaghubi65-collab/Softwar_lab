import socket
import unittest
from unittest.mock import patch

from qa_tools.web_api_smoke import smoke_check, validate_url


PUBLIC_DNS = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]


class UrlValidationTests(unittest.TestCase):
    @patch("qa_tools.safe_http.socket.getaddrinfo", return_value=PUBLIC_DNS)
    def test_accepts_public_http_and_https(self, _dns):
        self.assertEqual(validate_url("https://example.com/health"), "https://example.com/health")
        self.assertEqual(validate_url("http://example.com:8000/"), "http://example.com:8000/")

    def test_rejects_relative_and_non_http_urls(self):
        for url in ("/health", "file:///etc/passwd"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_url(url)

    def test_rejects_embedded_credentials(self):
        with self.assertRaises(ValueError):
            validate_url("https://user:secret@example.com/")

    @patch("qa_tools.safe_http.socket.getaddrinfo",
           return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))])
    def test_rejects_loopback_dns(self, _dns):
        with self.assertRaisesRegex(ValueError, "non-public"):
            validate_url("https://internal.example/")

    @patch("qa_tools.safe_http.socket.getaddrinfo",
           return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
                         (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.8", 443))])
    def test_rejects_mixed_public_and_private_dns(self, _dns):
        with self.assertRaisesRegex(ValueError, "non-public"):
            validate_url("https://mixed.example/")


class SmokeCheckTests(unittest.TestCase):
    @patch("qa_tools.web_api_smoke.safe_get", return_value=(200, {"Content-Type": "application/json"}, b'{"ok": true}'))
    def test_passes_expected_json_response(self, mocked):
        result = smoke_check("https://example.com/api/health", expect_json=True)
        self.assertTrue(result.passed)
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json_valid)
        mocked.assert_called_once()

    @patch("qa_tools.web_api_smoke.safe_get", return_value=(200, {}, b"Welcome"))
    def test_fails_when_expected_text_is_missing(self, _mocked):
        result = smoke_check("https://example.com/", expected_text="Dashboard")
        self.assertFalse(result.passed)
        self.assertIn("Expected text", result.message)

    @patch("qa_tools.web_api_smoke.safe_get", return_value=(200, {}, b"<html>not json</html>"))
    def test_fails_for_invalid_json(self, _mocked):
        result = smoke_check("https://example.com/api", expect_json=True)
        self.assertFalse(result.passed)
        self.assertFalse(result.json_valid)

    @patch("qa_tools.web_api_smoke.safe_get", return_value=(200, {}, b"x" * 20))
    def test_fails_when_body_exceeds_limit(self, _mocked):
        result = smoke_check("https://example.com/", max_bytes=10)
        self.assertFalse(result.passed)
        self.assertIn("safety limit", result.message)

    def test_rejects_invalid_timeout_before_network_call(self):
        with self.assertRaises(ValueError):
            smoke_check("https://example.com/", timeout=0)


if __name__ == "__main__":
    unittest.main()
