# Tool Registry

Loop Engineer is **self-contained**: it does not bundle or depend on any
third-party tool. Every skill, command, and script in this repo stands
alone; the chain works without network access to any external service.

The default policy for adopting an external tool remains:

1. The tool's *name* and *URL* are recorded **only in the file that
   uses the tool** (skill body, command, script). They are **not**
   displayed in the chain's discoverable surfaces (`/skill-list`,
   `/roles`, `/chain-catalog`).
2. The chain does not auto-install or auto-update the tool. The user
   installs the tool themselves and points the chain at it.
3. Other files in this repo do not name or link to the tool; the
   reference lives only in the file that uses it.

## Sanctioned exception: the external frontend chain

The frontend router (`scripts/frontend_skill_router.py`) selects
optional third-party frontend layers when a task carries design or 3D
signals. These packs are credited in exactly one place:
[`skills/frontend-animation/references/external-skill-chain.md`](../skills/frontend-animation/references/external-skill-chain.md).

That file is the single canonical catalog for the exception:

- It names the packs, their authors, repositories, and licenses (all MIT).
- It documents the precedence rule (core Loop rules override external
  pack instructions).
- It documents the no-auto-install rule (the chain detects and selects;
  the user installs).
- It documents the safety checks (no code execution from a pack,
  prompt-injection vigilance, bundled-asset license verification).

No other file in this repo collects third-party names or URLs. If a
future capability needs an external tool, add it to that catalog file
with the same credit, license, and safety structure - or record it in
the single file that uses it, per the default policy above.
