# Software QA Lab

A practical software-testing portfolio demonstrating Python unit testing, defect-oriented test design, reproducible bug reports, and continuous integration.

## Live portfolio

https://raminyaghubi65-collab.github.io/Softwar_lab/

## What this repository demonstrates

- Requirement-based test cases with positive, negative, and boundary coverage
- Automated tests using Python's built-in `unittest` (no third-party dependencies)
- Reproducible test execution on Windows, macOS, and Linux
- GitHub Actions CI on pushes and pull requests
- Clear reporting that distinguishes executed checks from unverified manual/device checks

## Sample under test

`sample_app/task_manager.py` is a small in-memory task manager. The test suite checks task creation, validation, completion, duplicate IDs, and missing-task behavior.

## Run the tests

Python 3.10 or newer is recommended.

```bash
python -m unittest discover -s tests -v
```

On Windows, use `py -m unittest discover -s tests -v` if the `python` command is not available.

## QA approach and scope

Each test is designed around an observable requirement. The automated suite avoids network access, credentials, paid services, and external dependencies. CI results are the source of truth for the latest automated run.

This repository is a portfolio demonstration, not evidence that an unrelated customer application has been tested. No Android device testing, penetration testing, load testing, or production-system assessment is claimed. Those require a defined target, permission, and suitable test environment.

## Web and API smoke checks

A read-only HTTP checker is available in `qa_tools/web_api_smoke.py`. It supports expected HTTP status, expected response text, JSON validation, bounded response sizes, and JSON result reports.

```bash
python -m qa_tools.web_api_smoke https://your-authorized-domain.example/health --expect-json
```

See [the smoke-check guide](reports/web-api-smoke-guide.md) for usage and safety limits. Test only systems you own or are explicitly authorized to assess.

## Declarative API contract suite

For authorized API endpoints, `qa_tools/api_suite.py` runs read-only GET checks for HTTP status, JSON validity, required nested fields, expected values, and optional response-time thresholds. It produces JSON and HTML reports.

Create a JSON spec using the example in [the API suite guide](reports/api-suite-guide.md), then run:

```bash
python -m qa_tools.api_suite reports/api-spec.json
```

On Windows:

```powershell
py -m qa_tools.api_suite reports/api-spec.json
```

The API suite has unit tests in `tests/test_api_suite.py`; run the complete suite with `py -m unittest discover -s tests -v`. It is not a penetration tester, load tester, or full OpenAPI validator.

## Client-ready portfolio pack

- [QA services and introductory pricing](SERVICES.md)
- [Client intake and authorization checklist](CLIENT_INTAKE.md)
- [Outreach message templates](OUTREACH_TEMPLATES.md)
- [Illustrative client report](reports/sample-client-report.md) — fictional example, not a real customer result

Before every engagement, agree in writing on authorization, exact scope, test environment, price, deadline, and deliverables. Never request or accept wallet seed phrases, private keys, or production payment credentials. Do not share private project URLs, builds, logs, or customer data in public GitHub issues or comments.

## Static portfolio website

The responsive English-language portfolio page is in `docs/`. GitHub Pages publishes it from the `main` branch and `/docs` folder. For first contact, the site links to the GitHub profile; agree on a private channel before exchanging client materials.
