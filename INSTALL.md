# Install / Use Loop Engineer

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
├── app/           # updatable tool - loop update
├── bin/loop
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

Or after install:

```bash
cd H:/POC/QEAutoAI
loop setup --use-cwd --name qeautoai
```

Global setup (no extra flags):

```bash
loop setup
```

**Coming from another AI tool?** Import its memory/skills in the same setup step:

```bash
loop setup --use-cwd --name qeautoai --source /path/to/other-tool/export
loop setup --use-cwd --name qeautoai --source /path/to/other-tool/export --dry-run
```

Imports `MEMORY.md`, `USER.md`, `SOUL.md`, and `skills/` from `--source`. If the other tool's files use **different names/structure**, add `--scan` - every file is classified by content and routed to the right home (secrets are never copied). See `skills/migrate-import/SKILL.md`.

### After install

The installer wires **every coding agent** you have (Claude, Codex, Cursor,
Gemini, OpenCode, ...) to this one app, so `/plan-loop` and the rest work in any
of them — and keep working if you switch agents mid-task. Just open your agent and
run `/plan-loop` (or describe the task).

```bash
loop doctor
loop bootstrap
loop skills install     # re-wire agents (also run automatically by setup/update)
loop update             # updates app only; memory is preserved
```

**Auto-update:** every `session-start` silently fast-forwards the app once/hour
(disable with `LOOP_AUTO_UPDATE=off`).

### Team mode (shared repos)

From inside a repo, make Loop the standard for teammates — they get bootstrapped
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

```bash
cd loop-engineer
loop setup --memory-mode local --workspace ../product --name product
```

## Validate template

```bash
python scripts/validate_template.py
```
