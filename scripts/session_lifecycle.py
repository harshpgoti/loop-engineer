#!/usr/bin/env python3
"""Always-on session lifecycle: start recall + end memory review (tool-agnostic)."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from agent_skill_router import run_router as run_agent_router
from agent_router import run_router as run_role_router
from domain_skill_router import run_router as run_domain_router
from frontend_skill_router import run_router
from feature_paths import read_active_feature
from memory_curator import apply_report, propose_updates, render_report
from memory_paths import ensure_memory_layout, session_bootstrap_paths, state_db
from pending_writes import list_pending
from session_recall import append_handoff_pointer, build_query, extract_keywords, render_recall
from session_store import init_db, log_session, recent_sessions, search_sessions
from workspace_utils import resolve_workspace


SESSION_META = ".loop/session.json"
MANIFEST = "plan/SESSION_MANIFEST.md"
CLOSEOUT = "plan/SESSION_CLOSEOUT.md"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    from datetime import date

    return date.today().isoformat()


def _meta_path(workspace: Path) -> Path:
    return workspace / SESSION_META


def read_meta(workspace: Path) -> dict:
    path = _meta_path(workspace)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_meta(workspace: Path, data: dict) -> None:
    path = _meta_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def run_recall(workspace: Path, query: str | None = None, limit: int = 5) -> int:
    db = state_db(workspace)
    init_db(db)
    keywords = extract_keywords(workspace)
    q = query or build_query(keywords)
    hits = search_sessions(db, q, limit=limit)
    if not hits:
        hits = recent_sessions(db, limit=limit)
    out = workspace / "plan" / "SESSION_RECALL.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_recall(workspace, hits), encoding="utf-8")
    append_handoff_pointer(workspace)
    log_session(
        db,
        workspace=str(workspace),
        command="session-start",
        title="Session recall (lifecycle)",
        body=f"query={q!r}; hits={len(hits)}",
        tags="recall lifecycle",
    )
    return len(hits)


def _hierarchy(workspace: Path, *, stage: bool = True) -> dict:
    """Retired. Sub-products are scopes in this workspace, so there is no second
    workspace to sync with (`docs/SCOPES.md`). Kept as an empty result so callers and
    the manifest shape do not have to special-case its absence."""
    return {"enabled": False, "role": None}


def _parent_findings(workspace: Path) -> dict:
    """Retired with the federated layout - a scope has no parent to disagree with."""
    return {"parent": None, "ask": [], "report": [], "total": 0}


def attention_block(workspace: Path) -> list[str]:
    """Anything needing a decision, in the file every command reads first.

    Nobody types `loop ...`. They type a slash command, and the agent works from
    `plan/SESSION_MANIFEST.md`. A capability the manifest never mentions is a
    capability that never runs - which is how the approval queue accumulated 164
    entries nobody drained. Four checks were shipped in exactly that state
    (`loop evidence`, `loop fresh`, `loop graph`, `loop archive`), reachable only by
    someone who already knew they existed.

    So this is the surface. Each line states the condition and the command that
    answers it, and the block is absent entirely when there is nothing to do -
    a standing checklist teaches people to skim past it.
    """
    items: list[tuple[str, str]] = []

    # Doubts come first: an unanswered blocking question invalidates whatever would be
    # planned or built on top of it. This block is the surface every command reads, and
    # doubts were the one thing it never mentioned - so a workspace could carry open
    # blocking questions through planning and into a build without ever being asked.
    try:
        import doubts as _doubts

        askable = _doubts.frontier(workspace)
        if askable:
            head = ", ".join(d.id for d in askable[:3])
            items.append(
                (f"{len(askable)} blocking doubt(s) can be answered now ({head}"
                 f"{', ...' if len(askable) > 3 else ''})",
                 "`loop doubts ask` - one round, each with its recorded default as the "
                 "recommendation; `loop doubts resolve <id> \"<answer>\"` or `loop doubts defer <id> \"<reason>\"`"))
        waiting = _doubts.blocked_behind(workspace)
        if waiting:
            items.append(
                (f"{len(waiting)} doubt(s) wait on an earlier answer, so they are not asked yet",
                 "answer the frontier first - they become askable on their own"))
        delegated = _doubts.delegated_doubts(workspace)
        if delegated:
            items.append(
                (f"{len(delegated)} doubt(s) are addressed to someone who is not here",
                 "`loop doubts questionnaire` - send them out; do not guess the answer"))
    except Exception:
        pass

    try:
        from freshness import stale_views

        stale = stale_views(workspace)
        if stale:
            names = ", ".join(item["view"] for item in stale[:3])
            items.append(
                (f"{len(stale)} generated file(s) no longer match their sources ({names}"
                 f"{', ...' if len(stale) > 3 else ''})",
                 "`loop fresh` - then re-run whatever generates them"))
    except Exception:
        pass

    try:
        from evidence_review import review_due, undated

        due = review_due(workspace)
        if due:
            items.append(
                (f"{len(due)} evidence entr(ies) past their validity window - uncertain, not disproved",
                 "`loop evidence` - re-check, or record a fresh `Date checked`"))
        loose = undated(workspace)
        if len(loose) > 10:
            items.append(
                (f"{len(loose)} evidence entr(ies) carry no `Date checked`, so nothing can age them",
                 "`loop evidence --verbose` - add dates as you touch them"))
    except Exception:
        pass

    try:
        import graph_index
        import graph_schema

        graph = graph_index.build(workspace)
        if graph["nodes"]:
            broken = graph.get("dangling") or []
            if broken:
                items.append(
                    (f"{len(broken)} reference(s) point at an id nothing defines",
                     "`loop graph dangling` - fix the id, or add the record"))
            errors = [f for f in graph_schema.validate(workspace, graph) if f["level"] == graph_schema.ERROR]
            if errors:
                items.append(
                    (f"{len(errors)} reference-graph rule violation(s) - e.g. {errors[0]['rule']}",
                     "`loop graph check` - each finding names its fix"))
    except Exception:
        pass

    try:  # what still stands between this build and a release
        from release_check import assess
        from source_tree_scan import find_source_root

        # Only once something is being built - a plan-stage workspace has nothing to
        # be un-ready about, and saying so every session is noise.
        if find_source_root(workspace) is not None:
            state = assess(workspace)
            if state["blockers"]:
                head = "; ".join(b.split(" - ")[0] for b in state["blockers"][:2])
                items.append(
                    (f"{len(state['blockers'])} launch blocker(s) remain ({head}"
                     f"{', ...' if len(state['blockers']) > 2 else ''})",
                     "`loop release-check` - the full report, with warnings"))
    except Exception:
        pass

    try:
        from state_archive import recall_stats
        from state_archive import DECISIONS_ARCHIVE, EVIDENCE_ARCHIVE, TASKS_ARCHIVE

        archived = any((workspace / rel).is_file() for rel in (TASKS_ARCHIVE, EVIDENCE_ARCHIVE, DECISIONS_ARCHIVE))
        if archived and not recall_stats(workspace).get("searches"):
            items.append(
                ("Detail has been archived but never read back, so compaction may be losing it in practice",
                 "`loop archive --search \"<term>\"` when you need why a finished thing was done that way"))
    except Exception:
        pass

    if not items:
        return []

    lines = ["", "## Needs a decision", "", "Resolve these before planning or building on top of them:", ""]
    for condition, action in items:
        lines.append(f"- {condition}")
        lines.append(f"  - {action}")
    lines.append("")
    return lines


def _scope_block(workspace: Path, command: str | None) -> list[str]:
    """The manifest's scope section: which sub-product this session is about.

    Scope-filtered on purpose. A unified workspace with ten sub-products would
    otherwise put ten plans in front of every command, which is the one way this
    layout could cost more context than the federated one it replaces. Siblings are
    listed by name only; the active scope is the one whose plan is read.
    """
    try:
        import scope_paths as sp
        import scope_state

        if sp.workspace_mode(workspace) != "unified":
            return []
        scopes = sp.list_scopes(workspace)
        if not scopes:
            return []

        res = sp.resolve(workspace, cwd=Path.cwd())
        lines = ["", "## Scope", ""]
        if res.scope is None or res.needs_confirm:
            lines.append(
                "- **Not selected.** Ask which sub-product this is about before writing anything."
            )
            if res.reason:
                lines.append(f"- {res.reason}")
            for scope in scopes:
                lines.append(f"  - `{scope.slug}` - {scope.title} ({scope.code_dir or 'no code dir yet'})")
            lines.append("  - shared platform work - root `TASKS.yml`, CI, schema, design system")
            return lines

        scope = res.scope
        lines.extend(
            [
                f"- **Active scope:** `{scope.slug}` - {scope.title} (source: {res.source})",
                f"- **Plan:** `plan/products/{scope.slug}/` - read `prd.md`, `TASKS.yml`, `GATES.yml`, `DOUBTS.md` there",
                f"- **Code:** `{scope.code_dir or '(not decided - ask during planning)'}`",
            ]
        )
        if scope.provides:
            lines.append(f"- **Provides:** {', '.join(scope.provides)}")
        if scope.consumes:
            lines.append(f"- **Consumes:** {', '.join(scope.consumes)} - see `plan/contracts/`")
        blocks = [
            b
            for b in scope_state.cross_scope_blocks(scope_state.load_tasks(workspace))
            if b["scope"] == scope.slug and not b["satisfied"]
        ]
        for block in blocks:
            lines.append(
                f"- **Blocked:** {block['task']} waits on {block['blocked_by']} in `{block['provider_scope']}`"
            )
        others = [s.slug for s in scopes if s.slug != scope.slug]
        if others:
            lines.append(f"- **Other sub-products (names only):** {', '.join(others)}")
        lines.append(
            "- A change needed in another sub-product: locate it, **ask the user**, then apply it there."
        )
        return lines
    except Exception:
        return []


def render_manifest(
    workspace: Path,
    *,
    command: str | None,
    tool: str | None,
    hits: int,
    auto_skills: list[str],
    auto_agent_skills: list[str] | None = None,
    auto_domain_skills: list[str] | None = None,
    auto_agents: list[str] | None = None,
    update_status: dict | None = None,
    hierarchy: dict | None = None,
    findings: dict | None = None,
) -> str:
    auto_agent_skills = auto_agent_skills or []
    auto_domain_skills = auto_domain_skills or []
    auto_agents = auto_agents or []
    lines = [
        "# Session Manifest",
        "",
        f"**Generated:** {_now()}",
        f"**Workspace:** `{workspace}`",
        "",
        "Always-on memory bootstrap. **Every agent must read these files in order** before acting.",
        "Regenerated by `loop session-start` (any coding agent: Cursor, Claude Code, Codex, OpenCode, Grok, ...).",
        "",
        "## Lifecycle",
        "",
        "- **Start:** `loop session-start` (or `/session-start`) - you are here",
        "- **End:** `loop session-end` (or `/session-end`) before stopping",
        "",
    ]
    if command:
        lines.append(f"- **Active command:** `{command}`")
    if tool:
        lines.append(f"- **Tool hint:** `{tool}`")
    lines.append(f"- **Session recall hits:** {hits}")
    if update_status:
        if update_status.get("updated"):
            lines.append(f"- **App auto-updated:** {update_status['updated']} commit(s) pulled; routers refreshed")
        elif update_status.get("notice"):
            lines.append(f"- **App update:** {update_status['notice']}")
    lines.append("")

    lines.extend(["## Read order", ""])
    lines.append(f"1. `{MANIFEST}` (this file)")
    idx = 2
    for path in session_bootstrap_paths(workspace, command):
        if path.name == "SESSION_MANIFEST.md":
            continue
        try:
            rel = path.relative_to(workspace).as_posix()
        except ValueError:
            rel = str(path)
        exists = "ok" if path.exists() else "missing"
        lines.append(f"{idx}. `{rel}` ({exists})")
        idx += 1

    if auto_skills:
        lines.extend(["", "## Auto frontend skills", ""])
        for name in auto_skills:
            lines.append(f"- `{name}` - see `plan/AUTO_SKILLS.md`")

    if auto_agent_skills:
        lines.extend(["", "## Auto agent-development skills", ""])
        for name in auto_agent_skills:
            lines.append(f"- `{name}` - see `plan/AUTO_AGENT_SKILLS.md`")

    if auto_domain_skills:
        lines.extend(["", "## Auto domain skills", ""])
        for name in auto_domain_skills:
            lines.append(f"- `{name}` - see `plan/AUTO_DOMAIN_SKILLS.md`")

    if auto_agents:
        lines.extend(["", "## Auto agent roles", ""])
        for name in auto_agents:
            lines.append(f"- `{name}` - see `plan/AUTO_AGENTS.md`")

    try:
        from eval_suite import manifest_block as evals_block

        lines.extend(evals_block(workspace))
    except Exception:
        pass

    try:
        from fog import manifest_block as fog_block

        lines.extend(fog_block(workspace))
    except Exception:
        pass

    try:
        from glossary import manifest_block as language_block

        lines.extend(language_block(workspace))
    except Exception:
        pass

    try:
        lines.extend(attention_block(workspace))
    except Exception:
        pass

    bootstrap = workspace / "plan" / "PLAN_BOOTSTRAP.md"
    if bootstrap.exists():
        lines.extend(
            [
                "",
                "## Plan bootstrap",
                "",
                f"- Read `{bootstrap.relative_to(workspace).as_posix()}` - auto scale + ultraplan route from user idea.",
            ]
        )

    if command in ("/plan-loop", "/ultraplan-loop", "/loop-engine", "/spec-clarify", "/spec-checklist") or (
        workspace / "plan" / "main_plan.md"
    ).exists():
        try:
            from plan_phase import render_phase_block

            lines.extend(["", render_phase_block(workspace, heading="## Plan phase")])
        except Exception:
            pass

    # The development counterpart: one phase file and its skills, instead of the
    # 32-item Read First list a build session used to work through.
    from memory_paths import _is_build_command

    if _is_build_command(command) and (workspace / "TASKS.yml").exists():
        try:
            from build_phase import render_phase_block as render_build_phase

            lines.extend(["", render_build_phase(workspace, heading="## Build phase")])
        except Exception:
            pass

    lines.extend(_scope_block(workspace, command))

    active = read_active_feature(workspace)
    if active:
        lines.extend(
            [
                "",
                "## Active feature",
                "",
                f"- **ID:** `{active.get('id')}` - {active.get('title', '')}",
                f"- **Path:** `{active.get('path')}`",
                "- Read `spec.md`, `feature-plan.md`, `tasks.md` in that folder during `/develop-product`.",
            ]
        )

    lines.extend(
        [
            "",
            "## Rules",
            "",
            "- Reuse `plan/SESSION_RECALL.md` - do not re-ask settled decisions.",
            "- Update `HANDOFF.md`, `DOUBTS.md`, `memories/MEMORY.md` before `loop session-end`.",
            "- Memory curator writes this workspace's memory directly; only cross-workspace and skill writes wait for `loop pending approve`.",
            "",
        ]
    )
    return "\n".join(lines)


def _auto_maintenance(workspace: Path) -> list[str]:
    """Chores that used to be separate commands the user had to remember.

    Only work that is deterministic, idempotent, and creates no new plan content
    belongs here - it runs on every `loop session-start`, so anything that authors
    content would author it again every session. That rules out
    `loop plan-loop decompose` (it creates a step pack per map row, including rows
    the plan has deliberately deferred) and `loop sync` (it appends dated notes to
    MEMORY.md and HANDOFF.md). Both stay explicit.
    """
    actions: list[str] = []

    try:  # was: loop plan-loop ultraplan status
        from plan_paths import product_map_file
        from ultraplan_harness import update_ultraplan_status

        if product_map_file(workspace).exists():
            update_ultraplan_status(workspace)
            actions.append("ultraplan status refreshed")
    except Exception:
        pass

    try:  # the task-scoped slice a build session reads instead of the whole files
        from task_context import write_context

        if write_context(workspace) is not None:
            actions.append("build context refreshed for the active task")
    except Exception:
        pass

    try:  # was: loop pending dedupe
        from pending_writes import dedupe_pending

        dropped = dedupe_pending(workspace)
        if dropped:
            actions.append(f"dropped {len(dropped)} duplicate pending write(s)")
    except Exception:
        pass

    try:  # claims whose validity window has closed - epistemic, not mechanical
        from evidence_review import review_due

        due = review_due(workspace)
        if due:
            actions.append(
                f"{len(due)} evidence entr(ies) past their validity window - `loop evidence`"
            )
    except Exception:
        pass

    try:  # generated files that no longer match what they were generated from
        from freshness import stale_views

        stale = stale_views(workspace)
        if stale:
            names = ", ".join(item["view"] for item in stale[:3])
            actions.append(
                f"{len(stale)} generated file(s) out of date ({names}"
                f"{', ...' if len(stale) > 3 else ''}) - `loop fresh`"
            )
    except Exception:
        pass

    try:  # the reference index, and one more day of edge history
        import graph_index

        graph = graph_index.build(workspace)
        if graph["nodes"]:
            graph_index.write(workspace, graph)
            graph_index.record_history(workspace, graph)
            broken = len(graph.get("dangling", []))
            if broken:
                actions.append(f"{broken} dangling reference(s) - run `loop graph dangling`")
    except Exception:
        pass


    return actions


def _auto_update() -> dict:
    """Silent, throttled app self-update. Never raises."""
    try:
        from auto_update import maybe_auto_update, resolve_app_root
        from loop_home import global_data_home

        return maybe_auto_update(resolve_app_root(), global_data_home())
    except Exception as exc:
        return {"skip": f"error: {exc.__class__.__name__}"}


PLAN_BOOTSTRAP_COMMANDS = {
    "/plan-loop",
    "plan-loop",
    "/startup-discovery-loop",
    "startup-discovery-loop",
    "/loop-engine",
    "loop-engine",
    "/all-in-one",
    "all-in-one",
}


def _command_bootstraps_plan(command: str | None) -> bool:
    """Only idea-entry commands may decompose or rewrite the product map."""
    return (command or "").strip().lower() in PLAN_BOOTSTRAP_COMMANDS


def _plan_needs_bootstrap(workspace: Path) -> bool:
    """Bootstrap is initialization, never a resume mechanism.

    Passing planning text to an initialized workspace is routing context. Treating it
    as a new idea rewrites IDEA/PRODUCT_MAP and can rename or recreate step folders.
    """
    main_plan = workspace / "plan" / "main_plan.md"
    if not main_plan.exists():
        return True
    text = main_plan.read_text(encoding="utf-8", errors="ignore")
    return not text.strip() or "UNINITIALIZED" in text.upper()


def session_start(
    workspace: Path,
    *,
    command: str | None = None,
    tool: str | None = None,
    text: str = "",
    skip_recall: bool = False,
) -> dict:
    ensure_memory_layout(workspace)
    update_status = _auto_update()
    hits = 0
    if not skip_recall:
        hits = run_recall(workspace)

    picks = run_router(workspace, extra=text, write=True)
    auto_names = [name for name, _ in picks]

    agent_picks = run_agent_router(workspace, extra=text, write=True)
    auto_agent_names = [name for name, _ in agent_picks]

    domain_picks = run_domain_router(workspace, extra=text, write=True)
    auto_domain_names = [name for name, _ in domain_picks]
    auto_agents = run_role_router(workspace, command=command or "", text=text, domain_skills=auto_domain_names, write=True)

    hierarchy = _hierarchy(workspace)
    findings = _parent_findings(workspace)
    maintenance = _auto_maintenance(workspace)

    plan_bootstrap = None
    if text.strip() and _command_bootstraps_plan(command) and _plan_needs_bootstrap(workspace):
        try:
            from plan_idea import bootstrap_plan

            plan_bootstrap = bootstrap_plan(workspace, text.strip())
        except Exception as exc:
            plan_bootstrap = {"error": str(exc)}

    manifest_path = workspace / MANIFEST
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        render_manifest(
            workspace,
            command=command,
            tool=tool,
            hits=hits,
            auto_skills=auto_names,
            auto_agent_skills=auto_agent_names,
            auto_domain_skills=auto_domain_names,
            auto_agents=auto_agents,
            update_status=update_status,
            hierarchy=hierarchy,
            findings=findings,
        ),
        encoding="utf-8",
    )

    meta = read_meta(workspace)
    meta.update(
        {
            "started_at": _now(),
            "ended_at": None,
            "command": command,
            "tool": tool,
            "recall_hits": hits,
            "auto_skills": auto_names,
            "auto_agent_skills": auto_agent_names,
            "auto_domain_skills": auto_domain_names,
            "auto_agents": auto_agents,
            "manifest": MANIFEST,
            "role": hierarchy.get("role"),
            "sub_products": hierarchy.get("children", 0),
            "maintenance": maintenance,
            # Read by plan_phase to route the parent-findings phase without
            # re-running the drift checks.
            "open_parent_findings": findings.get("total", 0),
            "parent_findings_ask": len(findings.get("ask") or []),
        }
    )
    write_meta(workspace, meta)

    try:
        from event_store import append as append_event

        append_event(
            workspace, "session.started",
            {"command": command, "tool": tool, "auto_agents": auto_agents,
             "auto_domain_skills": auto_domain_names},
            idempotency_key=f"{meta['started_at']}:start",
        )
    except Exception as exc:  # lifecycle remains usable; doctor can report store damage
        meta["event_store_error"] = str(exc)
        write_meta(workspace, meta)

    db = state_db(workspace)
    init_db(db)
    log_session(
        db,
        workspace=str(workspace),
        command=command or "session-start",
        title="Session started",
        body=(
            f"manifest={MANIFEST}; recall_hits={hits}; auto_skills={auto_names}; "
            f"auto_agent_skills={auto_agent_names}; auto_domain_skills={auto_domain_names}; auto_agents={auto_agents}; role={hierarchy.get('role')}; "
            f"sub_products={hierarchy.get('children', 0)}; drift={hierarchy.get('counts')}"
        ),
        tags="lifecycle start hierarchy",
    )

    return {
        "hits": hits,
        "auto_skills": auto_names,
        "auto_agent_skills": auto_agent_names,
        "auto_domain_skills": auto_domain_names,
        "auto_agents": auto_agents,
        "manifest": str(manifest_path),
        "hierarchy": hierarchy,
        "maintenance": maintenance,
        "findings": findings,
    }


def render_closeout(workspace: Path, report: dict, actions: list[str], pending: int) -> str:
    lines = [
        "# Session Closeout",
        "",
        f"**Generated:** {_now()}",
        f"**Workspace:** `{workspace}`",
        "",
        "Always-on memory closeout from `loop session-end`. Read `plan/MEMORY_REVIEW.md` for details.",
        "",
        "## Memory usage",
        "",
        f"- Memory: {report['memory_usage']['chars']}/{report['memory_usage']['limit']} chars",
        f"- User: {report['user_usage']['chars']}/{report['user_usage']['limit']} chars",
        "",
        "## Actions",
        "",
    ]
    if actions:
        lines.extend(f"- {a}" for a in actions)
    else:
        lines.append("- Memory within limits; nothing to curate.")
    lines.extend(
        [
            "",
            f"## Pending writes: {pending}",
            "",
        ]
    )
    if pending:
        lines.append(
            "These need a human decision (cross-workspace or skill writes). "
            "Run `loop pending list`, then approve or reject by id."
        )
    else:
        lines.append("Nothing waiting on a human.")
    lines.extend(["", "## Next agent", "", "Read `plan/SESSION_MANIFEST.md` after the next `loop session-start`.", ""])
    return "\n".join(lines)


def session_end(
    workspace: Path,
    *,
    command: str | None = None,
    summary: str = "",
    apply: bool = True,
    stage: bool = False,
) -> dict:
    ensure_memory_layout(workspace)
    report = propose_updates(workspace)
    review_path = workspace / "plan" / "MEMORY_REVIEW.md"
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(render_report(workspace, report), encoding="utf-8")

    # This workspace's own memory applies directly - see apply_report(). Only
    # cross-workspace and skill writes go through the approval queue, so a
    # closeout no longer leaves work for the user to remember to do.
    actions = apply_report(workspace, report, stage_only=stage)

    # State drift is reconciled here rather than left for the user to notice.
    # `/sync-loop-state` existed as a command the user had to think to run, which meant
    # HANDOFF pointing one way while MEMORY pointed another survived until somebody
    # tripped over it. The mechanical half fixes itself; what is left is reported.
    try:
        from sync_loop_state import detect_drift

        drift, fixes = detect_drift(workspace)
        actions.extend(f"state sync: {fix}" for fix in fixes)
        for item in drift:
            actions.append(f"state drift: {item}")
    except Exception as exc:  # noqa: BLE001 - closeout must never fail on a reconcile
        actions.append(f"state sync skipped: {exc}")

    converge_note = ""
    if _command_reconciles_feature(command):
        try:
            from feature_converge import converge

            report_path, _ = converge(workspace)
            if report_path:
                converge_note = str(report_path.relative_to(workspace))
        except Exception as exc:
            converge_note = f"feature converge skipped: {exc}"
    if converge_note:
        actions.append(f"feature converge: {converge_note}")

    # Fold this session's own edits into the reference index and its edge history.
    # Building only at session-start recorded the state the session *inherited*, so a
    # retraction made during the session stayed invisible until the next one began -
    # the history lagged by a session, which is the one thing a history must not do.
    try:
        import graph_index

        graph = graph_index.build(workspace)
        if graph["nodes"]:
            graph_index.write(workspace, graph)
            closed = graph_index.record_history(workspace, graph)
            graph_index.prune_history(workspace)
            withdrawn = sum(1 for e in closed["edges"].values() if e.get("closed_at") == _today())
            if withdrawn:
                actions.append(f"graph: {withdrawn} reference(s) withdrawn this session")
    except Exception:
        pass

    # Compact finished work at the *end* of a session, never at the start - the
    # session that just closed a task should still see it in full when it writes
    # its handoff. Budget-gated, so a small workspace is never touched.
    try:
        from state_archive import run as compact_state

        for item in compact_state(workspace):
            if item.get("compacted"):
                saved = item["before"] - item["after"]
                actions.append(
                    f"{item['file']}: compacted {len(item['compacted'])} finished entry(ies), "
                    f"-{saved:,} chars (detail in plan/archive/)"
                )
    except Exception:
        pass

    # Refresh the roll-up so the next agent inherits a current view of the tree.
    hierarchy = _hierarchy(workspace, stage=False)
    if hierarchy.get("children"):
        counts = hierarchy.get("counts", {})
        actions.append(
            f"hierarchy: {hierarchy['children']} sub-product(s), "
            f"{counts.get('error', 0)} error / {counts.get('warn', 0)} warning finding(s) "
            "in plan/SUBPRODUCTS.md"
        )
    elif hierarchy.get("parent"):
        actions.append(f"hierarchy: sub-product of `{hierarchy['parent']}` (plan/PARENT_CONTEXT.md refreshed)")

    pending = len(list_pending(workspace))

    closeout_path = workspace / CLOSEOUT
    closeout_path.write_text(render_closeout(workspace, report, actions, pending), encoding="utf-8")

    handoff_excerpt = ""
    handoff = workspace / "HANDOFF.md"
    if handoff.exists():
        handoff_excerpt = handoff.read_text(encoding="utf-8", errors="ignore")[:800]

    body = summary.strip() or handoff_excerpt or review_path.read_text(encoding="utf-8")[:1200]
    db = state_db(workspace)
    init_db(db)
    log_session(
        db,
        workspace=str(workspace),
        command=command or "session-end",
        title="Session ended",
        body=body[:2000],
        tags="lifecycle end memory-review",
    )

    meta = read_meta(workspace)
    meta["ended_at"] = _now()
    meta["last_closeout"] = CLOSEOUT
    meta["pending_writes"] = pending
    write_meta(workspace, meta)

    try:
        from event_store import append as append_event

        append_event(
            workspace, "session.ended",
            {"command": command, "summary": body[:500], "pending_writes": pending},
            idempotency_key=f"{meta.get('started_at') or meta['ended_at']}:end",
        )
    except Exception as exc:
        actions.append(f"event store skipped: {exc}")

    return {
        "review": str(review_path),
        "closeout": str(closeout_path),
        "pending": pending,
        "actions": actions,
        "hierarchy": hierarchy,
    }


FEATURE_RECONCILING_COMMANDS = (
    "/plan-loop",
    "/startup-discovery-loop",
    "/revise-plan",
    "/develop-product",
    "/startup-build-loop",
    "/loop-engine",
    "/all-in-one",
    "/feature-new",
    "/spec-clarify",
    "/spec-checklist",
    "/resolve-doubts",
    "/ultraplan-loop",
)


def _command_reconciles_feature(command: str | None) -> bool:
    """Whether closeout must check active-feature drift for this mutating command."""
    normalized = (command or "").strip().lower()
    return any(name in normalized for name in FEATURE_RECONCILING_COMMANDS)


def main() -> int:
    parser = argparse.ArgumentParser(description="Always-on session lifecycle (start/end).")
    parser.add_argument("phase", choices=("start", "end"))
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--command", default=None, help="Active loop command e.g. /develop-product")
    parser.add_argument("--tool", default=None, help="Tool hint e.g. cursor, claude, codex, cline")
    parser.add_argument("--text", default="", help="Extra context for routers (user message).")
    parser.add_argument("--skip-recall", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Apply memory directly on end (default).")
    parser.add_argument("--stage", action="store_true", help="Stage this workspace's memory writes for approval instead of applying.")
    parser.add_argument("--summary", default="", help="Optional closeout summary for state.db")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)

    if args.phase == "start":
        result = session_start(
            workspace,
            command=args.command,
            tool=args.tool,
            text=args.text,
            skip_recall=args.skip_recall,
        )
        print(f"session-start ok")
        print(f"  manifest: {result['manifest']}")
        print(f"  recall hits: {result['hits']}")
        if result["auto_skills"]:
            print(f"  auto skills: {', '.join(result['auto_skills'])}")
        if result["auto_agent_skills"]:
            print(f"  auto agent skills: {', '.join(result['auto_agent_skills'])}")
        if result["auto_domain_skills"]:
            print(f"  auto domain skills: {', '.join(result['auto_domain_skills'])}")
        if result["auto_agents"]:
            print(f"  auto agent roles: {', '.join(result['auto_agents'])}")
        for action in result.get("maintenance", []):
            print(f"  auto: {action}")
        # Sub-products are scopes in this workspace, so there is no hierarchy to report
        # and no parent findings to drain. Which scope this session is about is stated
        # in the manifest's `## Scope` block instead.
        print("  read plan/SESSION_MANIFEST.md first")
        return 0

    result = session_end(workspace, command=args.command, summary=args.summary, stage=args.stage)
    print("session-end ok")
    print(f"  review: {result['review']}")
    print(f"  closeout: {result['closeout']}")
    print(f"  pending writes: {result['pending']}")
    for action in result["actions"]:
        print(f"  - {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
