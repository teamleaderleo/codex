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

The repository-native `just test -p codex-core` command was not green:

- 3,110 tests executed;
- 3,017 passed;
- 93 failed;
- 9 skipped;
- command exit 100.

The handoff identifies absent helper binaries, sandbox aborts, and unrelated assertions among the failures. No ad hoc Cargo fallback was used. However, the same command was not run against the exact clean upstream base in the same environment. The full 93-test failure set therefore cannot yet be classified as baseline-equivalent from the recorded evidence alone.

This red project result is not evidence that Patch 1 failed: the changed-area focused tests and complete acceptance target passed, and the candidate files are byte-identical to the previously focused-validated tree. It is nevertheless an unresolved submission-validation classification item and must not be described as a green `codex-core` project suite.

## Verdict

### Clean candidate code, scope, and history

**Pass.**

The clean candidate is suitable for final team review. No Patch 1 code change is requested.

### Submission validation

**Qualified / incomplete.**

Final publication sign-off remains withheld on validation classification, not on code equivalence or Patch 1 correctness.

## Minimal next validation step

Run the same repository-native command against the exact upstream base `61a44880a85d2fd0d8770908dea5733495e571c8` in the same runner configuration:

`just test -p codex-core`

Compare at minimum:

- failed-test names;
- skip set;
- failure classes;
- helper-binary and sandbox failures;
- any failure in code-mode or unified-exec areas;
- aggregate counts.

Decision rule:

- If the clean candidate introduces no new failures relative to the matched upstream-base run, classify the broad project result as baseline/environment-limited and close this validation item.
- If the clean candidate introduces new failures, investigate only the differential failures before publication.

A complete workspace run is not required for this differential classification and remains subject to explicit human approval.

## Other scope clarifications

Agent 1 confirmed Patch 2 and Patch 3 were planning labels for separate follow-up families, not approved implementation contracts. Do not infer or publish additional patch commitments from those labels.

The delayed cross-turn dispatch path remains a high-confidence static finding only. It is not reproduced and remains outside Patch 1.
