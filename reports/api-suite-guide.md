# Declarative API QA Suite

This tool runs bounded, read-only **GET** checks against endpoints you own or are explicitly authorized to test. It validates HTTP status, JSON syntax, required nested fields, expected field values, and optional response-time thresholds. It creates JSON and HTML reports.

## 1. Create a test specification

Save this as `reports/api-spec.json`:

```json
{
  "endpoints": [
    {
      "name": "Public health endpoint",
      "url": "https://your-authorized-domain.example/api/health",
      "expected_status": 200,
      "json": true,
      "required_fields": ["status", "service.version"],
      "expected_values": {"status": "ok"},
      "max_elapsed_ms": 1500
    }
  ]
}
```

Nested field paths use dot notation. Remove `max_elapsed_ms` if no response-time objective has been agreed.

## 2. Run

```bash
python -m qa_tools.api_suite reports/api-spec.json
```

Windows:

```powershell
py -m qa_tools.api_suite reports/api-spec.json
```

Optional outputs:

```bash
python -m qa_tools.api_suite reports/api-spec.json --json-report reports/client-api.json --html-report reports/client-api.html
```

Exit codes: `0` all checks passed, `1` at least one endpoint failed, `2` invalid configuration or unreadable spec.

## Network safety and limitations

- GET only; no POST/PUT/PATCH/DELETE, login automation, or state changes.
- Only globally routable destination IP addresses are accepted; private, loopback, link-local, multicast, and reserved destinations are rejected.
- DNS is checked and the socket connects to a validated IP, avoiding a second DNS lookup for the connection. HTTPS still verifies the original hostname.
- Redirects are not followed, preventing a public endpoint from redirecting the checker to an internal address.
- Environment HTTP proxy settings are not used.
- URL credentials and fragments are rejected.
- Timeout is capped at 60 seconds and response size at 5 MB.
- Response bodies are never included in generated reports.
- Authentication, custom headers, cookies, pagination, proxy support, and redirects are not implemented.
- DNS resolution is performed by the operating system and may block independently of the HTTP timeout.

This is contract/smoke testing, not penetration testing, load testing, or a complete OpenAPI schema validator. Never put secrets in the specification.
