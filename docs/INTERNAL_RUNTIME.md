# Internal Runtime Boundary

Loop Engineer is used through coding-agent skills and slash commands, not through a
terminal CLI.

## Public interface

Users interact with:

- `/plan-loop`, `/develop-product`, and `/loop-engine`
- the other slash-command skills listed in `AGENTS.md`
- equivalent natural-language requests in coding agents that support skill routing

Installers wire thin router skills into each supported coding harness. Those routers read
the canonical command and skill files from the installed app.

## Internal deterministic runtime

The installed `bin/loop` executable is retained as a private bridge between coding-agent
skills and deterministic Python modules. It owns operations that should not be recreated by
free-form model edits:

- session lifecycle and workspace resolution
- doubt and parent-finding parsing/resolution
- product hierarchy synchronization
- feature creation and convergence
- graph, freshness, evidence, and output validation
- eval result persistence
- installation, migration, update, and diagnostic administration

The shell bridge is an implementation detail. Command and skill files may invoke it; normal
user documentation must not require users to chain runtime commands.

## Compatibility policy

- Primitive runtime operations remain supported for skills, tests, installers, and
  maintainers.
- The free-form `loop plan-loop "<idea>"` orchestration alias is compatibility-only and
  emits a deprecation notice. `/plan-loop <idea>` is the public interface.
- Existing scripts are not broken in this change. No workspace file format or state
  transition changes.
- Maintainer-only shell operations may remain documented in explicitly labelled sections.

## Removal gate

Do not delete `bin/loop` or `scripts/loop_cli.py` until every supported coding harness has a
portable replacement for invoking deterministic operations (for example a stable tool API
or universally supported MCP transport), installed routers no longer reference the shell
bridge, and a versioned migration exists for external automation. Until then, deleting the
runner would move rules-first state transitions back into nondeterministic model behavior.

