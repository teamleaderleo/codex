# External review packet: code-mode live nested sessions

Status date: 2026-07-26

This directory is the shortest path for an independent reviewer who should not need to understand the investigation branch graph.

## Current state

- Production implementation review: **pass**.
- Clean production candidate: `3778e1fae6e7e3d885252282a7c5ce67e06730ff`.
- Upstream base used for that candidate: `61a44880a85d2fd0d8770908dea5733495e571c8`.
- Test-conventions review requested a test-only packaging and robustness revision.
- Test-polish branch: `review/code-mode-roundtable-test-polish`.
- At packet creation, the test-polish branch is still identical to the clean candidate; no test-polish commit has been pushed yet.
- No upstream issue or pull request has been published.
- Two later independent static reviews are consolidated in the [external review triage](triage-2026-07-26.md).

## Canonical links

### Problem and proposed public wording

- [Review-only issue draft](issue-draft.md)
- [Review-only pull-request draft](pr-draft.md)
- [External review triage](triage-2026-07-26.md)

These are review snapshots, not the final publication source. Agent 4 will update the final public drafts after the test-only revision establishes the final candidate head.

### Production implementation

- [Clean implementation commit](https://github.com/teamleaderleo/codex/commit/3778e1fae6e7e3d885252282a7c5ce67e06730ff)
- [Clean implementation compared with its upstream base](https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...3778e1fae6e7e3d885252282a7c5ce67e06730ff)
- [Downloadable commit patch](https://github.com/teamleaderleo/codex/commit/3778e1fae6e7e3d885252282a7c5ce67e06730ff.patch)
- [Clean branch tree](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-summary-clean)

The production implementation is the stable object to review now. The pending revision is expected to alter test placement and test robustness only, except for any separately approved presentation-bound hardening.

### Pending test revision

- [Test-polish branch](https://github.com/teamleaderleo/codex/tree/review/code-mode-roundtable-test-polish)
- [Compare test-polish branch with the clean candidate](https://github.com/teamleaderleo/codex/compare/3778e1fae6e7e3d885252282a7c5ce67e06730ff...review/code-mode-roundtable-test-polish)

Reviewers should re-open this comparison after Agent 2 publishes the test-only commit.

### Review conclusions

- [Final roundtable synthesis](../final-roundtable/synthesis.md)
- [Architecture and API-conventions review](../agent-3-architecture-api-conventions-review.md)
- [Clean-candidate review and validation classification](../final-clean-candidate-review-3778e1f.md)
- [Complete broad-test failure inventory](../agent-1-clean-candidate-project-failure-inventory.md)

### Full provenance, only when needed

- [Agent 4 evidence and publication-preparation report](../agent-4-history-issue-report.md)
- [Canonical coordination status](../coordination-status.md)

The provenance links are intentionally secondary. An ordinary code reviewer should start with the issue draft, PR draft, clean comparison, external review triage, and roundtable synthesis.

## Defect in one paragraph

A code-mode JavaScript cell can start nested `tools.exec_command()` processes, let them yield into manager-owned live sessions, discard the returned `session_id` values by projecting only `.output`, and then finish with `Script completed`. The processes intentionally remain alive, but the model-visible terminal result contains no IDs for polling or termination. The proposed patch preserves creator-cell attribution on the stored process entries and reports exact-cell, manager-live session IDs only when that code-mode cell reaches a terminal result.

## Accepted behavioural contract

- Visibility-only; do not terminate or otherwise change process lifetime.
- Unified-exec manager remains the sole source of liveness.
- Carry typed creator-cell attribution onto stored manager process entries.
- Query by exact creator cell and current manager liveness.
- Return deterministic numeric session IDs.
- Report only on terminal `Result` and `Terminated` responses.
- Keep ordinary `Yielded` responses neutral.
- Keep the JavaScript-visible result schema and opaque nested call IDs unchanged.
- Place the status summary outside emitted-output truncation.

## What an external reviewer should check

1. Is `ExecCommandHandler -> UnifiedExecContext -> ProcessEntry` the correct provenance path?
2. Is `UnifiedExecProcessManager` the correct and only liveness authority?
3. Is the manager query exact-cell, live-only, read-only, and race-tolerant as a point-in-time display?
4. Is terminal reporting performed at the correct code-mode output layer?
5. Does any production path accidentally alter persistence, termination, pruning, shutdown, interrupts, dispatch, recovery, or the JavaScript schema?
6. After the test-polish commit appears, do the five acceptance cases remain behaviourally equivalent while following the aggregate integration-test convention?
7. Are the issue and PR drafts accurate, concise, privacy-safe, and appropriately bounded in their validation claims?
8. Do the existing aggregate code-mode header assertions remain stable under the new optional terminal summary?

## Known non-blocking implementation notes

- `ToolCallSource::CodeMode` currently carries the cell ID as a string; `ExecCommandHandler` reconstructs the typed `CellId`. A broader typed-source cleanup is intentionally outside this patch.
- `UnifiedExecContext::with_creator_cell_id(Option<CellId>)` is a minor crate-private API-shape wart but not a correctness problem.
- Process IDs are sorted both by the manager query and the formatter; this is redundant but harmless.
- The summary currently has no independent hard display-cardinality cap; the final review must either approve a bounded presentation or explicitly document reliance on downstream history limits.

## Validation wording boundary

The focused unit tests and five acceptance cases passed. The broad `just test -p codex-core` run was red on both the candidate and the exact upstream base because of shared missing helpers, sandbox/runner limitations, timeouts, and unrelated baseline assertions. Repeated focused runs eliminated the only two differing broad-run failures. Therefore no persistent candidate-only regression remained, but neither the broad project suite nor the complete workspace suite may be described as green. The complete workspace suite was not run.

## Suggested independent-review prompt

> Review the linked issue draft, PR draft, clean implementation comparison, external review triage, and final roundtable synthesis. Focus on ownership/provenance boundaries, manager-owned liveness, terminal-only disclosure, lifecycle non-expansion, API idioms, existing aggregate-suite compatibility, and test robustness. Treat the production implementation commit as stable except for any explicitly approved presentation-bound hardening. Treat the test-polish branch as pending until it differs from the clean candidate. Report blocking defects, likely maintainer objections, validation overclaims, and optional cleanups separately. Do not propose broader lifecycle, recovery, or subagent-policy changes as part of this patch.
