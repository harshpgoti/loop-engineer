---
name: model-providers
description: Configure AI model providers for Loop Engineer API-hosted inference. Use for /model, loop model setup, OpenRouter, Anthropic, OpenAI, Gemini, Ollama, or custom OpenAI-compatible endpoints.
---

# Model providers skill

Configure external LLM providers for Loop Engineer without vendoring third-party agent runtimes.

## When to use

- User runs Loop Engineer from a direct LLM API, automation script, or headless CLI
- User asks to connect OpenRouter, Anthropic, OpenAI, Gemini, local Ollama, or custom OpenAI-compatible endpoints
- `/doctor` reports missing model provider

## Layout

| Path | Purpose |
|------|---------|
| `providers/registry.yml` | Provider **connection** metadata (not a model allowlist) |
| `~/.loop-engineer/data/model.yml` | Active provider + **any** model id |
| `~/.loop-engineer/data/secrets.env` | API keys (never commit) |
| `plan/MODEL_STATUS.md` | Workspace status after `loop model use` |

## Workflow

1. Run `loop model list` to show provider connections.
2. Run `loop model models <provider>` to fetch the live catalog from the provider API.
3. Run `loop model setup` or `loop model <provider>:<model-id>` - **any** model id the provider accepts.
4. Store keys with `loop model set-key ENV_NAME`.
5. Run `loop model doctor` - key + connectivity checks.
6. Optional: `loop model custom add <name> <base_url>` for a second/third self-hosted endpoint, `loop model fallback add <provider:model>` for a backup chain, `loop model context set <n>` for a context-length override.

## Provider types

- **api_key** - requires env var in `secrets.env`
- **none** - local endpoint (Ollama, llama.cpp, Jan), no key
- **optional_key** - LM Studio, vLLM, SGLang, custom endpoints
- **ide** - Cursor, Claude Code, Codex; document only, no HTTP probe

Auth is API-key / env-var / no-auth only. OAuth device/browser flows and AWS credential-chain auth are not implemented yet - out of scope until explicitly requested.

## Rules

- Never store secrets in the product repo or `model.yml`.
- Extend `providers/registry.yml` for new **providers**, not model lists.
- Model ids are free-form; use `loop model models` to discover what the provider currently offers.
- Use `scripts/model_config.resolve_api_target()` for automation that needs base URL + model (also returns `fallback` chain and `context_length`).
- Prefer OpenAI-compatible mode for local/self-hosted servers (Ollama, vLLM, SGLang, llama.cpp, Jan, LM Studio).
- For more than one custom endpoint, use named entries (`loop model custom add <name> <base_url>`) and select with `custom:<name>:<model>` - never overload the single legacy `custom.base_url`.

## Commands map

| User | CLI |
|------|-----|
| `/model` | `loop model` or `loop model setup` |
| `/model list` | `loop model list` |
| `/model models` | `loop model models <provider>` |
| `/model doctor` | `loop model doctor` |
| `/model custom` | `loop model custom add <name> <base_url>` / `loop model custom list` |
| `/model fallback` | `loop model fallback add <provider:model>` / `list` / `clear` |
| `/model context` | `loop model context set <n>` / `loop model context show` |

## Integration

- `loop session-start` manifest lists active model.
- `loop doctor` includes model checks.
- `/plan-loop`, `/loop-engine`: if no provider and user needs API inference, suggest `loop model setup` once.
