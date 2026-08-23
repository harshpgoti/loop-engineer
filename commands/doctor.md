# /doctor

Check whether the Loop Engineering OS runtime and active product workspace are healthy.

## How To Interpret

If the user says `/doctor`, `doctor`, `health check`, `is loop engine healthy`, or `validate setup`, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/doctor/SKILL.md`
3. Registered workspace config
4. Product-state files in the active workspace

## Loop

```text
CHECK TOOL FILES -> CHECK WORKSPACE -> IMPORT SCRIPTS -> RUN VALIDATORS -> WRITE DOCTOR.md
```

## Checks

- Required tool files exist
- Workspace is registered or detectable
- Product-state files exist
- Tool repo is not storing initialized product data
- Scripts import correctly
- Template validation passes
- Product output validation passes when possible
- Memory size vs limits
- `memories/MEMORY.md` drift vs root `MEMORY.md`
- `state.db` FTS5 health
- Missing `memories/USER.md` / `memories/SOUL.md`
- Pending staged writes under `.loop/pending/`
- User skill frontmatter validation

## Optional Script

```bash
python scripts/doctor.py
loop doctor
```

Custom workspace:

```bash
python scripts/doctor.py --workspace ../product
```

## Continuation

**Read-only - deliberately does not cascade.** Analysing and reporting is this
command's product; recommending a next command is correct here, not a
continuation failure. Any *fix* it identifies belongs to `/revise-plan`,
`/develop-product`, or a `TASKS.yml` entry. See `docs/CONTINUATION.md`.

## Output

Return:

1. `DOCTOR.md` path
2. Overall health status
3. Errors and warnings
4. Next recommended command
