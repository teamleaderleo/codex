# Agent 2 test/runtime report: code-mode orphan sessions

Date: 2026-07-26

## Verified negative reproduction

- Branch: `research/code-mode-live-session-test`
- Commit: `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
- Test: `code_mode_completion_does_not_surface_discarded_live_exec_sessions`
- Verified runtime: Linux aarch64 in the local Lima `smolrunner` VM
- Result: `1 passed; 0 failed; 0 ignored`

Exact command used by the final harness:

```sh
RUST_MIN_STACK=8388608 \
CARGO_BUILD_JOBS=4 \
CARGO_INCREMENTAL=1 \
CARGO_PROFILE_TEST_DEBUG=0 \
CARGO_TARGET_DIR=/home/lima/.cache/codex-orphan-target \
RUST_BACKTRACE=1 \
cargo test -p codex-core \
  --test code_mode_orphan_sessions \
  code_mode_completion_does_not_surface_discarded_live_exec_sessions \
  -- --exact --nocapture
```

The passing negative regression confirms:

- two nested `exec_command` calls yield;
- JavaScript discards both returned `session_id` values by retaining only `output`;
- both background terminals remain registered after the cell completes;
- the outer status says `Script completed`;
- the outer status does not disclose either live session;
- panic-safe teardown terminates all registered terminals and verifies no survivors remain.

The local machine log path is intentionally omitted.

## Preserved baseline evidence

The negative reproduction commit is intentionally unchanged and remains the clean executable proof of the defect. Do not rewrite its expectation in place.

## Patch 1 acceptance-test preparation

- Branch: `research/code-mode-live-session-acceptance`
- Base: `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
- Acceptance-test commit: `528171c72c06d8be3471752322b7755a1eac3ac8`
- Handoff-note commit on that branch: `1ae28a191a7885438abf15f61de273ab37551768`
- Test file: `codex-rs/core/tests/code_mode_orphan_sessions.rs`

The main positive acceptance test retains the same two-process reproduction, obtains the actual process IDs from `CodexThread::list_background_terminals()`, sorts them numerically, and requires the completion status to contain each exact ID once and in deterministic numeric order. It does not hard-code sample IDs or exact warning prose.

Additional focused cases prepared:

1. One yielded process exits before the outer summary while another survives; only the survivor's actual ID is expected.
2. A 65,536-character emitted payload must not truncate or displace the live-session warning.
3. An ordinary yielded cell must retain `Script running with cell ID ...` and must not receive the completion-oriented process warning.

All cases retain `catch_unwind`, terminate all registered terminals after assertions, and verify the final terminal list is empty.

The positive acceptance suite has not yet been run against Agent 1's implementation. It is expected to fail against the unchanged baseline behaviour.

## Agent 1 integration contract

No new public test-only API is required. The tests derive expected IDs from the existing background-terminal listing API.

Production code must expose internally at completion-summary time:

- typed creator-cell attribution for each stored unified-exec process;
- the concrete process ID;
- a live-only snapshot restricted to the completing cell;
- deterministic numeric ordering;
- completion-only formatting, leaving ordinary yielded responses unchanged;
- warning placement outside emitted-output truncation.

## Platform limitations

- Verified on Linux aarch64 under Lima.
- Shell fixtures use `printf` and `sleep` and are intended for Linux/macOS Unix environments.
- Tests remain ignored on Windows in this coverage path.
- A shared portable long-running helper is follow-up cleanup, not a Patch 1 blocker.
- Only the focused negative regression was run; the full `codex-core` and workspace suites were not run.

## Compact handoff

```text
Agent: 2 / test-runtime prototype
Branch/ref: research/code-mode-live-session-test @ 7298dcf44f61164ffc25b8bdf5f136281caeb9f5
Acceptance branch: research/code-mode-live-session-acceptance @ 528171c72c06d8be3471752322b7755a1eac3ac8
Baseline: 20dafe201d91d4405eef05ecd1db0257f13a9ac8
Changed files: codex-rs/core/tests/code_mode_orphan_sessions.rs; this report
Tests run and results: focused negative regression passed, 1/1, Linux aarch64 Lima
Confirmed findings: discarded nested session IDs remain live and are absent from the outer completion status
Open risks: acceptance suite still needs Agent 1 implementation, formatting, compilation, focused run, and broader core validation
Decision requested: integrate the acceptance test with typed creator-cell attribution rather than call-ID parsing
Recommended next action: cherry-pick or merge the acceptance-test commit onto Agent 1's branch, run the focused file with RUST_MIN_STACK=8388608, then run formatting and the relevant core suite
```
