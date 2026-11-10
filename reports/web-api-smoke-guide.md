# Web/API Smoke Checker

## Purpose

A small, read-only HTTP smoke-check utility for authorized website and API targets. It sends bounded GET requests and records status, response time, content type, and configured expectation results.

## Run

From the repository root:

\`\`\`bash
python -m qa_tools.web_api_smoke https://your-authorized-domain.example/health
\`\`\`

Require JSON:

\`\`\`bash
python -m qa_tools.web_api_smoke https://your-authorized-domain.example/api/health --expect-json
\`\`\`

Require a response phrase:

\`\`\`bash
python -m qa_tools.web_api_smoke https://your-authorized-domain.example/ --expect-text "Welcome"
\`\`\`

Choose a report destination:

\`\`\`bash
python -m qa_tools.web_api_smoke https://your-authorized-domain.example/health --report reports/client-smoke.json
\`\`\`

Windows users can replace \`python\` with \`py\`.

## Safety boundaries

- GET requests only; no form submission or state-changing methods.
- Use only targets you own or have explicit permission to test.
- No port scanning, brute force, fuzzing, load testing, or vulnerability exploitation.
- URLs containing embedded usernames or passwords are rejected.
- Each response is limited to 1 MB by default; configurable library limit is capped at 5 MB.
- Request timeout is bounded to 60 seconds.
- Response bodies are not written to the report.

## Report fields

The JSON report includes generation time, totals, URL, pass/fail, HTTP status, elapsed milliseconds, content type, a concise message, and JSON validity when requested.

## Limitations

This is a basic smoke checker, not a full API contract validator, browser automation suite, security audit, or uptime-monitoring service. Authentication, custom headers, cookies, POST requests, redirects policy, and TLS customization are intentionally outside this first version.
