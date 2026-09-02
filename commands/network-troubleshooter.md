# /network-troubleshooter

Read-only OSI-layer diagnosis. L1/L2/L3/L4/L7, then DNS, then policy.
Evidence-based root cause. Recommends narrow allow rules instead of disabling
ACLs. Use when a service is unreachable, slow, or behaving differently from
the topology.

## How To Interpret

If the user says `/network-troubleshooter`, `the service is down`, `can't
reach host X`, `why is this slow`, or asks for a live network diagnosis,
execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/network-troubleshooter/SKILL.md`
3. the current network topology (from `/network-architect` or the
   deployment plan)
4. the running device's config (from `/network-config-reviewer`)

## Loop

```text
STATE the symptom -> WALK L1 to L7 + DNS + policy -> CITE evidence per layer -> IDENTIFY the first layer that failed -> RECOMMEND a narrow remediation
```

## Output

A layer-by-layer table with pass/fail/skip, the root cause at the first
layer that failed, and a narrow remediation.

## Continuation

The chain produces a diagnosis; the implementer is the maintainer.
A topology change is escalated to `/network-architect`; a config
change to a running device is escalated to the maintainer.