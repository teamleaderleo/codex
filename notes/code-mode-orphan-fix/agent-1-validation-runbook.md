# Agent 1 integrated-branch validation runbook

Date: 2026-07-26

Canonical branch:

```text
fix/code-mode-live-session-summary
```

Expected starting head:

```text
4263facaf3c7d30b26cae33fd1e679278ac02105
```

This head is a two-parent merge of the reviewed typed-attribution implementation and the verified acceptance-test lineage. Do not replace it with the documentation-only Agent 2 handoff commit. Do not squash before validation and review.

## Environment

Run in the existing Linux aarch64 Lima VM and reuse the established target directory:

```sh
export CARGO_BUILD_JOBS=4
export CARGO_INCREMENTAL=1
export CARGO_PROFILE_TEST_DEBUG=0
export CARGO_TARGET_DIR=/home/lima/.cache/codex-orphan-target
export RUST_BACKTRACE=1
```

The repository `just test` recipe sets `RUST_MIN_STACK=8388608` and uses the local nextest profile.

## 1. Resolve the canonical branch

```sh
cd ~/Projects/codex
git fetch origin
git switch fix/code-mode-live-session-summary
git reset --hard origin/fix/code-mode-live-session-summary
test "$(git rev-parse HEAD)" = "4263facaf3c7d30b26cae33fd1e679278ac02105"
git status --short
```

Stop if the head differs or the worktree is not clean.

## 2. Format and inspect

From the repository root:

```sh
just fmt
git diff --check
git status --short
git diff --stat
git diff -- codex-rs/core/src/tools/code_mode/mod.rs \
  codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs \
  codex-rs/core/src/unified_exec/mod.rs \
  codex-rs/core/src/unified_exec/process_manager.rs \
  codex-rs/core/tests/code_mode_orphan_sessions.rs
```

Expected: formatting-only changes, if any. One known candidate is the wrapped `finish_network_approval_after_process_exit_for_entry` call in `process_manager.rs`. Do not accept unrelated formatting churn.

If formatting changes files, commit them separately:

```sh
git add codex-rs
git commit -m "style: format code-mode live-session patch"
git push origin fix/code-mode-live-session-summary
```

Record the resulting head before continuing.

## 3. Compile before integration execution

```sh
cargo check -p codex-core --tests
```

Record success or the complete compiler diagnostic. Do not proceed to the acceptance file if compilation fails.

## 4. Focused code-mode unit tests

```sh
just test -p codex-core terminal_cell_id_excludes_yielded_responses
just test -p codex-core terminal_script_status_surfaces_sorted_live_background_sessions
just test -p codex-core yielded_script_status_does_not_surface_background_sessions
```

## 5. Focused unified-exec tests

```sh
just test -p codex-core unified_exec_persists_across_requests
just test -p codex-core multi_unified_exec_sessions
just test -p codex-core pruning_does_not_evict_live_process_while_exited_process_is_finalizing
```

Platform or sandbox skips must be recorded exactly rather than treated as passes.

## 6. Complete acceptance file

Run serially from the canonical integrated branch:

```sh
just test -p codex-core \
  --test code_mode_orphan_sessions \
  --test-threads=1 \
  --nocapture
```

Expected cases:

```text
code_mode_completion_reports_only_sessions_created_by_current_cell
code_mode_completion_reports_only_surviving_nested_session
code_mode_completion_surfaces_discarded_live_exec_sessions
large_emitted_output_does_not_truncate_live_session_warning
yielded_cell_response_does_not_include_completion_session_warning
```

Expected result on Linux aarch64:

```text
5 passed; 0 failed; 0 ignored
```

Every test must leave no background terminal registered after panic-safe teardown.

## 7. Final inspection

```sh
git status --short
git diff --check
git log --oneline --decorate -8
git diff --stat 20dafe201d91d4405eef05ecd1db0257f13a9ac8...HEAD
git diff --name-status 20dafe201d91d4405eef05ecd1db0257f13a9ac8...HEAD
```

Confirm that Patch 1 remains visibility-only: no automatic termination, shutdown-policy, interrupt-policy, subagent-policy, dispatch-policy, or macOS recovery changes.

## Required report

```text
Runner:
Platform:
Starting head:
Final head:
Formatting command and result:
Formatting diff:
Compile command and result:
Focused code-mode tests:
Focused unified-exec tests:
Acceptance command and result:
Skips:
Flakes/retries:
Background-terminal cleanup result:
Unexpected diff findings:
Decision requested:
```

Do not open an upstream issue or PR. Do not squash until Agent 3 reviews the validated net diff.