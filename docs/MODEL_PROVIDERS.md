# Model providers

Loop Engineer stores model configuration under **LOOP_HOME's data folder** (`~/.loop-engineer/data/`), separate from `app/` and from any product workspace.

The **registry defines how to connect** (API URL, auth env var). It does **not** limit which models you can use.

## Quick start

```bash
loop model setup
loop model doctor
```

## Choosing a model (any provider model id)

```bash
loop model models anthropic              # live list from Anthropic API
loop model models openai --search gpt    # filter results
loop model anthropic:claude-opus-4-20250514   # any model id the provider accepts
loop model openrouter:anthropic/claude-opus-4
```

`default_model` in the registry is only a **fallback** when you omit the model:

```bash
loop model anthropic    # uses registry fallback if you skip the model suffix
```

Your real choice is stored in `~/.loop-engineer/data/model.yml`.

## Files

| File | Location | Contents |
|------|----------|----------|
| Registry | `providers/registry.yml` (repo) | Provider connection metadata only |
| Active config | `~/.loop-engineer/data/model.yml` | Your active `provider` + **any** `model` id |
| Secrets | `~/.loop-engineer/data/secrets.env` | API keys |

## Supported providers

- **Gateways** - OpenRouter
- **Cloud APIs** - Anthropic, OpenAI, Gemini, DeepSeek, Groq, xAI
- **Chinese providers** - Qwen (Alibaba DashScope compatible mode), Moonshot (Kimi), MiniMax, Zhipu/z.ai GLM
- **Emerging** - Together AI, Perplexity, Novita AI, NVIDIA NIM, Hugging Face Inference Providers
- **Self-hosted** (OpenAI-compatible) - Ollama, LM Studio, vLLM, SGLang, llama.cpp/llama-server, Jan
- **Custom** - any OpenAI-compatible base URL, including multiple **named** endpoints (see below)
- **IDE** - Cursor, Claude Code, Codex (no Loop Engineer API key)

Add connection entries by editing `providers/registry.yml`. Model catalogs come from the provider API, not the registry.

Auth today is API-key / env-var / no-auth only (matches every provider above). OAuth device/browser flows (e.g. Anthropic Claude Max login, Google Vertex service accounts, GitHub Copilot tokens) and AWS credential-chain auth are **not yet implemented** - planned as a future extension, not required for any provider currently in the registry.

## Named custom providers

For more than one custom endpoint (e.g. a local dev server and a work GPU box), register each by name instead of overwriting the single `custom.base_url`:

```bash
loop model custom add local http://localhost:8080/v1
loop model custom add work https://gpu-server.internal/v1 --key-env CORP_API_KEY
loop model custom list
```

Select with the triple syntax `custom:<name>:<model>`:

```bash
loop model custom:local:qwen-2.5
loop model custom:work:llama-3.3-70b
```

Named entries are stored in `~/.loop-engineer/data/model.yml` under `custom_providers:`; `--key-env` is optional (omit for keyless local servers).

## Fallback provider chain

Configure backup providers to try if the primary fails (rate limit, auth failure, outage). Automation scripts read the chain from `resolve_api_target()["fallback"]` and try each entry in order.

```bash
loop model fallback add openrouter:anthropic/claude-sonnet-4
loop model fallback add anthropic:claude-sonnet-4-20250514
loop model fallback list
loop model fallback clear
```

## Context length override

Loop Engineer does not auto-detect context length (no network round-trip beyond the model catalog). Set an explicit override when a provider under-reports or needs a floor:

```bash
loop model context set 64000
loop model context show
```

`resolve_api_target()["context_length"]` returns the override if set, else the registry's `context_min` for that provider, else empty.

## API modes

| Mode | Used for |
|------|----------|
| `openai_chat` | OpenAI-compatible `/v1/models` and chat |
| `anthropic_messages` | Anthropic `/v1/models` and Messages API |

Automation scripts should call `scripts/model_config.resolve_api_target()` for the resolved endpoint.

## Provider quirks

| Provider | Quirk |
|----------|-------|
| Ollama | Context length must be set server-side (`OLLAMA_CONTEXT_LENGTH` env var or Modelfile) - the OpenAI-compatible API cannot override it. Defaults to 4k-32k depending on VRAM if unset. |
| vLLM | Requires explicit flags for tool calling: `--enable-auto-tool-choice --tool-call-parser <parser-name>` - the parser name depends on the model family; check vLLM's docs for the right one for your model. |
| xAI | Auto-enables prompt caching via the `x-grok-conv-id` header for multi-turn requests - no config needed. |
| Custom / self-hosted | Prefer `openai_chat` mode; omit the API key entirely for keyless local servers (`auth: none` or `optional_key`). |
| WSL2 (Windows) | Direct `localhost` connections to a Windows-hosted local server can fail from inside WSL2. Use mirrored networking mode (`networkingMode=mirrored` in `.wslconfig`, Windows 11 22H2+) or the Windows host IP as `base_url`. |
| Qwen / DashScope | The registry `base_url` is the China (Beijing) endpoint. International/Singapore accounts need `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` instead - add it as a named custom provider if your key is international. |
| Perplexity, MiniMax | Marked `note:` **unconfirmed** in the registry - their current docs didn't clearly show a plain `/v1/chat/completions`-style path during the last verification pass. Confirm the exact path against the provider's docs before relying on `loop model models` for these two. |
| Ollama Cloud | Not in the registry - ollama.com's cloud docs only show native `/api/chat` / `/api/tags` routes, not a confirmed OpenAI-compatible `/v1` surface. |

## Security

- `secrets.env` is created with `chmod 600` where supported.
- Do not commit `secrets.env` or paste keys into plans or chat logs.
- Named custom providers (`loop model custom add`) store `base_url` and `env_key` name in `model.yml` (safe to share) - the actual key value still only lives in `secrets.env`.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `missing OPENROUTER_API_KEY` | `loop model set-key OPENROUTER_API_KEY` |
| `loop model models` fails | Check key, base URL, provider docs for model id |
| Local probe fails | Start Ollama/LM Studio/vLLM/etc.; confirm base URL |
| Named custom provider `Unknown custom provider` | `loop model custom add <name> <base_url>` first, then select `custom:<name>:<model>` |
| IDE agent | No key needed - use `/plan-loop` in Cursor etc. |

Run `loop doctor` for combined runtime + model health.
