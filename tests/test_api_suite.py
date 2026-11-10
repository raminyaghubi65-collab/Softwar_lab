import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from qa_tools.api_suite import run_endpoint, write_reports


class FakeResponse:
    status = 200

    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return self.body[:size]


class ApiSuiteTests(unittest.TestCase):
    @patch("qa_tools.api_suite.urlopen")
    def test_valid_contract_passes(self, mocked):
        mocked.return_value = FakeResponse(b'{"status":"ok","data":{"count":3}}')
        result = run_endpoint({
            "name": "health", "url": "https://example.test/health",
            "required_fields": ["status", "data.count"],
            "expected_values": {"status": "ok", "data.count": 3},
        })
        self.assertTrue(result.passed)
        self.assertEqual(result.failures, [])
        mocked.assert_called_once()

    @patch("qa_tools.api_suite.urlopen")
    def test_missing_field_fails(self, mocked):
        mocked.return_value = FakeResponse(b'{"status":"ok"}')
        result = run_endpoint({
            "url": "https://example.test/api",
            "required_fields": ["data.id"],
        })
        self.assertFalse(result.passed)
        self.assertIn("Missing required field: data.id", result.failures)

    @patch("qa_tools.api_suite.urlopen")
    def test_wrong_status_fails(self, mocked):
        response = FakeResponse(b'{"ok":true}')
        response.status = 204
        mocked.return_value = response
        result = run_endpoint({
            "url": "https://example.test/api", "expected_status": 200,
        })
        self.assertFalse(result.passed)
        self.assertIsNotNone(result.status_code)

    @patch("qa_tools.api_suite.urlopen")
    def test_invalid_json_fails(self, mocked):
        mocked.return_value = FakeResponse(b"<html>oops</html>")
        result = run_endpoint({"url": "https://example.test/api"})
        self.assertFalse(result.passed)
        self.assertIn("Response is not valid UTF-8 JSON", result.failures)

    def test_rejects_unsafe_url_before_network(self):
        with self.assertRaises(ValueError):
            run_endpoint({"url": "file:///etc/passwd"})

    @patch("qa_tools.api_suite.urlopen")
    def test_response_limit_is_enforced(self, mocked):
        mocked.return_value = FakeResponse(b"x" * 30)
        result = run_endpoint({"url": "https://example.test/api"}, max_bytes=10)
        self.assertFalse(result.passed)
        self.assertTrue(any("safety limit" in x for x in result.failures))

    def test_writes_json_and_html_reports_without_body(self):
        result = run_endpoint_result()
        with tempfile.TemporaryDirectory() as folder:
            json_path = Path(folder) / "report.json"
            html_path = Path(folder) / "report.html"
            write_reports([result], json_path, html_path)
            data = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(data["passed"], 1)
            self.assertNotIn("response_body", data["results"][0])
            self.assertIn("API QA Report", html_path.read_text(encoding="utf-8"))


def run_endpoint_result():
    from qa_tools.api_suite import ApiResult
    return ApiResult("demo", "https://example.test", True, 200, 12,
                     ["HTTP status is 200"], [])


if __name__ == "__main__":
    unittest.main()
