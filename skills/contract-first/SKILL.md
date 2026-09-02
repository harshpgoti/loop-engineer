---
name: contract-first
description: Design every cross-boundary contract as a single canonical artifact (OpenAPI / AsyncAPI / Protobuf / JSON Schema) per boundary, with consumer types generated from the artifact and provider behaviour verified against it at runtime. Use when designing or reviewing a service boundary, a public API, or an event schema.
---

# Contract First

Inherits `docs/SKILL_CONTRACT.md`.

A boundary is the line where two things meet: service-to-service, service-to-
client, producer-to-consumer, app-to-vendor. The contract is the
specification of that line. "Contract first" means the contract is the
first thing designed, the last thing changed, and the only source of truth
for both sides.

## When to use

- A new service boundary is being designed.
- An existing boundary is drifting (provider changed, consumer did not).
- A vendor API is being integrated and the boundary needs a typed contract.
- An event schema is shared by more than one consumer.

## When NOT to use

| Instead of this skill | Use |
|---|---|
| An internal function call | no contract needed |
| A boundary that already has a working contract | iterate the contract, not the boundary |
| A one-off data export | schema, but not the full rigour |

## The Five-Step Pipeline

### 1. Identify the owners

A boundary is between two things. Name both owners. An owner is a person or
a team, not a service. The provider owns the implementation; the consumer
owns the client. The contract belongs to neither alone; it is the joint
artefact.

### 2. Describe the consumer jobs

For each consumer, list the jobs the consumer needs the boundary to do.
A job is a user-visible outcome, not a method call. "Create a user" is a
job; "POST /users" is a method.

The smallest useful contract is the one that covers the consumer's jobs.
It is not the union of everything the provider could expose.

### 3. Define the contract artifact

Pick the artifact format that matches the boundary:

| Boundary | Artifact |
|---|---|
| HTTP / REST | OpenAPI 3.1 |
| Async messaging | AsyncAPI 2.6 |
| gRPC / RPC | Protobuf |
| Internal data | JSON Schema |
| Database schema | the schema itself (not an external artifact) |

The artifact is the source of truth. Generated types, generated
documentation, generated tests all derive from it. The artifact is the
only thing that may be edited by hand.

### 4. Generate consumer types

From the artifact, generate the consumer's type definitions. The consumer
does not invent its own types; the contract types are the consumer types.
A consumer that "improves" a contract type is a consumer that has drifted.

If the consumer is in a different language from the provider, the
generator must produce types in the consumer's language. The contract is
language-neutral; the types are not.

### 5. Verify both sides at runtime

Two verifications, both required:

- **Provider verification** - the provider's response is validated against
  the contract at every test run. A non-conforming response is a test
  failure, not a runtime warning.
- **Consumer verification** - the consumer's requests are validated
  against the contract before they leave the consumer. A non-conforming
  request is a bug in the consumer, not a bug in the provider.

Both verifications run in CI. The artifact is the test fixture; the
provider and the consumer are the units under test.

## The "Verify" Half

Most projects stop at step 4. They write the contract, generate types,
ship the consumer, and assume the provider will conform. The provider
will not. The provider will add a field, rename a status code, drop a
null. The consumer breaks at 03:00.

The verify half is the discipline that closes the loop. Without it, the
contract is documentation; with it, the contract is a test.

## When the Contract Changes

A contract change is a breaking change. The discipline:

1. Edit the artifact (the only editable thing).
2. Regenerate types on both sides.
3. Bump the version. A backward-incompatible change bumps the major
   version; the old version is kept running until consumers migrate.
4. Mirror the change as an ADR (see `architecture-decision-records`).
5. Notify the consumers. The notification is a TODO in their TASKS.yml
   or a doubt in their DOUBTS.md.

A change that does not go through all five steps is a change that drifts
the contract.

## Anti-Patterns

- **Provider-first design.** "The provider exposes X" is not a contract; it
  is an implementation detail. The contract is what the consumer needs;
  the provider implements what the contract asks for.
- **Hand-written types on the consumer.** Hand-written types drift from the
  contract within a sprint. Generate them.
- **Versioned only in the URL.** A `/v2/users` route is not a contract
  change; the artifact and the generated types are the contract. The
  URL is one possible way to express the version.
- **Skipping runtime verification.** "The provider is well-tested" is not
  verification. The provider's tests assert the provider's intent, not
  the contract. The contract test is the only test that fails when the
  contract breaks.
- **A "Pact" or "WireMock" mock that drifts.** The mock is part of the
  contract; if it drifts, the consumer's tests pass against a contract
  that no longer exists. Generate the mock from the artifact.

## Related Skills

- `api-design` - the conventions the HTTP contract follows.
- `error-handling` - the error envelope the contract exposes.
- `architecture-decision-records` - the place to record a contract change.
- `qa-validation` - the test discipline the contract test lives in.