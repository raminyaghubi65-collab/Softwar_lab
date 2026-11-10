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
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


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
    """Accept only absolute HTTP(S) URLs without embedded credentials."""
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("URL must be an absolute http:// or https:// URL")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URLs containing embedded credentials are not allowed")
    if any(char.isspace() for char in url):
        raise ValueError("URL must not contain whitespace")
    return url


def smoke_check(
    url: str,
    *,
    expect_status: int = 200,
    expected_text: str | None = None,
    expect_json: bool = False,
    timeout: float = 10.0,
    max_bytes: int = 1_000_000,
) -> CheckResult:
    """Perform one bounded GET request and evaluate basic response expectations."""
    validate_url(url)
    if not 1 <= expect_status <= 599:
        raise ValueError("expect_status must be between 1 and 599")
    if not 0 < timeout <= 60:
        raise ValueError("timeout must be greater than 0 and at most 60 seconds")
    if not 1 <= max_bytes <= 5_000_000:
        raise ValueError("max_bytes must be between 1 and 5,000,000")

    request = Request(url, headers={"User-Agent": "Software-QA-Lab-SmokeCheck/1.0"})
    started = time.monotonic()
    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.status
            content_type = response.headers.get("Content-Type")
            body = response.read(max_bytes + 1)
        elapsed = round((time.monotonic() - started) * 1000)
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
    except HTTPError as exc:
        elapsed = round((time.monotonic() - started) * 1000)
        return CheckResult(url, exc.code == expect_status, exc.code, elapsed,
                           exc.headers.get("Content-Type"),
                           "HTTP error response" if exc.code == expect_status
                           else f"Expected HTTP {expect_status}, received {exc.code}")
    except (URLError, TimeoutError, OSError) as exc:
        elapsed = round((time.monotonic() - started) * 1000)
        reason = getattr(exc, "reason", exc)
        return CheckResult(url, False, None, elapsed, None,
                           f"Request failed: {reason}")


def write_report(results: list[CheckResult], output: Path) -> None:
    """Write a machine-readable report without storing response bodies."""
    payload: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "passed": sum(item.passed for item in results),
        "failed": sum(not item.passed for item in results),
        "results": [asdict(item) for item in results],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run safe, read-only HTTP smoke checks against authorized targets."
    )
    parser.add_argument("urls", nargs="+", help="Absolute http(s) URL(s) you are authorized to test")
    parser.add_argument("--expect-status", type=int, default=200)
    parser.add_argument("--expect-text", help="Text that must appear in each response")
    parser.add_argument("--expect-json", action="store_true", help="Require valid JSON responses")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--report", type=Path, default=Path("reports/smoke-results.json"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results: list[CheckResult] = []
    for url in args.urls:
        try:
            result = smoke_check(
                url,
                expect_status=args.expect_status,
                expected_text=args.expect_text,
                expect_json=args.expect_json,
                timeout=args.timeout,
            )
        except ValueError as exc:
            result = CheckResult(url, False, None, 0, None, str(exc))
        results.append(result)
        marker = "PASS" if result.passed else "FAIL"
        print(f"[{marker}] {result.url} — {result.message} ({result.elapsed_ms} ms)")

    write_report(results, args.report)
    print(f"Report written to: {args.report}")
    return 0 if all(item.passed for item in results) else 1


if __name__ == "__main__":
    sys.exit(main())
