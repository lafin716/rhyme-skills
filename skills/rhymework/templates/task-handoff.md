# Task Handoff: {{Task ID}}

- Role / installed agent_type: {{role and supported type}}
- Purpose / requirements: {{goal, requirement IDs}}
- Complexity / requested tier / effective model / reasoning / reason: {{resolved choice; unknown if unavailable}}
- Read first: {{applicable AGENTS, PROGRESS, MASTER_PLAN, ARCHITECTURE, task documents, source files}}
- Dependencies: {{IDs and evidence they are DONE}}
- Ownership / allowed files: {{exclusive paths}}
- Forbidden files: {{shared contracts, other owners, PROGRESS unless exclusive write handoff}}
- Expected output: {{artifacts and contract}}
- Validation: {{commands/actions, environment, pass criteria}}
- Completion criteria: {{implementation and evidence}}

Check current Task state before work. Request/emit IN_PROGRESS at start; the leader persists the event unless you have exclusive progress writer ownership. You are not alone in the workspace: do not revert others' edits or write outside ownership. Request shared changes from the leader. Do not recursively delegate. Implementation complete means REVIEW; run validation and report evidence. Only successful validation permits DONE; the leader confirms the state. Return changed files, actual validation results, blockers, contract implications and notes for the next agent.

## Escalation / Resume Context (when applicable)

{{Task ID, original requirements, current implementation and changed files, failed commands/log paths, attempts, hypotheses vs facts, current PROGRESS state, next discriminating check. Never include secret values.}}
