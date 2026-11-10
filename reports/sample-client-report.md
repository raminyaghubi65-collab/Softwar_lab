# Example Client QA Report

> **Demonstration only.** The target and findings below are fictional examples to demonstrate report structure. No external customer application was tested.

## Project summary

| Field | Example |
|---|---|
| Project | Demo Shop API |
| Environment | Staging |
| Build/version | demo-1.0 |
| Test date | Example date |
| Method | Read-only GET contract checks |
| Authorization | Example assumes written client permission |

## Scope

- Health endpoint: expected HTTP 200 and JSON response
- Product-list endpoint: expected JSON and required `items` field
- Product-detail endpoint: expected JSON and required `id` and `name` fields

## Example results

| Check | Expected | Example observation | Status |
|---|---|---|---|
| Health status | HTTP 200 | HTTP 200 | PASS |
| Health JSON | Valid JSON | Valid JSON | PASS |
| Product list field | `items` exists | Field missing | FAIL |
| Product detail ID | `id` exists | Field exists | PASS |

These are illustrative values, not actual test measurements.

## Example finding

**DEMO-API-001 — Product list omits required `items` field**

- Severity: Medium (example classification; confirm against product requirements)
- Preconditions: Staging API is available and client has authorized the check
- Steps:
  1. Send the agreed GET request to the product-list endpoint.
  2. Parse the response as JSON.
  3. Check for the required `items` field.
- Expected: JSON object contains an `items` field with the documented type.
- Actual: The example response does not contain `items`.
- Evidence: Attach a sanitized response excerpt supplied/approved for the report. Do not include tokens or personal data.
- Recommendation: Confirm the API contract and align the implementation or documentation.

## Limitations

This example does not represent a real customer test. A real report must state the exact tested build, date, environment, authorized scope, checks executed, and actual evidence. Untested areas must remain explicitly marked as not tested.
