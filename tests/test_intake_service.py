import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

APP_PATH = Path(__file__).resolve().parents[1] / "intake_service" / "app.py"


class IntakeValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"DATA_DIR": self.temp.name, "ADMIN_TOKEN": "test-secret-token"}, clear=False)
        self.env.start()
        spec = importlib.util.spec_from_file_location("intake_app_under_test", APP_PATH)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_valid_pdf(self):
        self.assertEqual(self.module.validate_upload("report.pdf", b"%PDF-1.7 sample"), ".pdf")

    def test_rejects_executable_extension(self):
        with self.assertRaises(HTTPException) as caught:
            self.module.validate_upload("payload.exe", b"MZ...")
        self.assertEqual(caught.exception.status_code, 415)

    def test_rejects_fake_pdf(self):
        with self.assertRaises(HTTPException):
            self.module.validate_upload("report.pdf", b"not a pdf")

    def test_rejects_invalid_json(self):
        with self.assertRaises(HTTPException):
            self.module.validate_upload("data.json", b"{bad json")

    def test_rejects_binary_disguised_as_text(self):
        with self.assertRaises(HTTPException):
            self.module.validate_upload("notes.txt", b"hello\\x00world")

    def test_rejects_oversized_file(self):
        with patch.object(self.module, "MAX_FILE_BYTES", 3):
            with self.assertRaises(HTTPException) as caught:
                self.module.validate_upload("report.pdf", b"%PDF-too-large")
            self.assertEqual(caught.exception.status_code, 413)

    def test_filename_is_sanitized(self):
        self.assertEqual(self.module.clean_filename("../../my report?.pdf"), "my report_.pdf")

    def test_admin_token_required(self):
        with self.assertRaises(HTTPException) as caught:
            self.module.require_admin("Bearer wrong")
        self.assertEqual(caught.exception.status_code, 401)

    def test_upload_rate_limit(self):
        for _ in range(self.module.RATE_LIMIT):
            self.module.enforce_rate_limit("192.0.2.10")
        with self.assertRaises(HTTPException) as caught:
            self.module.enforce_rate_limit("192.0.2.10")
        self.assertEqual(caught.exception.status_code, 429)


if __name__ == "__main__":
    unittest.main()
