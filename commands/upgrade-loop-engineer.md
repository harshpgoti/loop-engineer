# /upgrade-loop-engineer

Upgrade Loop Engineering OS without losing product data.

## How To Interpret

If the user says `/upgrade-loop-engineer`, `upgrade loop engineer`, `update loop engine`, or asks how to pull new tool changes safely, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/upgrade-loop-engineer/SKILL.md`
3. `memories/MEMORY.md`
4. `HANDOFF.md`
5. `COMPACT.md`
6. `docs/UPGRADE.md`

## Protected Product-State Files

Never overwrite these during a tool upgrade:

```text
plan/main_plan.md
plan/
MEMORY.md
DOUBTS.md
TASKS.yml
GATES.yml
HANDOFF.md
CURRENT_STATE.md
DECISIONS.md
EVIDENCE_LOG.md
COMPACT.md
.ai/
docs/
```

## Separate Folder Setup

For:

```text
Main/
├── loop-engineer/
└── product/
```

Upgrade only the tool:

```bash
cd loop-engineer
git pull
python scripts/validate_template.py
```

Do not copy product data into `loop-engineer/`.

## Embedded Setup

If Loop Engineering OS files were copied into a product repo:

1. Run `/compact-loop`.
2. Back up or commit product work.
3. Run dry-run first:

```bash
python path/to/new-loop-engineer/scripts/upgrade_loop_engineer.py --source path/to/new-loop-engineer --target path/to/product
```

4. If dry-run looks safe, apply:

```bash
python path/to/new-loop-engineer/scripts/upgrade_loop_engineer.py --source path/to/new-loop-engineer --target path/to/product --apply
```

The script backs up overwritten tool files and refuses to touch protected product-state files.

## Output

Return:

1. Setup detected: separate or embedded
2. Protected files confirmed
3. Dry-run or apply result
4. Validation result
5. Next command
