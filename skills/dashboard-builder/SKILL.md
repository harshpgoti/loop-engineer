---
name: dashboard-builder
description: Build a small, deterministic dashboard for the chain or the active product from a YAML spec. The dashboard is a single HTML file with inline SVG, no external dependencies, and is regenerated on every release. Use when the chain or product needs a status page, a metric tracker, or a release dashboard without spinning up a separate service.
---

# Dashboard Builder

Inherits `docs/SKILL_CONTRACT.md`.

A small, deterministic discipline for building a status dashboard
from a YAML spec. The dashboard is a single HTML file with inline
SVG, no external dependencies, and is regenerated on every release.
Useful for the chain (chain health) and the active product
(metric tracker).

## When to use

- The chain needs a status page (`/chain-bench` results over time,
  audit history, drift reports).
- The active product needs a small metric tracker that the user
  checks weekly.
- The user wants a release dashboard without spinning up a
  separate service.
- A new feature ships and needs a small per-feature dashboard.

## When NOT to use

| Instead of this skill | Use |
|---|---|
| A full observability stack | Datadog, Grafana, or equivalent |
| A real-time dashboard | a streaming pipeline |
| An interactive dashboard | a JS framework, not this skill |

## The Dashboard Spec

The dashboard is described by a YAML file:

```yaml
dashboard:
  title: "Chain Health"
  panels:
    - title: "Skill count"
      type: counter
      source: scripts/chain_bench.py
    - title: "Test pass rate"
      type: counter
      source: python -m unittest discover -s scripts -p "test_*.py"
    - title: "Open doubts"
      type: counter
      source: grep -c "^- \[" DOUBTS.md
    - title: "Drift"
      type: table
      source: scripts/living_docs_audit.py
```

Each panel has a `title`, a `type` (counter, table, or sparkline), and
a `source` (a script or a shell command that emits JSON).

## Workflow

### 1. Write the spec

`docs/CHAIN_DASHBOARD.yaml` (or `<workspace>/plan/DASHBOARD.yaml`).

### 2. Generate the dashboard

```bash
python scripts/dashboard.py --spec docs/CHAIN_DASHBOARD.yaml --out docs/CHAIN_DASHBOARD.html
```

The script reads the spec, runs each `source` to get a JSON value,
and emits a single HTML file with inline SVG.

### 3. Commit and serve

The HTML is committed to the repo. The user opens it from the file
system or serves it via a tiny static server. No JS frameworks, no
CDN, no external dependencies.

## Output

A single HTML file at the path specified by `--out`. The file is
self-contained: it works offline, in `file://`, on a USB stick.

```html
<!DOCTYPE html>
<html>
<head><title>Chain Health</title></head>
<body>
  <section>
    <h2>Skill count</h2>
    <p>91</p>
  </section>
  ...
</body>
</html>
```

## Anti-Patterns

- **A dashboard with too many panels.** A dashboard with 30 panels
  is one the user cannot read in 30 seconds. Limit to 6-8 panels.
- **A dashboard that hides the source.** Each panel must show the
  source command (so the user can re-run it). A panel with no
  source is a magic number.
- **A dashboard that is not regenerated.** A dashboard that is
  rebuilt only on a release is the right cadence. A dashboard that
  is rebuilt on every commit is too much.
- **A dashboard that needs a server.** The HTML must work in
  `file://`. A dashboard that needs a server is a different
  product.

## Related Skills

- `chain-bench` - the source of the data for the chain health
  dashboard.
- `release-check` - the trigger for the dashboard regeneration.
- `living-docs-governance` - the source of the drift panel.

## Stop Conditions and Rollback

### When to stop

- The YAML spec is malformed or missing required fields; the script
  emits a clear error and exits non-zero.
- The spec declares panels whose `source` commands do not return
  parseable JSON or text; the panel renders as `no data` and the
  report flags it.
- The output file's parent directory is not writable; the script
  exits non-zero.
- The HTML output exceeds 1 MB; the dashboard is too dense and the
  output is split or the spec is reviewed.

### When to escalate to the user

- A panel's `source` runs a command that has never been run before;
  the user verifies it is safe.
- The dashboard spec is updated in a way that exposes sensitive data
  to the dashboard (the user confirms what is shown).
- A release of the chain or product wants to commit a dashboard
  HTML that contains PII (the user reviews before commit).

### Rollback path

- **A single-panel rollback** is reverting the spec to the previous
  version and re-running the script. The previous HTML is overwritten
  on the same path; git `git restore <dashboard.html>` recovers the
  old version.
- **A spec rollback** is reverting the YAML spec file; the script
  regenerates the HTML from the previous spec.
- **A generated-HTML rollback** is `git checkout <previous-commit> --
  <dashboard.html>`; the script is rerun on the next release to
  produce a fresh HTML.
- **A wrong-data rollback** is reverting the source of the data
  (e.g. the script that emits the panel's JSON). The dashboard
  reflects the source's state at regeneration time; the source is
  the single source of truth.
