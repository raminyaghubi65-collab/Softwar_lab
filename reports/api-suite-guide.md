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

From the repository root:

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

## Safety and limitations

- GET only; no POST/PUT/PATCH/DELETE, login automation, or state changes.
- Only test systems for which you have permission.
- HTTP(S) URLs only; embedded URL credentials are rejected.
- Timeout is capped at 60 seconds and response size at 5 MB.
- Response bodies are never included in generated reports.
- This is contract/smoke testing, not penetration testing, load testing, or a complete OpenAPI schema validator.
- Authentication, custom headers, cookies, pagination, and redirect restrictions are not implemented. Do not put secrets in the specification.
