# Software QA Lab

A practical software-testing portfolio demonstrating Python unit testing, defect-oriented test design, reproducible bug reports, and continuous integration.

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

## Repository layout

```text
sample_app/
  task_manager.py
tests/
  test_task_manager.py
reports/
  test-report.md
.github/workflows/
  tests.yml
```

## QA approach

Each test is designed around an observable requirement. The suite avoids network access, credentials, paid services, and external dependencies. CI results are the source of truth for the latest automated run.

## Scope and honesty

This repository is a portfolio demonstration, not evidence that an unrelated customer application has been tested. No Android device testing, penetration testing, load testing, or production-system assessment is claimed. Those require a defined target, permission, and suitable test environment.

## Contact

Available for small, clearly scoped Python testing, manual QA, and reproducible bug-reporting tasks.

## Web and API smoke checks

A safe, read-only HTTP checker is available in `qa_tools/web_api_smoke.py`. It supports expected HTTP status, expected response text, JSON validation, bounded response sizes, and JSON result reports.

```bash
python -m qa_tools.web_api_smoke https://your-authorized-domain.example/health --expect-json
```

Run the full automated suite, including the smoke-checker's unit tests:

```bash
python -m unittest discover -s tests -v
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
