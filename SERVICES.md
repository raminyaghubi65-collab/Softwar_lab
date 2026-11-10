# QA Testing Services

Small, clearly scoped software QA tasks for indie developers, solo founders, and small teams.

## Services and starting prices

Prices below are introductory estimates, not fixed quotes. Final scope and price are agreed before work starts.

| Service | Starting price | Typical deliverable |
|---|---:|---|
| Website smoke test | $15 | Checklist, screenshots, reproducible findings |
| Android app manual test | $25 | Device details, tested flows, screenshots, bug reports |
| Read-only API smoke test | $20 | Endpoint results and JSON/HTML report |
| Python bug reproduction | $20 | Minimal reproduction, observed behavior, suggested fix direction |
| Small combined QA pass | $40 | Agreed website/API/manual checks and consolidated report |

## What a basic test includes

1. Confirm the exact target, build/version, test environment, and permission.
2. Agree on a short list of user flows or endpoints.
3. Run only the agreed checks.
4. Record actual results, screenshots where useful, and steps to reproduce defects.
5. Deliver a concise report with tested scope, findings, limitations, and retest status.

## Bug report format

Each finding should include:
- ID and short title
- Severity (blocker/high/medium/low) with a brief reason
- Environment and app/build version
- Preconditions
- Numbered reproduction steps
- Expected result
- Actual result
- Evidence (screenshot or sanitized response excerpt)
- Reproducibility

## Client responsibilities

The client supplies a test build or public/staging URL, test account if required, acceptance expectations, and written authorization. Use test accounts and synthetic data wherever possible. Never send production passwords, private keys, seed phrases, or payment credentials.

## Boundaries

- No production data changes or financial transactions.
- API tooling in this repository performs read-only GET checks only.
- No penetration testing, exploit attempts, brute force, load testing, or security certification.
- No guarantee that testing will discover every defect.
- Manual Android checks depend on the device/OS and build supplied; they are not a substitute for a full device-farm test.

## Payment and delivery

Agree on scope, deadline, currency, payment method, and any platform fees in writing before starting. Never pay a client an upfront "unlock", "verification", or "withdrawal" fee. Never share wallet seed phrases or private keys.
