"""CLI for Loop Engineer model provider setup and selection."""

from __future__ import annotations

import argparse
import getpass
import sys
from datetime import datetime, timezone
from pathlib import Path

from model_catalog import fetch_provider_models, filter_models
from model_config import (
    active_summary,
    add_custom_provider,
    add_fallback,
    clear_fallback,
    get_custom_provider,
    load_config,
    parse_selection,
    save_config,
    set_active,
    set_context_length,
)
from model_doctor import check_provider_key, doctor_active, doctor_all_keys
from model_paths import load_secrets_env, secrets_env_path, workspace_model_status
from model_registry import get_provider, list_provider_ids, load_registry
from workspace_utils import resolve_workspace

PREVIEW_LIMIT = 30


def _write_secret(key: str, value: str) -> None:
    path = secrets_env_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_secrets_env()
    existing[key] = value
    lines = [
        "# Loop Engineer provider secrets - never commit this file",
        f"# Updated {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
    ]
    for k, v in sorted(existing.items()):
        lines.append(f"{k}={v}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _sync_workspace_status(workspace: Path, provider_id: str, model: str) -> None:
    meta = get_provider(provider_id)
    if not meta:
        return
    path = workspace_model_status(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    label = meta.get("label", provider_id)
    body = f"""# Model status

| Field | Value |
|-------|-------|
| Provider | {label} (`{provider_id}`) |
| Model | `{model}` |
| Config | `~/.loop-engineer/data/model.yml` |
| Secrets | `~/.loop-engineer/data/secrets.env` |
| Updated | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} |

Use `loop model doctor` to verify connectivity.
"""
    path.write_text(body, encoding="utf-8")


def _sync_deployment_plan(workspace: Path, provider_id: str, model: str) -> None:
    dep = workspace / "DEPLOYMENT_PLAN.md"
    if not dep.exists():
        return
    text = dep.read_text(encoding="utf-8", errors="ignore")
    meta = get_provider(provider_id)
    label = meta.get("label", provider_id) if meta else provider_id
    for field, val in [
        ("LLM_PROVIDER", label),
        ("LLM_MODEL", model),
        ("LLM_API_MODE", meta.get("api_mode", "") if meta else ""),
    ]:
        if not val:
            continue
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.strip().startswith(f"| {field} |"):
                parts = line.split("|")
                if len(parts) >= 4:
                    parts[2] = f" {val} "
                    lines[i] = "|".join(parts)
        text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    dep.write_text(text, encoding="utf-8")


def _print_model_preview(provider_id: str, *, search: str = "", limit: int = PREVIEW_LIMIT) -> None:
    ok, models, msg = fetch_provider_models(provider_id)
    if not ok:
        print(f"  (could not fetch models: {msg})")
        print("  Enter any model id from the provider docs.")
        return
    filtered = filter_models(models, search)
    print(f"\nAvailable models from {provider_id} ({msg}):")
    show = filtered[:limit]
    for mid in show:
        print(f"  {mid}")
    if len(filtered) > limit:
        print(f"  ... {len(filtered) - limit} more - use: loop model models {provider_id} --search <term>")
    print("\nUse any id above, or any model id the provider publishes.")


def cmd_status(_: argparse.Namespace) -> int:
    cfg = load_config()
    active = cfg.get("active") or {}
    print("Active model:", active_summary())
    print("Config:", secrets_env_path().parent / "model.yml")
    print("Secrets:", secrets_env_path())
    if active.get("provider"):
        for name, ok, msg in doctor_active():
            flag = "OK" if ok else "FAIL"
            print(f"  [{flag}] {name}: {msg}")
    else:
        print("No provider selected. Run: loop model setup")
    fallback = cfg.get("fallback") or []
    if fallback:
        print("Fallback chain:")
        for i, fb in enumerate(fallback, 1):
            print(f"  {i}. {fb.get('provider')}:{fb.get('model')}")
    context_length = cfg.get("context_length", "")
    if context_length:
        print(f"Context length override: {context_length}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    reg = load_registry()
    provider = getattr(args, "provider", None)
    if provider:
        meta = get_provider(provider)
        if not meta:
            print(f"Unknown provider: {provider}", file=sys.stderr)
            return 1
        print(f"{meta.get('label', provider)} ({meta['id']})")
        print(f"  fallback default: {meta.get('default_model', '') or '(none)'}")
        print(f"  auth: {meta.get('auth', '')}")
        if meta.get("base_url"):
            print(f"  base_url: {meta.get('base_url')}")
        if meta.get("docs"):
            print(f"  docs: {meta.get('docs')}")
        pid = meta["id"]
        print(f"\n  loop model models {pid}   # live list from provider API")
        print(f"  loop model {pid}:<any-model-id>")
        return 0
    print("API providers (registry = connection only; any provider model id works):")
    for pid in list_provider_ids():
        meta = reg.get(pid, {})
        print(
            f"  {pid:14} {meta.get('label', pid):32} "
            f"fallback={meta.get('default_model', '') or '(none)'}"
        )
    print("\nLive model catalog:     loop model models <provider>")
    print("Set any model:          loop model anthropic:<model-id>")
    print("\nIDE providers (no API key):")
    for pid, meta in reg.items():
        if isinstance(meta, dict) and meta.get("auth") == "ide":
            print(f"  {pid:14} {meta.get('label', pid)}")
    return 0


def cmd_models(args: argparse.Namespace) -> int:
    provider_id = args.provider
    if not provider_id:
        cfg = load_config()
        provider_id = (cfg.get("active") or {}).get("provider", "")
    if not provider_id:
        print("Usage: loop model models <provider>  (or set active provider first)", file=sys.stderr)
        return 1
    ok, models, msg = fetch_provider_models(provider_id)
    if not ok:
        print(msg, file=sys.stderr)
        return 1
    filtered = filter_models(models, getattr(args, "search", "") or "")
    print(f"{provider_id}: {msg}")
    if getattr(args, "search", None):
        print(f"filter: {args.search!r} ({len(filtered)} matches)")
    for mid in filtered:
        print(mid)
    return 0


def cmd_use(args: argparse.Namespace) -> int:
    provider_id, model, custom_name = parse_selection(args.selection)
    try:
        cfg = set_active(provider_id, model, custom_name=custom_name)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    active = cfg["active"]
    label = f"custom:{custom_name}" if custom_name else active["provider"]
    print(f"Active: {label} - {active['model']}")
    ws = resolve_workspace(getattr(args, "workspace", None))
    if ws:
        _sync_workspace_status(ws, active["provider"], active["model"])
        _sync_deployment_plan(ws, active["provider"], active["model"])
        print(f"Updated {workspace_model_status(ws)}")
    return 0


def cmd_setup(args: argparse.Namespace) -> int:
    ids = list_provider_ids()
    reg = load_registry()
    print("Select a model provider:\n")
    for i, pid in enumerate(ids, 1):
        meta = reg.get(pid, {})
        print(f"  {i}. {pid} - {meta.get('label', pid)}")
    choice = args.provider
    if not choice:
        choice = input("\nProvider id or number: ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if idx < 0 or idx >= len(ids):
            print("Invalid number", file=sys.stderr)
            return 1
        choice = ids[idx]
    meta = get_provider(choice)
    if not meta:
        print(f"Unknown provider: {choice}", file=sys.stderr)
        return 1
    env_key = meta.get("env_key", "")
    if meta.get("auth") == "api_key" and env_key:
        ok, msg = check_provider_key(meta["id"])
        if not ok:
            print(f"\n{msg}")
            if not args.non_interactive:
                val = getpass.getpass(f"Enter {env_key} (hidden): ").strip()
                if val:
                    _write_secret(env_key, val)
                    print(f"Saved to {secrets_env_path()}")
            else:
                print("Run: loop model set-key", env_key, file=sys.stderr)
                return 1
    if meta["id"] == "custom" and not args.non_interactive:
        base = input("Base URL (OpenAI-compatible): ").strip()
        if base:
            cfg = load_config()
            cfg.setdefault("custom", {})["base_url"] = base
            save_config(cfg)
    model = args.model or ""
    if not model and not args.non_interactive and meta["id"] != "custom":
        _print_model_preview(meta["id"])
        default = meta.get("default_model", "")
        entered = input(f"\nModel id from provider [{default or 'required'}]: ").strip()
        model = entered or default
    elif not model:
        model = meta.get("default_model", "")
    if meta["id"] == "custom" and not model and not args.non_interactive:
        model = input("Model id: ").strip()
    if not model:
        print("Model id is required.", file=sys.stderr)
        return 1
    cfg = set_active(meta["id"], model)
    active = cfg["active"]
    print(f"\nConfigured: {active['provider']} - {active['model']}")
    ws = resolve_workspace(getattr(args, "workspace", None))
    if ws:
        _sync_workspace_status(ws, active["provider"], active["model"])
        _sync_deployment_plan(ws, active["provider"], active["model"])
    for name, ok, msg in doctor_active():
        print(f"  [{'OK' if ok else 'WARN'}] {name}: {msg}")
    return 0


def cmd_set_key(args: argparse.Namespace) -> int:
    key = args.key.strip()
    val = args.value
    if not val and not args.non_interactive:
        val = getpass.getpass(f"{key} (hidden): ").strip()
    if not val:
        print("No value provided", file=sys.stderr)
        return 1
    _write_secret(key, val)
    print(f"Saved {key} to {secrets_env_path()}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    if args.all:
        for pid, ok, msg in doctor_all_keys():
            print(f"[{'OK' if ok else 'FAIL'}] {pid}: {msg}")
        return 0
    failed = any(not ok for _, ok, _ in doctor_active())
    for name, ok, msg in doctor_active():
        print(f"[{'OK' if ok else 'FAIL'}] {name}: {msg}")
    return 1 if failed else 0


def cmd_custom_add(args: argparse.Namespace) -> int:
    entry = add_custom_provider(args.name, args.base_url, args.key_env or "")
    print(f"Added custom provider `{entry['name']}` -> {entry['base_url']}")
    print(f"Select it with: loop model custom:{entry['name']}:<model-id>")
    if args.key_env:
        print(f"Set its key with: loop model set-key {args.key_env}")
    return 0


def cmd_custom_list(_: argparse.Namespace) -> int:
    cfg = load_config()
    providers = cfg.get("custom_providers") or []
    if not providers:
        print("No named custom providers. Add one with: loop model custom add <name> <base_url>")
        return 0
    for entry in providers:
        key = entry.get("env_key", "") or "(no key)"
        print(f"  {entry.get('name')}: {entry.get('base_url')} [{key}]")
    return 0


def cmd_fallback_add(args: argparse.Namespace) -> int:
    provider_id, model, custom_name = parse_selection(args.selection)
    if custom_name:
        print("Fallback entries do not support named custom providers yet.", file=sys.stderr)
        return 1
    try:
        cfg = add_fallback(provider_id, model)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    fallback = cfg.get("fallback") or []
    print(f"Fallback chain ({len(fallback)}):")
    for i, fb in enumerate(fallback, 1):
        print(f"  {i}. {fb.get('provider')}:{fb.get('model')}")
    return 0


def cmd_fallback_list(_: argparse.Namespace) -> int:
    cfg = load_config()
    fallback = cfg.get("fallback") or []
    if not fallback:
        print("No fallback providers configured. Add one with: loop model fallback add <provider:model>")
        return 0
    for i, fb in enumerate(fallback, 1):
        print(f"  {i}. {fb.get('provider')}:{fb.get('model')}")
    return 0


def cmd_fallback_clear(_: argparse.Namespace) -> int:
    clear_fallback()
    print("Fallback chain cleared.")
    return 0


def cmd_context_set(args: argparse.Namespace) -> int:
    set_context_length(str(args.value))
    print(f"Context length override set to {args.value}")
    return 0


def cmd_context_show(_: argparse.Namespace) -> int:
    cfg = load_config()
    value = cfg.get("context_length", "")
    if value:
        print(f"Context length override: {value}")
    else:
        print("No context length override set. Provider registry context_min is used as a floor when present.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Loop Engineer model provider CLI")
    p.add_argument("--workspace", help="Product workspace path")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("status", help="Show active provider").set_defaults(func=cmd_status)
    lst = sub.add_parser("list", help="List providers")
    lst.add_argument("provider", nargs="?", default=None, help="Provider id for detail")
    lst.set_defaults(func=cmd_list)

    mdl = sub.add_parser("models", help="Fetch live model list from provider API")
    mdl.add_argument("provider", nargs="?", default=None, help="Provider id (default: active)")
    mdl.add_argument("--search", default="", help="Filter model ids")
    mdl.set_defaults(func=cmd_models)

    use = sub.add_parser("use", help="Set active provider[:model]")
    use.add_argument("selection", help="e.g. anthropic:claude-opus-4-20250514")
    use.set_defaults(func=cmd_use)

    setup = sub.add_parser("setup", help="Interactive provider setup wizard")
    setup.add_argument("--provider", help="Provider id")
    setup.add_argument("--model", help="Model id (any id the provider accepts)")
    setup.add_argument("--non-interactive", action="store_true")
    setup.set_defaults(func=cmd_setup)

    sk = sub.add_parser("set-key", help="Save API key to secrets.env")
    sk.add_argument("key", help="Env var name e.g. OPENROUTER_API_KEY")
    sk.add_argument("value", nargs="?", default="", help="Key value (omit to prompt)")
    sk.add_argument("--non-interactive", action="store_true")
    sk.set_defaults(func=cmd_set_key)

    doc = sub.add_parser("doctor", help="Check keys and connectivity")
    doc.add_argument("--all", action="store_true", help="Check all registered providers")
    doc.set_defaults(func=cmd_doctor)

    custom = sub.add_parser("custom", help="Manage named custom OpenAI-compatible endpoints")
    custom_sub = custom.add_subparsers(dest="custom_cmd")
    ca = custom_sub.add_parser("add", help="Add/update a named custom endpoint")
    ca.add_argument("name", help="Short name, e.g. local")
    ca.add_argument("base_url", help="OpenAI-compatible base URL")
    ca.add_argument("--key-env", default="", help="Env var name holding this endpoint's API key")
    ca.set_defaults(func=cmd_custom_add)
    cl = custom_sub.add_parser("list", help="List named custom endpoints")
    cl.set_defaults(func=cmd_custom_list)
    custom.set_defaults(func=cmd_custom_list)

    fb = sub.add_parser("fallback", help="Manage the fallback provider chain")
    fb_sub = fb.add_subparsers(dest="fallback_cmd")
    fba = fb_sub.add_parser("add", help="Append a provider:model to the fallback chain")
    fba.add_argument("selection", help="e.g. openrouter:anthropic/claude-sonnet-4")
    fba.set_defaults(func=cmd_fallback_add)
    fbl = fb_sub.add_parser("list", help="List the fallback chain")
    fbl.set_defaults(func=cmd_fallback_list)
    fbc = fb_sub.add_parser("clear", help="Clear the fallback chain")
    fbc.set_defaults(func=cmd_fallback_clear)
    fb.set_defaults(func=cmd_fallback_list)

    ctx = sub.add_parser("context", help="Manage the context-length override")
    ctx_sub = ctx.add_subparsers(dest="context_cmd")
    ctxs = ctx_sub.add_parser("set", help="Set context length override")
    ctxs.add_argument("value", type=int)
    ctxs.set_defaults(func=cmd_context_set)
    ctxg = ctx_sub.add_parser("show", help="Show context length override")
    ctxg.set_defaults(func=cmd_context_show)
    ctx.set_defaults(func=cmd_context_show)

    return p


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        return cmd_status(argparse.Namespace())
    known = (
        "status",
        "list",
        "models",
        "use",
        "setup",
        "set-key",
        "doctor",
        "custom",
        "fallback",
        "context",
        "-h",
        "--help",
    )
    if argv[0] not in known:
        ns = argparse.Namespace(selection=" ".join(argv), workspace=None)
        return cmd_use(ns)
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        return cmd_status(args)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
