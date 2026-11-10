# Sample QA Report

## Target

The in-repository sample application: `sample_app/task_manager.py`.

## Test method

Automated unit tests using Python's standard-library `unittest`. The test suite covers valid task creation, title trimming, invalid identifiers, invalid titles, duplicate identifiers, completion state, missing-task errors, and task-list ordering.

## Reproduction command

```bash
python -m unittest discover -s tests -v
```

Windows alternative:

```powershell
py -m unittest discover -s tests -v
```

## Results

This file describes the intended test scope, not a fabricated execution result. See the latest GitHub Actions run for the actual pass/fail result and runtime environment.

## Limitations

- In-memory behavior only; no database or persistence tests.
- No API, browser, Android-device, security-penetration, or performance testing.
- No claim is made about third-party or customer software.
