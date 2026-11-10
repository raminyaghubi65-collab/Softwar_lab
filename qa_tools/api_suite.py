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
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from qa_tools.web_api_smoke import validate_url


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
    validate_url(url)
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
        request = Request(url, headers={"User-Agent": "Software-QA-Lab-API-Suite/1.0"})
        try:
            with urlopen(request, timeout=timeout) as response:
                status = response.status
                body = response.read(max_bytes + 1)
        except HTTPError as exc:
            status = exc.code
            body = exc.read(max_bytes + 1)

        elapsed = round((time.monotonic() - started) * 1000)
        if status == expected_status:
            checks.append(f"HTTP status is {expected_status}")
        else:
            failures.append(f"Expected HTTP {expected_status}, received {status}")

        if len(body) > max_bytes:
            failures.append(f"Response exceeded {max_bytes}-byte safety limit")
            return ApiResult(name, url, False, status, elapsed, checks, failures)

        payload: Any = None
        if spec.get("json", True):
            try:
                payload = json.loads(body.decode("utf-8"))
                checks.append("Response is valid JSON")
            except (UnicodeDecodeError, json.JSONDecodeError):
                failures.append("Response is not valid UTF-8 JSON")
                payload = None

        if payload is not None:
            for field in spec.get("required_fields", []):
                try:
                    _value_at_path(payload, str(field))
                    checks.append(f"Required field exists: {field}")
                except KeyError:
                    failures.append(f"Missing required field: {field}")

            for field, expected in spec.get("expected_values", {}).items():
                try:
                    actual = _value_at_path(payload, str(field))
                    if actual == expected:
                        checks.append(f"Expected value matches: {field}")
                    else:
                        failures.append(f"Unexpected value for field: {field}")
                except KeyError:
                    failures.append(f"Missing field for value assertion: {field}")

        max_elapsed = spec.get("max_elapsed_ms")
        if max_elapsed is not None:
            if not isinstance(max_elapsed, int) or max_elapsed < 0:
                raise ValueError(f"{name}: max_elapsed_ms must be a non-negative integer")
            if elapsed <= max_elapsed:
                checks.append(f"Response time is within {max_elapsed} ms")
            else:
                failures.append(f"Response time exceeded {max_elapsed} ms")

        return ApiResult(name, url, not failures, status, elapsed, checks, failures)
    except (URLError, TimeoutError, OSError) as exc:
        elapsed = round((time.monotonic() - started) * 1000)
        reason = getattr(exc, "reason", exc)
        return ApiResult(name, url, False, status, elapsed, checks,
                         [f"Request failed: {reason}"])


def write_reports(results: list[ApiResult], json_path: Path, html_path: Path) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "passed": sum(item.passed for item in results),
        "failed": sum(not item.passed for item in results),
        "results": [asdict(item) for item in results],
    }
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    rows = []
    for item in results:
        status = "PASS" if item.passed else "FAIL"
        details = "<br>".join(html.escape(x) for x in item.checks + item.failures)
        rows.append(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                html.escape(item.name), html.escape(item.url), status,
                item.status_code if item.status_code is not None else "—",
                details or "—",
            )
        )
    passed = payload["passed"]
    page = """<!doctype html><html lang="en"><meta charset="utf-8">
<title>API QA Report</title><style>
body{{font:15px system-ui;margin:2rem;color:#202124}}table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:.65rem;text-align:left;vertical-align:top}}
th{{background:#f3f4f6}}.summary{{margin:1rem 0}}
</style><h1>API QA Report</h1><p class="summary">Generated: {generated}
<br>Total: {total} | Passed: {passed} | Failed: {failed}</p>
<table><thead><tr><th>Endpoint</th><th>URL</th><th>Result</th>
<th>HTTP</th><th>Checks and findings</th></tr></thead><tbody>{rows}</tbody></table></html>""".format(
        generated=html.escape(payload["generated_at"]), total=payload["total"],
        passed=passed, failed=payload["failed"], rows="".join(rows),
    )
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(page, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run read-only GET API contract checks.")
    parser.add_argument("spec", type=Path, help="JSON file containing an endpoints array")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--json-report", type=Path, default=Path("reports/api-suite.json"))
    parser.add_argument("--html-report", type=Path, default=Path("reports/api-suite.html"))
    args = parser.parse_args(argv)
    try:
        config = json.loads(args.spec.read_text(encoding="utf-8"))
        endpoints = config["endpoints"]
        if not isinstance(endpoints, list) or not endpoints:
            raise ValueError("spec must contain a non-empty endpoints array")
        results = [run_endpoint(item, timeout=args.timeout) for item in endpoints]
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    for result in results:
        marker = "PASS" if result.passed else "FAIL"
        print(f"[{marker}] {result.name}: {len(result.failures)} failure(s)")
        for failure in result.failures:
            print(f"  - {failure}")
    write_reports(results, args.json_report, args.html_report)
    print(f"Reports written: {args.json_report} and {args.html_report}")
    return 0 if all(item.passed for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
