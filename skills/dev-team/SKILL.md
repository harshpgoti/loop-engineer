---
name: dev-team
description: Run a preset four-persona parallel review (PM / Architect / Developer / QA) as independent analysis-only voices. Use when designing a feature, reviewing a proposal, or onboarding an initiative that benefits from constructive role-based feedback rather than adversarial council. Complements council.
---

# Dev Team

Inherits `docs/SKILL_CONTRACT.md`.

A preset four-persona review that runs as **analysis-only** parallel subagents. Each
persona is given only the question and the relevant context - never the full conversation
history. That is the anti-anchoring rule, and it is the same one `council` uses.

Unlike `council` (which is adversarial: Architect / Skeptic / Pragmatist / Critic push
against each other), `dev-team` is **collaborative**: PM / Architect / Developer / QA
each answer on their declared domain and surface tensions constructively. The
synthesis names agreements and tensions explicitly; it does not paper over disagreement.

## When to use

- a new feature is being designed and the build will benefit from four lenses at once;
- an existing initiative needs an early sanity check before significant work begins;
- the user asks for "PM + Arch + Dev + QA look at this" or a similar role-based review;
- council has run once and the next decision benefits from a constructive reframe
  rather than another adversarial round.

## When NOT to use

| Instead of dev-team | Use |
|---|---|
| Verifying whether output is correct | `santa-method` |
| Making a single decision with explicit dissent | `council` |
| Breaking a feature into implementation steps | `planner`, `implementation-planner` |
| Reviewing code for bugs or security | `code-reviewer`, `security-compliance` |
| Designing system architecture | `architect` |

## Roles

| Voice | Lens | Tools allowed |
|---|---|---|
| Product Manager | ICP, workflow, scope, PRD, acceptance criteria | Read, Grep, Glob |
| Architect | architecture, data model, integrations, scalability, build/buy | Read, Grep, Glob |
| Developer | implementation seams, tests, error handling, complexity | Read, Grep, Glob |
| QA | test plan, regressions, golden cases, release confidence | Read, Grep, Glob |

All four personas are **analysis-only**. None may write or edit. If the synthesis says
"this needs a code change," that becomes a task in `TASKS.yml`, not a write from this
skill.

## Anti-Anchoring Rule

Each persona receives **only**:
- the decision question;
- the compact context (files, snippets, prior decisions) the reviewer needs;
- a strict role prompt.

A persona that already saw the full conversation history cannot participate - re-issue
the question.

## Workflow

### 1. Extract the question

Reduce the decision to one explicit prompt. If it is vague, ask one clarifying question
before convening the team.

### 2. Gather context

If the decision is codebase-specific: collect the relevant files, snippets, issue text,
metrics. Keep it compact. If the decision is strategic/general, skip repo snippets
unless they materially change the answer.

### 3. Launch four parallel voices

Each subagent gets:

```text
You are the [ROLE] on a four-persona review team.

Question:
[decision question]

Context:
[only the relevant snippets or constraints]

Respond with:
1. Position - 1-2 sentences
2. Reasoning - 3 concise bullets
3. Risk - biggest risk in your recommendation
4. Surprise - one thing the other voices may miss

Be direct. No hedging. Keep it under 300 words.
```

Run them in parallel as one message. Wait for all four.

### 4. Synthesize

The synthesis must explicitly:
- name agreements across personas;
- name tensions (where personas disagree) without picking a winner to please everyone;
- recommend the next concrete step (a task, an ADR, a doubt, or "proceed");
- note the persona whose voice was loudest against the synthesis and the reason.

A dev-team review that ends with "they mostly agreed" is broken. The four personas
should disagree on something; the synthesis captures the disagreement and resolves it.

## Output Schema (locked)

```markdown
## Dev Team: <short decision title>

**PM:** <1-2 sentence position>
**Architect:** <1-2 sentence position>
**Developer:** <1-2 sentence position>
**QA:** <1-2 sentence position>

### Agreements
- <where all four aligned>

### Tensions
- <PM vs Architect on X>: <reason>
- <Developer vs QA on Y>: <reason>

### Recommendation
<the synthesised path; one concrete next step>

### Confidence
- per-persona: low | medium | high
- overall: low | medium | high
```

## Anti-Patterns

- using dev-team for code review (use `code-reviewer` or `santa-method`);
- using dev-team for one-shot implementation work (use `builder`);
- feeding the personas the entire conversation transcript;
- hiding disagreement in the final verdict;
- treating dev-team output as gospel - personas are missing context the user has.

## Related Skills

- `council` - adversarial decision review (Architect / Skeptic / Pragmatist / Critic);
- `planner` - feature implementation planning;
- `architect` - system design;
- `code-reviewer` - two-axis review (Spec vs Standards);
- `santa-method` - dual-reviewer adversarial verification;
- `architecture-decision-records` - formalize the outcome when the decision becomes
  long-lived system policy.