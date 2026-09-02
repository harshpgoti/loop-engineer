---
name: error-handling
description: Cross-stack conventions for shaping internal exceptions into the API error envelope. Typed ApiError, validation-error mapping, no stack traces to users, observability hooks. Pairs with api-design and security-compliance.
---

# Error Handling

Inherits `docs/SKILL_CONTRACT.md`.

How a server turns an internal failure into the public response envelope defined in
`api-design`. The rules apply regardless of language or framework; the implementation
details are stack-specific (recorded in `codebase-design`).

## The Two Layers

Two distinct layers, each with its own purpose.

- **Internal exception layer.** Caught by the framework, mapped to a status code and
  error envelope, never exposed to the user verbatim. Stack traces live here, in the
  server logs.
- **External response layer.** The public error envelope defined in `api-design`:
  `{ "error": { "code", "message", "details", "request_id" } }`. No stack trace. No
  internal class name. No file path. No query string with credentials.

Crossing the boundary incorrectly is the dominant error-handling bug. A user-facing
message that contains an internal class name or a file path is information disclosure
(see `security-compliance`).

## Typed Errors

Every server has a small set of typed errors. The error code is stable; the message
may evolve.

```text
- NotFoundError        -> 404, code "not_found"
- ValidationError      -> 422, code "validation_failed", details = { field, value }
- ConflictError        -> 409, code "conflict", details = { field, current_value }
- UnauthorizedError    -> 401, code "unauthorized"
- ForbiddenError       -> 403, code "forbidden"
- RateLimitedError     -> 429, code "rate_limited", headers = { Retry-After }
- InternalError        -> 500, code "internal_error"   # last resort
```

Application code throws these; the framework maps them at the boundary. A new error
type is a contract change; record it in `DECISIONS.md` and update the API spec.

## Validation Errors

A validation failure is a `422 Unprocessable Entity` with a structured `details` payload
naming the failing field. The client can fix the request without guessing.

```json
{
  "error": {
    "code": "validation_failed",
    "message": "Email is not a valid address.",
    "details": { "field": "email", "value": "..." },
    "request_id": "..."
  }
}
```

For multiple field errors, repeat the structure per field:

```json
{
  "error": {
    "code": "validation_failed",
    "message": "Multiple fields failed validation.",
    "details": {
      "fields": [
        { "field": "email", "issue": "not a valid address" },
        { "field": "password", "issue": "must be at least 12 characters" }
      ]
    },
    "request_id": "..."
  }
}
```

Validation is the client's job to fix. The error must name what to fix; it must not
echo the user's exact value back unmodified if that value is sensitive.

## Catching and Re-Throwing

Three rules:

1. **Catch at the boundary, not deep in the call stack.** A try/catch in a leaf
   function swallows context. The boundary handler is the only place that knows how
   to shape the response.
2. **Re-throw typed errors unchanged.** A `NotFoundError` thrown by a service is the
   same `NotFoundError` the controller sees. Wrapping in a generic `Error` loses the
   typed contract.
3. **Wrap unknown errors as `InternalError`.** Anything that is not a typed error
   becomes a `500 Internal Server Error` with a `code: "internal_error"`. The original
   exception goes to the logs with the `request_id`; the user sees a generic message.

## Logging the Error

Every error response is logged server-side with:

- `request_id` (mandatory; the bridge to the user's support thread);
- the typed error class;
- the stack trace (or its stack-walking equivalent);
- any sensitive-data-redacted inputs that explain the failure;
- the user identity, if authenticated;
- the route, method, status code, and latency.

A log line without a `request_id` is not auditable. The `request_id` is the single
join key across the entire system for an incident.

## Sensitive Data in Errors

The error envelope is user-facing. Anything in it is exposed.

- Never include a stack trace, a file path, an internal class name, a query string
  with credentials, or a connection string.
- Echoing the user's input back is fine for the field name but never for the value of
  a sensitive field (password, token, credit card, PII the system already has). The
  detail is "this field is invalid," not "the value you sent was X."
- The `request_id` is not sensitive. It is the bridge to support; it must be in the
  body and the headers and the log.

## Observability Hooks

Every error increments a counter and writes a structured log:

- counter by `code` and `status_code` (e.g., `errors_total{code="validation_failed"}`);
- log line with the structured fields above;
- a sampled trace when the error is 5xx (so the SRE can debug without changing
  sampling for every error class).

The metrics are how the SRE detects that an error class is rising. The logs are how
they find the cause. The trace is how they confirm the fix.

## Anti-Patterns

- **Empty catch blocks.** Swallowed exceptions are silent failures. Either re-throw
  as a typed error or log and recover with a deliberate, documented decision.
- **`catch (Exception)` and a generic 500 without logging.** A 500 the user sees and
  the server forgets is the worst possible outcome: visible to the user, invisible to
  the team.
- **Returning `null` for a failed read.** A `null` is ambiguous: did the resource not
  exist, did the caller lack permission, or did the system fail? Throw a typed error.
- **Using 200 with an `{"error": ...}` body.** The status code is the contract; 200
  with an error payload is a lie. See `api-design`.
- **Including the user's password in the error.** A validation message that says
  "password 'hunter2' is too short" is a credential leak. Say "password is too short."
- **Throwing the framework's default error class.** A `RuntimeException` or
  `Exception` thrown from a service reaches the boundary unchanged and gets
  generic-mapped to 500. The typed error is the contract.
- **Logging the full request body on every error.** A request body may contain
  PII, secrets, or large payloads. Log the structured fields; redact what is not
  necessary.
- **Mapping 404 and 403 to the same response.** A user with the wrong ID and a user
  without permission are not the same; record the choice in `DECISIONS.md` if they
  are intentionally collapsed.
- **Stack traces in production.** The stack trace is the developer's debug tool; it
  is the attacker's roadmap. Stack traces live in the logs.

## Related Skills

- `api-design` - the response envelope this skill shapes.
- `security-compliance` - what must not be in the error body.
- `data-engineering` - the storage layer's error types and their typed mapping.
- `qa-validation` - golden cases for each error class.
- `codebase-design` - the seam where internal exceptions cross the boundary.