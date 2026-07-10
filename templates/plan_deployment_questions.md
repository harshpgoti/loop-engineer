# Deployment Planning Questions

Use during `/plan-loop` to capture deployment choices early.

## Ask During Planning

- **Cloud provider:** Which cloud provider will we use (AWS, GCP, Azure, Vercel, Fly.io, other)?
- **Cloud strategy:** Will deployment be single-cloud or multi-cloud?
- **Primary region(s):** Which region(s) should production run in?
- **Compute model:** What compute model should we use (containers, serverless, VMs, PaaS)?
- **Database hosting:** Where will the primary database be hosted?
- **LLM provider:** Which LLM provider will the product use?
- **LLM model(s):** Which LLM model(s) should production use?
- **Embedding provider/model:** Which embedding provider/model should production use?
- **Agent runtime:** Where will agent loops run in production?
- **CI/CD platform:** Which CI/CD platform should deploy production?
- **Secrets management:** How should production secrets be managed?

## Reuse Rule

If the user already answered in `DECISIONS.md`, resolved `DOUBTS.md`, or an earlier `/plan-loop` session:

1. Copy the same answer into `plan/main_plan.md` → **Deployment & Infrastructure**
2. Inform the user which decisions were reused
3. Do not ask again unless the user wants to change them

## Write Targets

- `plan/main_plan.md` → **Deployment & Infrastructure**
- `DECISIONS.md` for durable architecture/deployment decisions
- `DOUBTS.md` for unresolved items
- `DEPLOYMENT_PLAN.md` draft via `python scripts/deployment_plan.py --source plan`
