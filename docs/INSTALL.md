# Install / Use Loop Engineer

Users operate Loop Engineer through slash commands and natural language in their coding
agent. The installed `bin/loop` program is an internal runtime bridge, not a user CLI. See
[`docs/INTERNAL_RUNTIME.md`](docs/INTERNAL_RUNTIME.md).

## One-liner install (GitHub)

**Windows:**

```powershell
irm https://raw.githubusercontent.com/harshpgoti/loop-engineer/main/install.ps1 | iex
```

**Mac / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/harshpgoti/loop-engineer/main/install.sh | bash
```

### Layout after install (all platforms)

```text
~/.loop-engineer/
├── app/           # updatable tool runtime
├── bin/loop       # internal bridge used by coding-agent skills
└── data/          # ALL global memory/data
    ├── memories/  # global memory (default)
    ├── state.db
    ├── skills/
    ├── plan/main_plan.md
    └── ...
```

Local product folders get the same split, nested one level deeper: `<product-folder>/.loop-engineer/{memories,state.db,skills,plan/main_plan.md,...}` - a single hidden folder, kept out of your product code. See [`docs/DATA_LAYOUT.md`](docs/DATA_LAYOUT.md).

### Memory: global vs local

| Mode | Where data lives | How to set up |
|------|------------------|---------------|
| **Global** (installer default) | `~/.loop-engineer/data/` | Just run the installer |
| **Local** | `<product-folder>/.loop-engineer/` | See below |

**Auto-detection:** When you work from a local product folder that already has a `.loop-engineer/` data dir, `/plan-loop` and `/loop-engine` use it automatically. Otherwise they use global `~/.loop-engineer/data/`.

**Local setup in your product folder:**

**Windows:**

```powershell
cd H:\POC\QEAutoAI
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/harshpgoti/loop-engineer/main/install.ps1))) -UseCwd
```

**Mac / Linux:**

```bash
cd ~/projects/my-app
curl -fsSL https://raw.githubusercontent.com/harshpgoti/loop-engineer/main/install.sh | bash -s -- --use-cwd
```

Or after install, open your coding agent in the product folder and run
`/setup-loop-engine`. For global mode, the installer has already created the workspace.

**Coming from another AI tool?** Run `/migrate-import` in your coding agent and provide
the export path. The skill classifies and imports memory, user profile, and skills without
requiring terminal syntax.

Imports `MEMORY.md`, `USER.md`, `SOUL.md`, and `skills/` from `--source`. If the other tool's files use **different names/structure**, add `--scan` - every file is classified by content and routed to the right home (secrets are never copied). See `skills/migrate-import/SKILL.md`.

### After install

The installer wires **every coding agent** you have (Claude, Codex, Cursor,
Gemini, OpenCode, ...) to this one app, so `/plan-loop` and the rest work in any
of them — and keep working if you switch agents mid-task. Just open your agent and
run `/plan-loop` (or describe the task).

```text
/doctor
/plan-loop
/upgrade-loop-engineer  # only when you explicitly want to update now
```

**Auto-update:** every `session-start` silently fast-forwards the app once/hour
(disable with `LOOP_AUTO_UPDATE=off`).

### Maintainer-only team mode (shared repos)

This is one of the few deliberate shell-administration surfaces. Product users do not need
it. From inside a repo, make Loop the standard for teammates — they get bootstrapped
automatically when they open any agent, no out-of-band instructions:

```bash
loop team-init required     # or: optional (nudge instead of block)
# review, then: git add .agents/ .claude/ CLAUDE.md && git commit -m "require Loop"
# or one-shot:
loop team-init required --commit
```

See [`docs/DATA_LAYOUT.md`](docs/DATA_LAYOUT.md) and [`docs/DISTRIBUTION.md`](docs/DISTRIBUTION.md).

---

## Manual central-tool layout

```text
Main/
├── loop-engineer/   # or clone to ~/.loop-engineer/app/
└── product/         # local memory
```

Open the coding agent in `loop-engineer/`, run `/setup-loop-engine`, and identify
`../product` as the product workspace when asked.

## Validate template

```bash
python scripts/validate_template.py
```
