# Agent 1 handoff: clean Patch 1 candidate

Date: 2026-07-26

## Required handoff

```text
Agent: 1 — clean candidate owner
Retrospective comment: https://github.com/teamleaderleo/stensibly/issues/246#issuecomment-5081855675
Patch 2/3 clarification: Patch 2 and Patch 3 were planning labels for separate follow-up families, with candidate mechanisms sketched, not approved implementation contracts. Patch 2 grouped ownership and cleanup-policy questions such as hidden/subagent completion while live yielded work remains. Patch 3 grouped macOS/runtime-loss orphan-recovery mechanisms such as durable process-group tracking, stale-process sweeps, guardians, or stronger termination reporting. Each family still requires its own executable reproduction, ownership statement, policy decision, and issue.
Upstream base SHA: 61a44880a85d2fd0d8770908dea5733495e571c8
Clean branch: fix/code-mode-live-session-summary-clean
Clean head SHA: 3778e1fae6e7e3d885252282a7c5ce67e06730ff
Commit structure and rationale: One coherent commit, `fix: surface live nested code-mode sessions`, containing the visibility-only implementation and focused tests. The intermediate investigation, prototype, correction, merge, runtime-report, review, and retrospective ancestry is excluded.
Changed files: Seven reviewed Rust files only; listed below.
Upstream conflicts or adaptations: None. Current upstream is two unrelated commits beyond the investigation baseline and touched none of the reviewed files. The reviewed seven-file contents apply unchanged.
Formatting command and result: `just fmt` — passed, exit 0, no worktree changes.
Lint/fix command and result: `just fix -p codex-core` — passed, exit 0, no worktree changes.
Focused/project tests and results: `just test -p codex-core` executed 3,110 tests: 3,017 passed, 93 failed, 9 skipped; command exit 100. All six Patch 1-focused code-mode and unified-exec tests passed. The failing set contains runner-dependent failures including absent helper binaries (`codex`, `test_stdio_server`) and sandbox aborts (`Sandbox(Signal(6))`), plus unrelated existing assertions. This project-wide result is recorded as failed/environment-limited, not as a green crate claim and not as evidence that Patch 1 failed.
Acceptance command and result: `just test -p codex-core --test code_mode_orphan_sessions --test-threads=1 --no-capture` — passed; 5 tests run, 5 passed, 0 skipped, 17.203 seconds. Nextest warned that `--test-threads` is ignored with `--no-capture`; the named target still ran all five cases successfully in one integration binary.
Complete workspace test: not run pending explicit human approval.
Skips, flakes, infrastructure failures, or command-selection failures: Project run had 9 skips and 93 persistent failures after retries on the generic hosted runner. Dedicated acceptance had no skips or flakes. The project command was repository-native and intentionally broad; its runner-dependent failures must remain separate from Patch 1 correctness. No ad hoc Cargo fallback was used. Full workspace validation is not claimed.
Repository inspection results: Clean status; `git diff --check` clean; one commit beyond upstream; exactly seven changed files; 660 insertions and 4 deletions; no research Markdown or workflow files on the clean branch.
Clean comparison: https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...3778e1fae6e7e3d885252282a7c5ce67e06730ff
Equivalence assessment against 73e5b9fc28de0815975fad3c3d70a6a0b38399b1: Exact seven-file equality passed. Path equality passed. No reviewed production or acceptance behaviour is missing; no extra lifecycle-policy or research artifact is present.
Open risks: The generic hosted-runner `codex-core` project suite is not green, and no clean upstream baseline was run in that same job to classify every one of the 93 failures. Complete workspace testing remains unapproved and unrun. Agent 3 has not yet issued a final verdict on the clean comparison. Upstream main must be refreshed again immediately before publication if it moves.
Decision requested: Decide whether the targeted green evidence plus the documented generic-runner project failures is sufficient for final clean-candidate review, or whether publication should wait for the project suite under the repository's full official CI harness and/or an explicitly approved complete workspace run.
Recommended next action: Agent 3 reviews the exact clean comparison; Agent 4 updates the unpublished issue/PR evidence to the clean head; the human coordinator decides the remaining validation and publication gate. Do not open the upstream issue or PR yet.
```

## Changed files

1. `codex-rs/core/src/tools/code_mode/mod.rs`
2. `codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs`
3. `codex-rs/core/src/unified_exec/mod.rs`
4. `codex-rs/core/src/unified_exec/mod_tests.rs`
5. `codex-rs/core/src/unified_exec/process_manager.rs`
6. `codex-rs/core/src/unified_exec/process_manager_tests.rs`
7. `codex-rs/core/tests/code_mode_orphan_sessions.rs`

## Named-tree and verification record

```text
upstream_base_sha=61a44880a85d2fd0d8770908dea5733495e571c8
clean_branch=fix/code-mode-live-session-summary-clean
clean_head_sha=3778e1fae6e7e3d885252282a7c5ce67e06730ff
reviewed_head_sha=73e5b9fc28de0815975fad3c3d70a6a0b38399b1
commit_count=1
worktree_sha_before_format=3778e1fae6e7e3d885252282a7c5ce67e06730ff
worktree_dirty_before_format=clean
required_tool_availability=setup-ci,just,dotslash,uv,cargo-nextest
path_equivalence=passed
reviewed_equivalence=passed
format=passed
format_dirty=no
fix=passed
fix_dirty=no
project_tests=failed (exit 100; 3017 passed, 93 failed, 9 skipped)
acceptance=passed (5 passed, 0 skipped)
worktree_sha_after_format_and_fix=3778e1fae6e7e3d885252282a7c5ce67e06730ff
worktree_dirty_after_format_and_fix=clean
complete_workspace_test=not run pending explicit human approval
```

Machine-readable receipt branch:

`automation/agent1-clean-candidate-results`

Receipt files:

- `notes/code-mode-orphan-fix/agent-1-clean-candidate-validation.txt`
- `notes/code-mode-orphan-fix/agent-1-clean-candidate-statuses.txt`

## Relevant focused tests observed passing in the repository-native project run

```text
terminal_cell_id_excludes_yielded_responses
terminal_script_status_surfaces_sorted_live_background_sessions
yielded_script_status_does_not_surface_background_sessions
unified_exec_persists_across_requests
multi_unified_exec_sessions
pruning_does_not_evict_live_process_while_exited_process_is_finalizing
```

## Dedicated acceptance result

```text
Summary [17.203s] 5 tests run: 5 passed, 0 skipped
```

Covered cases:

- exact Cell A/Cell B creator isolation;
- one-survivor live filtering;
- discarded live-session disclosure;
- warning placement outside emitted-output truncation;
- yielded-response neutrality;
- panic-safe cleanup.

No upstream Codex issue or pull request was opened.