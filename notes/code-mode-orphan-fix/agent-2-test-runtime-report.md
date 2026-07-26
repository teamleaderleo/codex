# Agent 2 test/runtime report: code-mode orphan sessions

Date: 2026-07-26

## Final status

Patch 1 is green on the published Rust-formatted canonical head:

- Branch: `fix/code-mode-live-session-summary`
- Published head: `73e5b9fc28de0815975fad3c3d70a6a0b38399b1`
- Formatting commit parent: `4263facaf3c7d30b26cae33fd1e679278ac02105`
- Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
- Platform: Linux aarch64 under Lima
- Publication: exact recovered commit object, fast-forward only, no squash

Validation results:

```text
cargo check -p codex-core --tests                         passed
focused code-mode library tests                          3 passed; 0 failed
focused unified-exec library tests                       3 passed; 0 failed
code_mode_orphan_sessions acceptance target              5 passed; 0 failed; 0 ignored
acceptance harness execution                             17.12s
skips/flakes                                             none
```

The final Lima checkout reported:

```text
git status --short
(no output; clean)

git diff --check
(no output; passed)
```

## Preserved evidence lineage

- Negative proof: `research/code-mode-live-session-test` at `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
- Corrected acceptance head: `research/code-mode-live-session-acceptance` at `89ffd99b81e872e3a961767e67fb8ec410df7eae`
- Initial implementation: `cea3f73d97897ca5ede37010cbd96addbabda6a5`
- Canonical merge before formatting: `4263facaf3c7d30b26cae33fd1e679278ac02105`
- Published tested head: `73e5b9fc28de0815975fad3c3d70a6a0b38399b1`

The negative reproduction remains intentionally unchanged as clean baseline evidence. The complete corrected acceptance file previously passed on the equivalent implementation/test composition and was repeated successfully from the canonical integrated tree after formatting.

## Formatting result

The full `just fmt` path was unavailable in the VM because `just`, `dotslash`, and `uv` were absent. Since Patch 1 changes Rust files only, the explicit reported deviation was:

```sh
cd /home/lima/codex-orphan-integration/codex-rs
cargo fmt --all
```

The recovered formatting commit was published unchanged. GitHub confirms it is exactly one commit ahead of `4263facaf3c7d30b26cae33fd1e679278ac02105` and changes only:

```text
codex-rs/core/src/tools/code_mode/mod.rs
codex-rs/core/src/unified_exec/process_manager.rs
```

Parent-to-formatting-commit comparison:

```text
codex-rs/core/src/tools/code_mode/mod.rs          7 additions, 3 deletions
codex-rs/core/src/unified_exec/process_manager.rs 2 additions, 1 deletion
```

The changes only wrap the `terminal_cell_id` match/assertion and the network-approval finalisation call.

## Compile/check result

Environment:

```sh
export CARGO_BUILD_JOBS=4
export CARGO_INCREMENTAL=1
export CARGO_PROFILE_TEST_DEBUG=0
export CARGO_TARGET_DIR=/home/lima/.cache/codex-orphan-target
export RUST_BACKTRACE=1
```

Command:

```sh
cargo check -p codex-core --tests
```

Result:

```text
Finished `dev` profile [unoptimized + debuginfo] target(s) in 7m 48s
```

The `proc-macro-error2 v2.0.1` future-incompatibility warning is unrelated to Patch 1.

## Focused library tests

The VM lacked `cargo-nextest`. The repository-specific low-memory fallback preserved the library target scope:

```sh
export CARGO_BUILD_JOBS=1
export CARGO_INCREMENTAL=1
export CARGO_PROFILE_TEST_DEBUG=0
export CARGO_TARGET_DIR=/home/lima/.cache/codex-orphan-target
export RUST_BACKTRACE=1
export RUST_MIN_STACK=8388608

cargo test -p codex-core --lib terminal_cell_id_excludes_yielded_responses
cargo test -p codex-core --lib terminal_script_status_surfaces_sorted_live_background_sessions
cargo test -p codex-core --lib yielded_script_status_does_not_surface_background_sessions
cargo test -p codex-core --lib unified_exec_persists_across_requests
cargo test -p codex-core --lib multi_unified_exec_sessions
cargo test -p codex-core --lib pruning_does_not_evict_live_process_while_exited_process_is_finalizing
```

Results:

```text
terminal_cell_id_excludes_yielded_responses ... ok
terminal_script_status_surfaces_sorted_live_background_sessions ... ok
yielded_script_status_does_not_surface_background_sessions ... ok
unified_exec_persists_across_requests ... ok
multi_unified_exec_sessions ... ok
pruning_does_not_evict_live_process_while_exited_process_is_finalizing ... ok

6 passed; 0 failed
```

## Complete acceptance target

Command:

```sh
cargo test -p codex-core \
  --test code_mode_orphan_sessions \
  -- --test-threads=1 --nocapture
```

Result:

```text
code_mode_completion_reports_only_sessions_created_by_current_cell ... ok
code_mode_completion_reports_only_surviving_nested_session ... ok
code_mode_completion_surfaces_discarded_live_exec_sessions ... ok
large_emitted_output_does_not_truncate_live_session_warning ... ok
yielded_cell_response_does_not_include_completion_session_warning ... ok

test result: ok. 5 passed; 0 failed; 0 ignored; finished in 17.12s
```

Every acceptance case retains panic-safe cleanup and verifies that no background terminals survive teardown.

## Infrastructure incident

An initial ad hoc fallback used plain:

```sh
cargo test -p codex-core <test-name>
```

That command widened the build to unrelated integration-test binaries, including `responses_headers` and `all`. Concurrent linkers were killed with signal 9. This was a runner/resource and tool-selection failure, not a Patch 1 compile error or failed assertion. The corrected explicit `--lib` commands passed all six focused tests.

## Baseline net comparison

GitHub comparison from `20dafe201d91d4405eef05ecd1db0257f13a9ac8` to `73e5b9fc28de0815975fad3c3d70a6a0b38399b1` reports 18 commits, 664 additions, 4 deletions, and exactly seven changed files:

```text
M codex-rs/core/src/tools/code_mode/mod.rs
M codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs
M codex-rs/core/src/unified_exec/mod.rs
M codex-rs/core/src/unified_exec/mod_tests.rs
M codex-rs/core/src/unified_exec/process_manager.rs
M codex-rs/core/src/unified_exec/process_manager_tests.rs
A codex-rs/core/tests/code_mode_orphan_sessions.rs
```

## What the validation proves

1. Terminal code-mode results surface surviving nested sessions created by the current cell.
2. Session IDs appear once and in deterministic numeric order.
3. Exited processes are excluded while live processes remain visible.
4. Large emitted output cannot truncate or displace the separately prepended session status.
5. Yielded responses remain completion-neutral.
6. Exact typed creator-cell attribution prevents cross-cell disclosure.
7. Existing unified-exec persistence behaviour remains intact in the focused tests.
8. Process pruning does not evict a live process while an exited process is finalising.
9. Acceptance teardown leaves no registered background terminal behind.

## Remaining gate

Complete:

- implementation integration;
- Rust formatting and two-file inspection;
- compile/check;
- six focused tests;
- five acceptance tests;
- exact-commit publication;
- clean worktree check;
- whitespace check;
- expected seven-file baseline comparison.

Still open before upstream publication:

1. Agent 3 final net-diff review for attribution, liveness, ordering, output placement, and absence of lifecycle-policy expansion.
2. Agent 4 evidence and related-issue refresh.
3. Integrator update of `coordination-status.md`.
4. Do not squash or open the upstream issue/PR until those reviews are complete.

## Compact handoff

```text
Agent: 2 / regression, acceptance, and runtime-validation support
Published tested head: fix/code-mode-live-session-summary @ 73e5b9fc28de0815975fad3c3d70a6a0b38399b1
Parent: 4263facaf3c7d30b26cae33fd1e679278ac02105
Baseline: 20dafe201d91d4405eef05ecd1db0257f13a9ac8
Formatting commit: exact recovered object, two approved files, no squash
Compile/check: passed
Focused code-mode: 3 passed; 0 failed
Focused unified-exec: 3 passed; 0 failed
Acceptance: 5 passed; 0 failed; 0 ignored; 17.12s
Status: clean
Diff check: passed
Open work: Agent 3 review, Agent 4 refresh, integrator board update
Decision: ready for Agent 3 net-diff review; do not squash yet
```
