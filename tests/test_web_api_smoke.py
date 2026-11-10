import io
import json
import unittest
from unittest.mock import patch

from qa_tools.web_api_smoke import smoke_check, validate_url


class FakeResponse:
    def __init__(self, body, status=200, content_type="application/json"):
        self._body = body
        self.status = status
        self.headers = {"Content-Type": content_type}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size=-1):
        return self._body[:size]


class UrlValidationTests(unittest.TestCase):
    def test_accepts_http_and_https(self):
        self.assertEqual(validate_url("https://example.com/health"), "https://example.com/health")
        self.assertEqual(validate_url("http://localhost:8000/"), "http://localhost:8000/")

    def test_rejects_relative_url(self):
        with self.assertRaises(ValueError):
            validate_url("/health")

    def test_rejects_non_http_scheme(self):
        with self.assertRaises(ValueError):
            validate_url("file:///etc/passwd")

    def test_rejects_embedded_credentials(self):
        with self.assertRaises(ValueError):
            validate_url("https://user:secret@example.com/")


class SmokeCheckTests(unittest.TestCase):
    @patch("qa_tools.web_api_smoke.urlopen")
    def test_passes_expected_json_response(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeResponse(b'{"ok": true}')
        result = smoke_check("https://example.com/api/health", expect_json=True)
        self.assertTrue(result.passed)
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json_valid)

    @patch("qa_tools.web_api_smoke.urlopen")
    def test_fails_when_expected_text_is_missing(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeResponse(b"Welcome")
        result = smoke_check("https://example.com/", expected_text="Dashboard")
        self.assertFalse(result.passed)
        self.assertIn("Expected text", result.message)

    @patch("qa_tools.web_api_smoke.urlopen")
    def test_fails_for_invalid_json(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeResponse(b"<html>not json</html>")
        result = smoke_check("https://example.com/api", expect_json=True)
        self.assertFalse(result.passed)
        self.assertFalse(result.json_valid)

    @patch("qa_tools.web_api_smoke.urlopen")
    def test_fails_when_body_exceeds_limit(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeResponse(b"x" * 20)
        result = smoke_check("https://example.com/", max_bytes=10)
        self.assertFalse(result.passed)
        self.assertIn("safety limit", result.message)

    def test_rejects_invalid_timeout_before_network_call(self):
        with self.assertRaises(ValueError):
            smoke_check("https://example.com/", timeout=0)


if __name__ == "__main__":
    unittest.main()
