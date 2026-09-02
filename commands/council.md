# /council

Convene a four-voice council for ambiguous decisions, tradeoffs, and go/no-go
calls. Adversarial; pairs with `/dev-team` (constructive). The skill is wired
into the chain; this command is for direct invocation.

## How To Interpret

If the user says `/council`, `council of four`, `adversarial review`, `four
voices`, or asks for a council decision, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/council/SKILL.md`
3. `plan/main_plan.md`
4. the active `plan/step_*.md` or feature `spec.md`
5. `DOUBTS.md`, `EVIDENCE_LOG.md`, `DECISIONS.md`, `GATES.yml`

## Anti-Anchoring Rule

Each of the four voices (Architect, Skeptic, Pragmatist, Critic) receives
**only** the question and the relevant context. The full conversation
history is intentionally withheld. A voice that already saw the conversation
cannot participate.

## Loop

```text
EXTRACT the real question -> GATHER compact context -> FORM the Architect position first -> LAUNCH three independent voices in parallel -> SYNTHESIZE with bias guardrails -> EMIT locked schema
```

## Output Schema (locked)

```markdown
## Council: <short decision title>

**Architect:** <1-2 sentence position>
**Skeptic:** <1-2 sentence position>
**Pragmatist:** <1-2 sentence position>
**Critic:** <1-2 sentence position>

### Verdict
- Consensus
- Strongest dissent
- Premise check
- Recommendation
```

## Continuation

`proceed` or `proceed with constraints` → chain continues.
`block and ask user` or `kill / rethink` → Stop Condition written into
`HANDOFF.md` with multiple-choice options.