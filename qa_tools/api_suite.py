"""Declarative, read-only API contract checks for explicitly authorized endpoints.

Only GET requests are sent. Response bodies are inspected in memory and are never
included in generated reports.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import http.client

from qa_tools.safe_http import safe_get


@dataclass
class ApiResult:
    name: str
    url: str
    passed: bool
    status_code: int | None
    elapsed_ms: int
    checks: list[str]
    failures: list[str]


def _value_at_path(payload: Any, path: str) -> Any:
    value = payload
    for part in path.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            raise KeyError(path)
    return value


def run_endpoint(spec: dict[str, Any], *, timeout: float = 10.0,
                 max_bytes: int = 1_000_000) -> ApiResult:
    name = str(spec.get("name") or spec.get("url") or "unnamed endpoint")
    url = str(spec.get("url", ""))
    if not 0 < timeout <= 60:
        raise ValueError("timeout must be greater than 0 and at most 60 seconds")
    if not 1 <= max_bytes <= 5_000_000:
        raise ValueError("max_bytes must be between 1 and 5,000,000")

    expected_status = spec.get("expected_status", 200)
    if not isinstance(expected_status, int) or not 100 <= expected_status <= 599:
        raise ValueError(f"{name}: expected_status must be an HTTP status integer")

    started = time.monotonic()
    status: int | None = None
    body = b""
    failures: list[str] = []
    checks: list[str] = []
    try:
        status, _headers, body = safe_get(
            url, timeout=timeout, max_bytes=max_bytes,
            user_agent="Software-QA-Lab-API-Suite/1.0",
        )
