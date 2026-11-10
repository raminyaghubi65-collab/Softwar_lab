import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from qa_tools.api_suite import run_endpoint, write_reports


class ApiSuiteTests(unittest.TestCase):
    @patch("qa_tools.api_suite.safe_get", return_value=(200, {}, b'{"status":"ok","data":{"count":3}}'))
    def test_valid_contract_passes(self, mocked):
        result = run_endpoint({
            "name": "health", "url": "https://example.test/health",
            "required_fields": ["status", "data.count"],
            "expected_values": {"status": "ok", "data.count": 3},
        })
        self.assertTrue(result.passed)
        self.assertEqual(result.failures, [])
        mocked.assert_called_once()

    @patch("qa_tools.api_suite.safe_get", return_value=(200, {}, b'{"status":"ok"}'))
    def test_missing_field_fails(self, _mocked):
        result = run_endpoint({
            "url": "https://example.test/api",
            "required_fields": ["data.id"],
        })
        self.assertFalse(result.passed)
        self.assertIn("Missing required field: data.id", result.failures)

    @patch("qa_tools.api_suite.safe_get", return_value=(204, {}, b'{"ok":true}'))
    def test_wrong_status_fails(self, _mocked):
        result = run_endpoint({
            "url": "https://example.test/api", "expected_status": 200,
        })
        self.assertFalse(result.passed)
        self.assertEqual(result.status_code, 204)

    @patch("qa_tools.api_suite.safe_get", return_value=(200, {}, b"<html>oops</html>"))
    def test_invalid_json_fails(self, _mocked):
        result = run_endpoint({"url": "https://example.test/api"})
        self.assertFalse(result.passed)
        self.assertIn("Response is not valid UTF-8 JSON", result.failures)

    def test_rejects_unsafe_url_before_network(self):
        with self.assertRaises(ValueError):
            run_endpoint({"url": "file:///etc/passwd"})

    @patch("qa_tools.api_suite.safe_get", return_value=(200, {}, b"x" * 11))
    def test_response_limit_is_enforced(self, _mocked):
        result = run_endpoint({"url": "https://example.test/api"}, max_bytes=10)
        self.assertFalse(result.passed)
        self.assertTrue(any("safety limit" in x for x in result.failures))

    def test_writes_json_and_html_reports_without_body(self):
        from qa_tools.api_suite import ApiResult
        result = ApiResult("demo", "https://example.test", True, 200, 12,
                           ["HTTP status is 200"], [])
        with tempfile.TemporaryDirectory() as folder:
            json_path = Path(folder) / "report.json"
            html_path = Path(folder) / "report.html"
            write_reports([result], json_path, html_path)
            data = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(data["passed"], 1)
            self.assertNotIn("response_body", data["results"][0])
            self.assertIn("API QA Report", html_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
