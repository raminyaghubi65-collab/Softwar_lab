# Web/API Smoke Checker

## Purpose

A read-only HTTP smoke checker for website and API targets you own or are explicitly authorized to test. It sends bounded GET requests and records status, response time, content type, and configured expectation results.

## Run

From the repository root:

```bash
python -m qa_tools.web_api_smoke https://your-authorized-domain.example/health
```

Require JSON:

```bash
python -m qa_tools.web_api_smoke https://your-authorized-domain.example/api/health --expect-json
```

Require a response phrase:

```bash
python -m qa_tools.web_api_smoke https://your-authorized-domain.example/ --expect-text "Welcome"
```

Windows users can replace `python` with `py`.

## Network safety controls

- GET requests only; no form submission or state-changing methods.
- Only globally routable destination IP addresses are accepted. Loopback, private, link-local, multicast, reserved, and other non-global destinations are rejected.
- DNS results are checked and the connection is pinned to the selected validated IP address; TLS certificate verification still uses the original hostname.
- Redirects are not followed. A 3xx response is reported as received.
- Environment HTTP proxy settings are not used by this transport.
- URL credentials and URL fragments are rejected.
- Timeout is capped at 60 seconds; response size is capped at 5 MB.
- Response bodies are not written to reports.

## Report fields

The JSON report includes generation time, totals, URL, pass/fail, HTTP status, elapsed milliseconds, content type, a concise message, and JSON validity when requested.

## Limitations

This is a basic smoke checker, not a penetration tester, load tester, browser automation suite, or security audit. Authentication, custom headers, cookies, POST requests, and proxy support are intentionally not implemented. DNS resolution itself is handled by the operating system resolver and may block independently of the HTTP timeout. Test only systems within your written authorization.
