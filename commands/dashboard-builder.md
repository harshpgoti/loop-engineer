# /dashboard-builder

Build a small, deterministic dashboard for the chain or the active product from
a YAML spec. The dashboard is a single HTML file with inline SVG, no external
dependencies, and is regenerated on every release. Use when the chain or
product needs a status page, a metric tracker, or a release dashboard without
spinning up a separate service.

## How To Interpret

If the user says `/dashboard-builder`, `build a dashboard`, `render the metrics`,
`status page`, or asks for a self-contained HTML dashboard, execute this file
directly.

## Required Reads

1. `AGENTS.md`
2. `skills/dashboard-builder/SKILL.md`
3. `scripts/dashboard.py`
4. the dashboard YAML spec (default: `docs/CHAIN_DASHBOARD.yaml`)

## Loop

```text
READ the YAML spec -> RUN each panel's source -> EMIT a single self-contained HTML file
```

## Script

```bash
python scripts/dashboard.py --spec docs/CHAIN_DASHBOARD.yaml --out docs/CHAIN_DASHBOARD.html
```

## Output

A single self-contained HTML file at the path specified by `--out`. The file
works offline, in `file://`, on a USB stick. No JS frameworks, no CDN.

## Continuation

The HTML is committed to the repo. The next release regenerates it.
`/release-check` verifies the file exists when a dashboard spec is
declared in the manifest.