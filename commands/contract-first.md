# /contract-first

Design every cross-boundary contract as a single canonical artifact
(OpenAPI / AsyncAPI / Protobuf / JSON Schema) per boundary, with consumer types
generated from the artifact and provider behaviour verified against it at runtime.

## How To Interpret

If the user says `/contract-first`, `design the contract`, `what's the boundary
shape`, or asks to define or audit a service boundary, execute this file
directly.

## Required Reads

1. `AGENTS.md`
2. `skills/contract-first/SKILL.md`
3. `skills/api-design/SKILL.md` (the conventions for HTTP)
4. existing boundary artifact (if any)
5. the provider and consumer modules

## Loop

```text
IDENTIFY OWNERS -> DESCRIBE CONSUMER JOBS -> PICK ARTIFACT FORMAT -> GENERATE CONSUMER TYPES -> VERIFY BOTH SIDES IN CI
```

## Output

- The contract artifact (e.g. `openapi.yaml`, `asyncapi.yaml`, `*.proto`,
  `*.schema.json`).
- The consumer's generated types (e.g. `src/types/api.ts`).
- The contract test in CI (provider + consumer verification).
- An ADR if the contract is at a stack or architecture level (see
  `architecture-decision-records`).

## Continuation

A contract change is a breaking change. Bump the version; regenerate types;
mirror the change as an ADR; notify consumers via `TASKS.yml` or `DOUBTS.md`.