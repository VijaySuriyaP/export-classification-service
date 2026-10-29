# API data contract

`contracts/classify_request.schema.json` and `src/common/models.py` define the input contract. Extra fields are rejected.

| Field | Rule |
|---|---|
| `client_request_id` | Required UUID supplied by the caller. |
| `product_description` | Required, 10–2000 characters. |
| `materials` | One or more enum values; unknown/mixed goods can use `other` or `unknown`. |
| `intended_use` | Optional, maximum 1000 characters. |
| `weight_grams` | Optional, greater than zero and at most 1,000,000,000. |
| `unit_value` / `currency` | Unit value is positive; currency is required if unit value is supplied. Currency is INR, USD, or EUR. |
| `destination_country` | Two uppercase letters; deployment should validate this against its current ISO-3166 registry before production use. |
| `hs_hint` | Optional 2–10 digit string; two-digit chapter is range-checked. Hints are not treated as proof. |
| `callback_url` | Optional HTTPS URL whose host is in `CALLBACK_ALLOWLIST`; callback delivery itself is not implemented. |
| `client_id` | Required, 1–128 characters; used for rate limiting. |

Rejected requests are recorded to `quarantine` with field, code and message and do not create a run or enqueue a job. A valid POST returns HTTP 202 and `{ "run_id": "...", "status": "queued" }`. `GET /v1/runs/{run_id}` returns the run state/result. All terminal answers include the proposal-only disclaimer.
