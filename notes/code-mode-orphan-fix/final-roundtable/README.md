# Final Patch 1 roundtable

Date opened: 2026-07-26

This directory collects the final lane-specific conventions reviews for the clean Patch 1 candidate.

## Reviewed tree

- Upstream base: `61a44880a85d2fd0d8770908dea5733495e571c8`
- Clean candidate: `3778e1fae6e7e3d885252282a7c5ce67e06730ff`
- Clean branch: `fix/code-mode-live-session-summary-clean`
- Roundtable base commit: `c96e66c47a4f2dc54bd69484905e03535f854c49`

Do not modify the clean candidate from this roundtable unless a review identifies a concrete blocking defect.

## Required files

Each agent owns exactly one file and should not edit another agent's review.

- Agent 1: `agent-1-implementation-conventions.md`
- Agent 2: `agent-2-testing-conventions.md`
- Agent 4: `agent-4-publication-conventions.md`

Agent 3's completed architecture review remains at:

- `notes/code-mode-orphan-fix/agent-3-architecture-api-conventions-review.md`

After all three files are integrated, Agent 3 will create:

- `synthesis.md`

The synthesis will distinguish:

1. blocking changes;
2. public-copy corrections;
3. non-blocking maintainer notes;
4. deferred follow-up families;
5. unresolved decisions requiring the human coordinator.

## Branch protocol

To avoid non-fast-forward conflicts, each agent should create a temporary review branch from the roundtable base commit and commit only its assigned file.

- Agent 1 branch: `review/code-mode-roundtable-agent-1`
- Agent 2 branch: `review/code-mode-roundtable-agent-2`
- Agent 4 branch: `review/code-mode-roundtable-agent-4`

Each agent should return its branch name and commit SHA. Agent 3 will then integrate the three files sequentially into `research/code-mode-orphan-handoffs`.

Do not merge the temporary review branch into the clean candidate.

## Review file format

Each review should include:

```text
Agent:
Lane:
Reviewed base:
Reviewed candidate:
Verdict: pass / pass with notes / change requested

Concrete findings:
- ...

Required code or test changes:
- none / ...

Public-copy corrections:
- none / ...

Likely maintainer concerns:
- none / ...

Deferred follow-ups:
- none / ...

Human decisions requested:
- none / ...
```

Keep findings evidence-based and scoped to the assigned lane. Do not reopen Patch 1 lifecycle policy, publish the upstream issue or pull request, or convert Patch 2/3 planning labels into commitments.

## Review ownership

Agent 3 will read all three files, integrate them into the research branch, and prepare the synthesis. Agent 4 should then use only the synthesis and its own publication review to update the unpublished issue and pull-request drafts. A second full reread by every agent is unnecessary unless the synthesis identifies a disagreement or blocking finding.
