# Acceptance - Step {{STEP_ID}}: {{STEP_TITLE}}

**Updated:** {{DATE}}

Ultraplan is **complete** when every item below is testable and TBD-free.

## Functional acceptance

- [ ] 

## Agent acceptance (if type=agent)

- [ ] Golden eval cases pass
- [ ] Tool calls schema-validated
- [ ] Human escalation path documented

## Non-functional acceptance

- [ ] Performance budget defined
- [ ] Security review items listed
- [ ] Observability (logs/metrics/traces) defined

## Ready for feature spec

- [ ] Overview, PRD, architecture filled
- [ ] Run `loop feature new "{{STEP_TITLE}}" --step plan/step_{{STEP_ID}}_*.md`
- [ ] Run `/spec-clarify` → `/spec-checklist` → task-compiler
