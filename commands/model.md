# /model

Configure the active AI model provider for Loop Engineer API-hosted inference.

## How To Interpret

If the user says `/model`, `loop model`, `model setup`, `model provider`, or `configure LLM`, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/model-providers/SKILL.md`
3. `docs/MODEL_PROVIDERS.md`
4. `providers/registry.yml`

## One-shot commands

```bash
loop model setup                    # wizard: pick provider, fetch models, set active
loop model models anthropic         # live model list from provider API
loop model anthropic:<model-id>     # any model id the provider accepts
loop model list
loop model doctor
loop model set-key OPENROUTER_API_KEY

# Multiple self-hosted / custom endpoints
loop model custom add local http://localhost:8080/v1
loop model custom:local:<model-id>
loop model custom list

# Fallback chain (tried in order by automation on failure)
loop model fallback add openrouter:anthropic/claude-sonnet-4
loop model fallback list

# Context length override
loop model context set 64000
```

Secrets live in `~/.loop-engineer/data/secrets.env` — never in the product repo.

## Loop

```text
LIST REGISTRY -> CHECK SECRETS -> SET ACTIVE -> DOCTOR -> SYNC plan/MODEL_STATUS.md
```

## Wiring

| When | Action |
|------|--------|
| `/session-start` | Manifest includes active model from `model.yml` |
| `/doctor` | Runs model key + connectivity checks |
| `/deployment-plan` | Patched when `loop model use` runs |
| Direct LLM / API usage | Read `resolve_api_target()` via `scripts/model_config.py` |

## IDE-hosted agents

Cursor, Claude Code, and Codex use the IDE's own inference — no API key in Loop Engineer. Register with `loop model use cursor` only when documenting routing; skip HTTP probe.

## Output

- `~/.loop-engineer/data/model.yml` — active provider + model
- `~/.loop-engineer/data/secrets.env` — API keys
- `plan/MODEL_STATUS.md` — workspace snapshot (when workspace resolved)

## Handoff

After setup, continue with `/plan-loop`, `/product-develop`, or `/loop-engine`. Model config persists across tools via LOOP_HOME.
