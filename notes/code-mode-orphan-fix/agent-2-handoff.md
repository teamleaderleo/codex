# Agent 2 handoff: code-mode live nested sessions

## Verified negative reproduction

- Branch: `research/code-mode-live-session-test`
- Commit: `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
- Test: `code_mode_completion_does_not_surface_discarded_live_exec_sessions`
- Host harness used: `run-codex-orphan-test-lima-v5.sh`
- Exact test command run by the harness:

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

Verified on a local Linux aarch64 Lima VM:

```text
test code_mode_completion_does_not_surface_discarded_live_exec_sessions ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
```

The passing negative regression confirms that two nested commands can yield, JavaScript can discard both returned `session_id` values, both terminals remain registered after cell completion, the outer status says `Script completed`, the status omits the live sessions, and panic-safe teardown leaves no registered background terminals.

The original commit is intentionally preserved as the clean executable baseline reproduction. Do not rewrite its assertion in place.

## Patch 1 acceptance tests

- Branch: `research/code-mode-live-session-acceptance`
- Base: `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
- Acceptance-test commit: `528171c72c06d8be3471752322b7755a1eac3ac8`
- Test file: `codex-rs/core/tests/code_mode_orphan_sessions.rs`

The main acceptance test retains the same two-process reproduction but now obtains the real process IDs from `list_background_terminals()`. It sorts the IDs numerically and requires the completion header to contain each exact numeric ID once and in that order. It does not hard-code example IDs or depend on exact warning prose.

Additional focused cases:

1. A short yielded process exits before the outer summary while a second process survives; only the survivor's actual ID may appear.
2. A 65,536-character emitted payload remains separate from, and must not truncate, the live-session warning in the status header.
3. A code-mode cell that yields while still running keeps the ordinary `Script running with cell ID ...` status and must not disclose the nested process ID through the completion-only warning path.

Every case wraps assertions in `catch_unwind`, terminates all registered background terminals afterward, and verifies the final terminal list is empty.

Suggested focused commands after applying Agent 1's implementation:

```sh
RUST_MIN_STACK=8388608 cargo test -p codex-core \
  --test code_mode_orphan_sessions \
  code_mode_completion_surfaces_discarded_live_exec_sessions \
  -- --exact --nocapture
```

```sh
RUST_MIN_STACK=8388608 cargo test -p codex-core \
  --test code_mode_orphan_sessions \
  -- --nocapture
```

The acceptance branch is expected to fail against the baseline production behavior. It has not been runtime-verified against Patch 1 yet because Agent 1's typed creator-cell attribution implementation was not available on this branch at preparation time.

## Agent 1 integration contract

No new public test-only API is required. The test derives expected IDs from the existing `CodexThread::list_background_terminals()` API.

Production code must make the following available internally at completion-summary time:

- typed creator-cell attribution for each live unified-exec process, without relying on call-ID string prefixes;
- the concrete unified-exec process ID;
- a liveness-filtered snapshot restricted to processes created by the completing cell;
- deterministic numeric ordering before formatting;
- completion-only formatting, leaving `RuntimeResponse::Yielded` / `Script running with cell ID ...` unchanged;
- warning placement outside emitted-output truncation so large `text()` output cannot remove it.

The best hook remains the code-mode nested-tool/output path before `ExecCommandToolOutput.process_id` is flattened into generic JavaScript-visible JSON, with the creator-cell identity propagated to the outer runtime response formatter.

## Platform and scope limitations

- Verified runtime: Linux aarch64 under Lima.
- The shell fixtures use `printf` and `sleep`, and are intended for Linux/macOS Unix environments.
- Tests remain ignored on Windows because `exec_command` is not available there in this coverage path.
- A shared portable long-running fixture remains follow-up cleanup rather than a Patch 1 blocker.
- The focused test was run; the full `codex-core` or workspace suite was not run for the negative reproduction commit.
