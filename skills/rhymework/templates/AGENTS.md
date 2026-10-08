# Project Agent Instructions

Create this file only if the project has no AGENTS.md. Otherwise merge necessary project rules without replacing existing instructions or runtime markers. Replace this notice with the project's actual context.

## Sources and Commands

- Read PROGRESS.md, docs/MASTER_PLAN.md, docs/ARCHITECTURE.md and task-specific documents before work; follow mapped existing paths when different.
- Project build/test commands: {{verified commands}}.
- Target environment and setup guide: {{actual path or justified N/A}}.

## Ownership and Handoff

- Follow the leader's Task IDs and exclusive file ownership; do not revert others' work.
- Shared contracts/schema/plans and PROGRESS are leader-owned by default.
- Send state events to the leader: start IN_PROGRESS, implementation ready REVIEW, validation evidence for DONE, blocked reason for BLOCKED. Direct progress edits require exclusive writer handoff from the leader.
- DONE requires applicable validation success. Report changed files, commands/results, blockers and downstream notes.
- No recursive delegation; return architecture or scope changes to the leader.
- Secrets stay outside tracked documents and logs.
