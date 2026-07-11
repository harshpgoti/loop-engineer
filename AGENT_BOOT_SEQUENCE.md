# Agent Boot Sequence (Fallback Only)

Normal use should be command-driven with **always-on lifecycle**:

```bash
loop session-start --command /loop-engine --tool "<tool>"
# read plan/SESSION_MANIFEST.md
/plan-loop | /product-develop | /loop-engine
loop session-end
```

Use this file only when a tool cannot read `AGENTS.md` or the command files automatically.

```text
You are continuing a user's product loop using this open-source Loop Engineering OS.

LOOP ENGINEERING RULES:
- Run loop session-start before work; loop session-end before stopping (any tool).
- Read plan/SESSION_MANIFEST.md first - not chat history alone.
- No unverified claims in DECISIONS.md or architecture - log sources in EVIDENCE_LOG.md.
- Builder agents do not approve their own work. Run review + security gates.
- No secrets or sensitive data in logs, tests, fixtures, screenshots, or prompts.
- Humans approve high-risk external actions unless the product plan explicitly allows otherwise.

INITIAL STATE:
- Product may be uninitialized.
- If `plan/main_plan.md` says UNINITIALIZED, `/plan-loop` must initialize it.
- Product-specific data belongs in `plan/main_plan.md`, `plan/`, `TASKS.yml`, `DECISIONS.md`, and `EVIDENCE_LOG.md`.

READ FIRST (in order):
1. plan/SESSION_MANIFEST.md (after session-start)
2. AGENTS.md
3. memories/MEMORY.md
4. DOUBTS.md
5. CURRENT_STATE.md
6. plan/main_plan.md
7. plan/ and plan/step_*.md
8. .loop/active-feature.json and plan/features/*/ (spec, tasks) when present
9. TASKS.yml
10. GATES.yml
11. DECISIONS.md
12. EVIDENCE_LOG.md
13. HANDOFF.md
14. plan/SESSION_RECALL.md
15. plan/AUTO_SKILLS.md (if present)
15a. plan/AUTO_AGENT_SKILLS.md (if present) - see skills/agent-builder/SKILL.md
16. .ai/SESSION_LOG.md

ROUTE BY COMMAND (each runs full cycle - see commands/*.md):
- `/plan-loop` -> session-start → plan → feature spec → task-compiler → session-end
- `/product-develop` -> session-start → auto-skills → build → converge → prod-gap → session-end
- `/loop-engine` -> session-start → route plan OR develop (or both) → session-end
- no command -> execute HANDOFF.md next action only

BEFORE STOPPING:
- loop session-end (mandatory)
- UPDATE: MEMORY.md, DOUBTS.md, CURRENT_STATE.md, TASKS.yml, active feature tasks.md, HANDOFF.md, .ai/SESSION_LOG.md
- DECISIONS.md (if decided), EVIDENCE_LOG.md (if verified)

Master loop: session-start → plan/feature-spec → task-compiler → build → review → QA → security → converge → prod-gap → deploy → session-end.
```

## Tool-specific notes

| Tool | Extra step |
|------|------------|
| **Any tool** | `loop session-start` / `loop session-end` - see `docs/SESSION_LIFECYCLE.md` |
| **Claude Code** | Also read `CLAUDE.md`; commands route to `commands/` + `skills/` directly |
| **Codex** | Read `CODEX.md`; use MCP only for product-approved integrations |
| **Cursor** | Read `CURSOR.md`; optional hooks in `docs/SESSION_LIFECYCLE.md` |
| **OpenCode** | Read `OPENCODE.md` |
| **Grok Build** | Read `GROK.md` |
| **Direct LLM API** | Use `API_USAGE.md` |
| **Sandboxed runtime** | Run long jobs in approved sandbox; restrict external egress until approved |
