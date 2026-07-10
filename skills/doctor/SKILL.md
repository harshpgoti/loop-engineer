---
name: doctor
description: Health-checks the Loop Engineering OS runtime and active product workspace, writing DOCTOR.md with errors and warnings. Use when the user types /doctor or asks if setup is healthy.
---

# Doctor

## Purpose

Detect broken setup, missing files, validator failures, and product/tool separation issues before long loops fail mid-run.

## Read First

- `commands/doctor.md`
- workspace registry config
- product-state files in the active workspace

## Write

- `DOCTOR.md`
- optional note in `.ai/SESSION_LOG.md`

## Checks

- required tool files exist
- workspace registered or detectable
- product-state files exist
- tool repo is not storing initialized product data
- scripts import correctly
- template validation passes
- product output validation passes when possible
- memory size vs limits and drift
- FTS5 health on `state.db`
- pending staged writes
- user skill frontmatter

## Optional Script

Use `scripts/doctor.py` first, then explain results to the user.

## Closeout

If unhealthy, recommend `/setup-loop-engine`, `/sync-loop-state`, or `/upgrade-loop-engineer` as appropriate.
