---
name: api-design
description: REST/HTTP API design conventions: resource naming, method semantics, status codes, error envelopes, rate-limit headers, pagination, and versioning. Use when designing, reviewing, or migrating an API surface. Stack-agnostic; pairs with the product's data-engineering and security-compliance reviews.
---

# API Design

Inherits `docs/SKILL_CONTRACT.md`.

Cross-stack conventions for HTTP APIs. Adopt the surface once per product; deviations
need a recorded reason in `DECISIONS.md`. Stack-specific adapters (REST framework,
RPC runtime, GraphQL schema) live in `codebase-design` and the product's framework
choice, not here.

## Resources

- Plural kebab-case: `/users`, `/billing-invoices`, `/audit-events`. The plural form is
  the collection; the singular form is not a URL.
- Lowercase ASCII letters, digits, and hyphens. No underscores, no camelCase, no
  trailing slash. The path is a stable identifier; changing it is a breaking change.
- Resources are nouns. Verbs in the URL (`/getUser`, `/createOrder`) break caching,
  HATEOAS, and tooling. Express the action via HTTP method.

## Methods

| Method | Idempotent | Safe | Body | Use for |
|---|---|---|---|---|
| GET | yes | yes | no | read state |
| POST | no | no | yes | create a resource, trigger an action that has side effects |
| PUT | yes | no | yes | replace a resource in full |
| PATCH | no (in practice) | no | yes | partial update |
| DELETE | yes | no | no | remove a resource |

`PUT` is idempotent. `POST` is not. Do not use `POST` for everything because "the client
expects a body." Idempotency is a property of the operation, not the verb.

## Status Codes

Use the smallest set that conveys the truth.

| Range | Class | Use for |
|---|---|---|
| 2xx | success | the operation worked |
| 3xx | redirect | the resource moved; client may follow |
| 4xx | client error | the client did something wrong; do not retry without change |
| 5xx | server error | the server failed; the client may retry |

Common specific codes this skill uses:

- `200 OK` with body: success with a payload.
- `201 Created` with `Location` header: resource created. The Location URL is the
  canonical pointer; clients follow it.
- `204 No Content` with no body: success without a payload (delete, idempotent update).
- `400 Bad Request`: the request was malformed in a way the server cannot parse.
- `401 Unauthorized`: no credentials or invalid credentials.
- `403 Forbidden`: credentials are valid but the caller is not allowed. Distinct from 401.
- `404 Not Found`: the resource does not exist (or the caller is not allowed to know
  whether it exists; choose deliberately).
- `409 Conflict`: the request conflicts with current state (duplicate key, version
  mismatch). The client may reconcile and retry.
- `410 Gone`: the resource existed and is now permanently gone. The client should not
  retry; remove cached copies.
- `422 Unprocessable Entity`: the request parsed but failed validation. Distinct from
  400; cite the field that failed in the body.
- `429 Too Many Requests`: rate-limited. Pair with `Retry-After`.
- `500 Internal Server Error`: the server failed unexpectedly. Never leak a stack trace.
- `503 Service Unavailable`: temporary overload or maintenance. Pair with `Retry-After`.

## Response Envelope

Two envelopes. Pick one per product; mixing is a contract violation.

```jsonc
// success
{ "data": <T>, "meta": { "request_id": "...", "...": "..." } }

// error
{ "error": {
    "code": "user_already_exists",
    "message": "Human-readable description of what went wrong.",
    "details": { "field": "email", "value": "..." },
    "request_id": "..."
}}
```

`code` is a stable machine-readable identifier; the client can switch on it. `message` is
human-readable, not localised. `details` is optional structured context. `request_id`
is mandatory; it appears in the server logs and is the bridge for any support thread.

Never leak: stack traces, file paths, internal class names, query strings with
credentials, secrets. The error envelope is user-facing.

## Pagination

Cursor-based by default for collections that grow unboundedly. Offset-based only when
the client genuinely needs page-N semantics (admin UIs, exports).

```http
GET /users?cursor=eyJpZCI6IjEyMyJ9&limit=50
```

Response shape:

```json
{
  "data": [ ... ],
  "page": {
    "next_cursor": "eyJpZCI6IjE3MyJ9",
    "has_more": true
  }
}
```

`has_more=false` means "stop calling." A missing `next_cursor` means "this is the last
page." The cursor is opaque to the client; the server decides its encoding.

## Rate Limiting

Three headers, all required when limiting is enabled:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1700000000   # unix epoch seconds
```

On `429`, also include:

```http
Retry-After: 30                # seconds, or an HTTP-date
```

The client must back off to at least `Retry-After`. The server must be honest about
the limit, not a guessed number.

## Versioning

URL-path versioning is the default for HTTP APIs: `/v1/users`, `/v2/users`. The
version is part of the canonical URL; clients and proxies can route on it.

Header versioning (`Accept: application/vnd.myapi.v2+json`) is acceptable for
internal APIs that already negotiate content type, but is harder to debug.

No versioning is acceptable only when the API has not yet shipped to anyone outside
the team. As soon as an external client exists, lock the version.

## Anti-Patterns

- **Verbs in the URL.** `/getUser`, `/createInvoice`, `/deleteUser/123` - actions
  belong in the method, not the path.
- **Returning 200 with an error payload.** `200 OK` is success; a payload that says
  `{"error": ...}` is a contract violation. Use 4xx and 5xx.
- **Stack traces in production responses.** A 500 body with a Python traceback is
  information disclosure. The body is the error envelope; the trace is in the logs.
- **Mixing pagination strategies.** Cursor on some endpoints, offset on others, with
  no product reason. Pick one; record the choice in `DECISIONS.md`.
- **Versioned via query string.** `?v=1` is invisible to caching and proxies. Use the
  path.
- **Returning all data when the client asked for a slice.** A 10,000-row response to
  `GET /users` is a denial-of-service waiting to happen. Always paginate.
- **Hiding errors as 200.** A `{"success": false, "error": "..."}` body inside a 200
  response is a contract lie. The status code is the contract.
- **Hardcoding rate limits in the client.** The server decides the limit; the
  client respects `Retry-After`. Hardcoded values drift.
- **Documenting endpoints in the spec that do not exist in the code.** Spec drift
  is the most common cause of client outages. The contract test enforces the
  spec; the spec is the truth.

## Validation

- OpenAPI or equivalent schema at every endpoint.
- Contract tests that run in CI and pin request/response shapes.
- Lint pass for status code usage, error envelope shape, and pagination consistency
  across the surface.

## Related Skills

- `data-engineering` - the storage layer behind the API.
- `security-compliance` - auth, rate limiting, and PII on the wire.
- `error-handling` - how the server shapes internal exceptions into the response
  envelope.
- `codebase-design` - module, interface, and seam vocabulary the API exposes.