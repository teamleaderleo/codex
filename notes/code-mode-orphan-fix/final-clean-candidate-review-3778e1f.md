# Final clean-candidate review: `3778e1fae6e7e3d885252282a7c5ce67e06730ff`

Date: 2026-07-26

Reviewer lane: Agent 3 — ownership audit and independent net-diff review

## Scope

Upstream base:

`61a44880a85d2fd0d8770908dea5733495e571c8`

Clean candidate:

`3778e1fae6e7e3d885252282a7c5ce67e06730ff`

Reviewed investigation head:

`73e5b9fc28de0815975fad3c3d70a6a0b38399b1`

Clean comparison:

`61a44880a85d2fd0d8770908dea5733495e571c8...3778e1fae6e7e3d885252282a7c5ce67e06730ff`

Agent 1 handoff:

`notes/code-mode-orphan-fix/agent-1-clean-candidate-handoff.md` at `0a6e63cb5e97db6cf076a9559f71697ea21bce70`

Machine-readable receipt branch:

`automation/agent1-clean-candidate-results`

Matched project-failure inventory:

`notes/code-mode-orphan-fix/agent-1-clean-candidate-project-failure-inventory.md` at `a3cdd18d2cd8e60e5997c25dd41d55b1af2ec2db`

## Independent repository checks

- Current `openai/codex` main still equals `61a44880a85d2fd0d8770908dea5733495e571c8` at review time.
- The clean candidate is exactly one commit ahead of that upstream base.
- The candidate changes exactly seven reviewed files: six production/internal-test files plus `codex-rs/core/tests/code_mode_orphan_sessions.rs`.
- The clean comparison contains 660 insertions and 4 deletions.
- No coordination, research, audit, runtime-report, issue-draft, retrospective, or agent-handoff Markdown is present in the clean candidate.
- No upstream conflict adaptation was required because the two upstream commits after the investigation baseline touched none of the seven Patch 1 files.

## Exact reviewed-tree equivalence

Each of the seven candidate files has the same Git blob SHA as the corresponding file at `73e5b9fc28de0815975fad3c3d70a6a0b38399b1`:

1. `codex-rs/core/src/tools/code_mode/mod.rs`
2. `codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs`
3. `codex-rs/core/src/unified_exec/mod.rs`
4. `codex-rs/core/src/unified_exec/mod_tests.rs`
5. `codex-rs/core/src/unified_exec/process_manager.rs`
6. `codex-rs/core/src/unified_exec/process_manager_tests.rs`
7. `codex-rs/core/tests/code_mode_orphan_sessions.rs`

Therefore the clean candidate preserves the exact previously reviewed Patch 1 production and acceptance-test contents. The clean reconstruction introduces no semantic adaptation.

## Contract review

Because the reviewed files are byte-identical, the final Patch 1 findings remain unchanged:

- typed `ToolCallSource::CodeMode` creator attribution reaches stored `ProcessEntry` metadata through typed `CellId` state;
- the unified-exec manager remains the source of truth for current liveness;
- lookup uses exact creator-cell equality, excludes exited processes, and sorts logical IDs;
- lookup is read-only;
- only terminal `Result` and `Terminated` responses disclose surviving sessions;
- ordinary `Yielded` responses remain completion-neutral;
- the live-session summary remains outside emitted-output truncation;
- nested tool-call IDs remain opaque;
- the JavaScript-visible result schema remains unchanged;
- no termination, persistence, pruning, shutdown, interrupt, dispatch, subagent, remote-exec, recovery, or public-protocol policy expansion is present.

## Validation review

Agent 1 recorded:

- `just fmt`: passed, no worktree changes;
- `just fix -p codex-core`: passed, no worktree changes;
- all six Patch 1-focused code-mode and unified-exec tests passed within the repository-native project run;
- dedicated `code_mode_orphan_sessions` target: 5 passed, 0 skipped;
- clean `git status --short`;
- clean `git diff --check`;
- complete workspace test: not run pending explicit human approval.

### Corrected broad project results

The retained nextest output corrected the earlier compact handoff transcription.

Candidate `just test -p codex-core`:

- 3,110 tests run;
- 3,015 passed, including one flaky pass;
- 94 failed;
- one timed out;
- nine skipped.

Exact upstream-base `just test -p codex-core`:

- 3,102 tests run;
- 3,007 passed;
- 94 failed;
- one timed out;
- nine skipped.

The broad project suite was not green on either ref and must not be described as green.

### Independent differential verification

Agent 3 independently inspected the retained raw candidate and upstream logs and reproduced the reported set comparison:

- 93 failed-test names were shared;
- the single timed-out test was shared;
- candidate-only broad-run failure: `codex-core::all suite::unified_exec::unified_exec_formats_large_output_summary`;
- upstream-only broad-run failure: `codex-core::all suite::compact_resume_fork::snapshot_rollback_followup_turn_trims_context_updates`;
- the candidate added eight tests—three code-mode unit tests and five acceptance tests—and all eight passed.

The two differential tests were then run three times on each ref in one shared runner and target cache. All 12 executions passed. The focused artifact status table independently confirms zero exits for every execution.

The candidate-only and upstream-only broad-run failures are therefore classified as concurrency or run-order flakes, not persistent candidate regressions.

The persistent broad-run outcomes are accounted for as:

- missing helper binaries or environment dependencies;
- sandbox, signal, timeout, or runner limitations;
- assertions reproduced on exact upstream.

No persistent candidate-only failure remains. No failure remains potentially related to Patch 1 or unclassified.

### Validation classification

The repository-native broad project suite is **baseline/environment-limited**, not green.

That classification is sufficient to close the clean-candidate differential gate because:

- the exact matched upstream command reproduced the persistent failure set;
- the only two name differences disappeared in repeated focused runs on both refs;
- all changed-area focused tests passed;
- all five dedicated acceptance tests passed;
- the candidate is byte-identical to the previously reviewed Patch 1 files.

A complete workspace run is not required for this differential classification and remains subject to explicit human approval.

## Verdict

### Clean candidate code, scope, and history

**Pass.**

### Submission validation classification

**Pass, with an explicit baseline-red caveat.**

The candidate is ready for final team and human wording review. No Patch 1 code change or further matched project-suite rerun is requested.

Public wording must state the focused and acceptance results accurately and must not claim that the complete `codex-core` project suite or complete workspace suite passed.

## Other scope clarifications

Agent 1 confirmed Patch 2 and Patch 3 were planning labels for separate follow-up families, not approved implementation contracts. Do not infer or publish additional patch commitments from those labels.

The delayed cross-turn dispatch path remains a high-confidence static finding only. It is not reproduced and remains outside Patch 1.
