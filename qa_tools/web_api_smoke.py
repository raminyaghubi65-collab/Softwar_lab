"""Safe, read-only HTTP smoke checks for websites and JSON APIs.

This tool sends GET requests only. It is not a vulnerability scanner or load tester.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import http.client

from qa_tools.safe_http import safe_get, validate_url as _validate_url


@dataclass
class CheckResult:
    url: str
    passed: bool
    status_code: int | None
    elapsed_ms: int
    content_type: str | None
    message: str
    json_valid: bool | None = None


def validate_url(url: str) -> str:
    """Validate URL syntax and reject non-public DNS destinations."""
    _validate_url(url)
    return url
    started = time.monotonic()
    try:
        status, headers, body = safe_get(
            url, timeout=timeout, max_bytes=max_bytes,
            user_agent="Software-QA-Lab-SmokeCheck/1.0",
        )
        elapsed = round((time.monotonic() - started) * 1000)
        content_type = headers.get("Content-Type")
        if len(body) > max_bytes:
            return CheckResult(url, False, status, elapsed, content_type,
                               f"Response exceeded the {max_bytes}-byte safety limit")

        text = body.decode("utf-8", errors="replace")
        failures: list[str] = []
        if status != expect_status:
            failures.append(f"Expected HTTP {expect_status}, received {status}")
        if expected_text is not None and expected_text not in text:
            failures.append("Expected text was not found in the response")

        json_valid: bool | None = None
        if expect_json:
            try:
                json.loads(text)
                json_valid = True
            except json.JSONDecodeError:
                json_valid = False
                failures.append("Response body is not valid JSON")

        return CheckResult(
            url=url,
            passed=not failures,
            status_code=status,
            elapsed_ms=elapsed,
            content_type=content_type,
            message="; ".join(failures) if failures else "All configured checks passed",
            json_valid=json_valid,
        )
    except (OSError, TimeoutError, http.client.HTTPException) as exc:
        elapsed = round((time.monotonic() - started) * 1000)
        return CheckResult(url, False, None, elapsed, None,
                           f"Request failed: {exc}")
