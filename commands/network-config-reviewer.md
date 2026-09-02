# /network-config-reviewer

Audit a running network device's configuration (Cisco IOS / IOS-XE / NX-OS /
vendor CLI) for SSH v1, plaintext credentials, SNMP public/private, missing
NTP/AAA, and similar. Read-only. Use when adopting a new device, after a
config change, or as a periodic security audit.

## How To Interpret

If the user says `/network-config-reviewer`, `audit the device config`, `check
the running-config`, `is SSH v1 disabled`, or asks for a network security
audit, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/network-config-reviewer/SKILL.md`
3. the running-config of the device (retrieved via SSH or
   supplied as a file)

## Loop

```text
RETRIEVE the running-config -> WALK the audit categories -> CITE the line for each finding -> EMIT a report with severity and remediation
```

## Output

A Markdown report with severity summary and a per-finding table with
line, category, severity, and remediation.

## Continuation

The chain produces a report; the implementer is the maintainer. The
audit is read-only. A config change is applied by the maintainer, then
re-audited.