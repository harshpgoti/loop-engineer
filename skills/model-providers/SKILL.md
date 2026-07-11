---
name: model-providers
description: Configure AI model providers for Loop Engineer API-hosted inference. Use for /manage-model, loop manage-model setup, OpenRouter, Anthropic, OpenAI, Gemini, Ollama, or custom OpenAI-compatible endpoints.
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
| `plan/MODEL_STATUS.md` | Workspace status after `loop manage-model use` |

## Workflow

1. Run `loop manage-model list` to show provider connections.
2. Run `loop manage-model models <provider>` to fetch the live catalog from the provider API.
3. Run `loop manage-model setup` or `loop manage-model <provider>:<model-id>` - **any** model id the provider accepts.
4. Store keys with `loop manage-model set-key ENV_NAME`.
5. Run `loop manage-model doctor` - key + connectivity checks.
6. Optional: `loop manage-model custom add <name> <base_url>` for a second/third self-hosted endpoint, `loop manage-model fallback add <provider:model>` for a backup chain, `loop manage-model context set <n>` for a context-length override.

## Provider types

- **api_key** - requires env var in `secrets.env`
- **none** - local endpoint (Ollama, llama.cpp, Jan), no key
- **optional_key** - LM Studio, vLLM, SGLang, custom endpoints
- **ide** - Cursor, Claude Code, Codex; document only, no HTTP probe

Auth is API-key / env-var / no-auth only. OAuth device/browser flows and AWS credential-chain auth are not implemented yet - out of scope until explicitly requested.

## Rules

- Never store secrets in the product repo or `model.yml`.
- Extend `providers/registry.yml` for new **providers**, not model lists.
- Model ids are free-form; use `loop manage-model models` to discover what the provider currently offers.
- Use `scripts/model_config.resolve_api_target()` for automation that needs base URL + model (also returns `fallback` chain and `context_length`).
- Prefer OpenAI-compatible mode for local/self-hosted servers (Ollama, vLLM, SGLang, llama.cpp, Jan, LM Studio).
- For more than one custom endpoint, use named entries (`loop manage-model custom add <name> <base_url>`) and select with `custom:<name>:<model>` - never overload the single legacy `custom.base_url`.

## Commands map

| User | CLI |
|------|-----|
| `/manage-model` | `loop manage-model` or `loop manage-model setup` |
| `/manage-model list` | `loop manage-model list` |
| `/manage-model models` | `loop manage-model models <provider>` |
| `/manage-model doctor` | `loop manage-model doctor` |
| `/manage-model custom` | `loop manage-model custom add <name> <base_url>` / `loop manage-model custom list` |
| `/manage-model fallback` | `loop manage-model fallback add <provider:model>` / `list` / `clear` |
| `/manage-model context` | `loop manage-model context set <n>` / `loop manage-model context show` |

## Integration

- `loop session-start` manifest lists active model.
- `loop doctor` includes model checks.
- `/plan-loop`, `/loop-engine`: if no provider and user needs API inference, suggest `loop manage-model setup` once.
