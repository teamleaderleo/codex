# Agent 2 test/runtime report: code-mode orphan sessions

Date: 2026-07-26

## Executive status

Patch 1's implementation and acceptance behaviour are green on the canonical integrated tree after Rust formatting:

- compile/check phase: passed;
- focused code-mode library tests: `3 passed; 0 failed`;
- focused unified-exec library tests: `3 passed; 0 failed`;
- complete acceptance target: `5 passed; 0 failed; 0 ignored`;
- verified platform: Linux aarch64 in the local Lima `smolrunner` VM.

The remote implementation branch still resolves to `4263facaf3c7d30b26cae33fd1e679278ac02105`. The Rust-formatted tree was tested locally, but its formatting-only commit has not been confirmed on the remote branch and its local SHA was not captured in this handoff. Final net-diff inspection and publication of that exact tested tree remain open.

## Preserved negative reproduction

- Branch: `research/code-mode-live-session-test`
- Commit: `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
- Test: `code_mode_completion_does_not_surface_discarded_live_exec_sessions`
- Runtime: Linux aarch64 Lima
- Result: `1 passed; 0 failed; 0 ignored`

Exact verified command:

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

This clean negative commit proves the original visibility defect and remains intentionally unchanged.

## Corrected acceptance lineage

- Branch: `research/code-mode-live-session-acceptance`
- Verified head: `89ffd99b81e872e3a961767e67fb8ec410df7eae`
- Negative proof: `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
- Initial acceptance tests: `528171c72c06d8be3471752322b7755a1eac3ac8`
- Contract/isolation correction: `0ba57a73ea5895883a21aeb88e923d75a74ed38d`
- Truncation assertion correction: `89ffd99b81e872e3a961767e67fb8ec410df7eae`
- Optional documentation-only commit: `1ae28a191a7885438abf15f61de273ab37551768`

The complete acceptance file previously passed against Agent 1's typed-attribution implementation at `cea3f73d97897ca5ede37010cbd96addbabda6a5` with `5 passed; 0 failed; 0 ignored` in 16.37 seconds.

## Canonical integrated branch under validation

- Branch: `fix/code-mode-live-session-summary`
- Remote starting head: `4263facaf3c7d30b26cae33fd1e679278ac02105`
- Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
- First parent: implementation `cea3f73d97897ca5ede37010cbd96addbabda6a5`
- Second parent: acceptance `89ffd99b81e872e3a961767e67fb8ec410df7eae`
- Validation workspace: dedicated Lima checkout
- Cargo target cache: `/home/lima/.cache/codex-orphan-target`

The remote branch was confirmed to resolve exactly to the expected starting head before validation.

## Formatting result

The repository-wide `just fmt` command could not run in the VM because its full formatter prerequisites were absent: `just`, `dotslash`, and `uv`.

Because Patch 1 changes Rust files only, the Rust workspace formatter was run directly:

```sh
cd /home/lima/codex-orphan-integration/codex-rs
cargo fmt --all
```

It changed only the two expected files:

```text
codex-rs/core/src/tools/code_mode/mod.rs
codex-rs/core/src/unified_exec/process_manager.rs
```

The changes were formatting-only:

- wrapping `terminal_cell_id` match formatting and one assertion;
- wrapping `finish_network_approval_after_process_exit_for_entry`.

This is an explicit runbook deviation, not a claim that the full multi-language repository formatter passed.

A local formatting-only commit was created during the run, but its SHA was not captured in the shared evidence and the remote branch remained at `4263facaf3c7d30b26cae33fd1e679278ac02105` when checked through GitHub.

## Compile/check result

Environment used:

```sh
export CARGO_BUILD_JOBS=4
export CARGO_INCREMENTAL=1
export CARGO_PROFILE_TEST_DEBUG=0
export CARGO_TARGET_DIR=/home/lima/.cache/codex-orphan-target
export RUST_BACKTRACE=1
```

Equivalent root-safe command:

```sh
cargo check \
  --manifest-path codex-rs/Cargo.toml \
  -p codex-core \
  --tests
```

Result:

```text
Finished `dev` profile [unoptimized + debuginfo] target(s) in 7m 48s
```

The `proc-macro-error2 v2.0.1` future-incompatibility warning is unrelated to Patch 1.

## Focused code-mode library tests

The VM lacked `cargo-nextest`. Focused unit tests were therefore run against the explicit `codex-core` library test harness with low-memory build concurrency:

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
```

Results:

```text
terminal_cell_id_excludes_yielded_responses ... ok
terminal_script_status_surfaces_sorted_live_background_sessions ... ok
yielded_script_status_does_not_surface_background_sessions ... ok

3 passed; 0 failed
```

## Focused unified-exec library tests

Commands:

```sh
cargo test -p codex-core --lib unified_exec_persists_across_requests
cargo test -p codex-core --lib multi_unified_exec_sessions
cargo test -p codex-core --lib pruning_does_not_evict_live_process_while_exited_process_is_finalizing
```

Results:

```text
unified_exec_persists_across_requests ... ok
multi_unified_exec_sessions ... ok
pruning_does_not_evict_live_process_while_exited_process_is_finalizing ... ok

3 passed; 0 failed
```

After the correctly scoped library harness was linked, the later focused selections reused it and completed with approximately half a second of build time each.

## Complete acceptance target

Exact command:

```sh
cargo test -p codex-core \
  --test code_mode_orphan_sessions \
  -- --test-threads=1 --nocapture
```

Result:

```text
running 5 tests
test code_mode_completion_reports_only_sessions_created_by_current_cell ... ok
test code_mode_completion_reports_only_surviving_nested_session ... ok
test code_mode_completion_surfaces_discarded_live_exec_sessions ... ok
test large_emitted_output_does_not_truncate_live_session_warning ... ok
test yielded_cell_response_does_not_include_completion_session_warning ... ok

test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 17.12s
```

The target compiled in 1m45s before the 17.12-second test execution.

Every acceptance case retains panic-safe teardown through `finish_with_cleanup`, which terminates all registered background terminals and verifies that none remain.

## Infrastructure incident and correction

An initial ad hoc fallback used:

```sh
cargo test -p codex-core <test-name>
```

That command was not equivalent to the repository's nextest selection. It widened the build to unrelated integration-test binaries, including `responses_headers` and `all`. Concurrent linkers were killed with signal 9:

```text
collect2: fatal error: ld terminated with signal 9 [Killed]
```

This was a runner/resource failure caused by an incorrectly broad fallback, not a compile error in Patch 1 and not a failed test assertion. The corrected `--lib` commands above passed all six focused tests.

- Test flakes: none observed.
- Test retries: none; the corrected commands used the intended explicit target scope.
- Platform skips: none in the commands reported here.
- Full workspace validation: not claimed.

## What the green validation proves

1. Terminal code-mode results surface surviving nested sessions created by the current cell.
2. Session IDs appear once and in deterministic numeric order.
3. Exited processes are excluded while surviving processes remain visible.
4. Large emitted output cannot truncate or displace the separately prepended live-session status.
5. Yielded cell responses remain completion-neutral.
6. Exact typed creator-cell attribution prevents cross-cell disclosure.
7. Existing unified-exec persistence behaviour remains intact in the focused tests.
8. Process pruning does not evict a live process while an exited process is finalising.
9. Acceptance teardown leaves no registered background terminal behind.

## Remaining publication gate

Still open:

1. Recover or recreate the exact local formatting-only commit and push it to `fix/code-mode-live-session-summary`.
2. Record the published final head and ensure it represents the exact Rust-formatted tree that passed the tests above.
3. Run and record final inspection:
   - `git status --short`;
   - `git diff --check`;
   - `git log --oneline --decorate -8`;
   - baseline `git diff --stat`;
   - baseline `git diff --name-status`.
4. Agent 3 reviews the published net diff for attribution correctness, liveness filtering, output placement, and lifecycle-policy expansion.
5. Agent 4 fills the remaining evidence and related-issue placeholders.
6. Do not squash or publish an upstream issue/PR until those steps are complete.

## Compact handoff

```text
Agent: 2 / regression, acceptance, and runtime-validation support
Negative proof: research/code-mode-live-session-test @ 7298dcf44f61164ffc25b8bdf5f136281caeb9f5
Acceptance head: research/code-mode-live-session-acceptance @ 89ffd99b81e872e3a961767e67fb8ec410df7eae
Canonical remote start: fix/code-mode-live-session-summary @ 4263facaf3c7d30b26cae33fd1e679278ac02105
Validated tree: local Rust-formatted descendant of 4263fac; local SHA not captured, not confirmed published
Platform: Linux aarch64 Lima
Compile/check: passed
Focused code-mode: 3 passed; 0 failed
Focused unified-exec: 3 passed; 0 failed
Acceptance: 5 passed; 0 failed; 0 ignored; 17.12s
Skips/flakes: none
Infrastructure note: one invalid broad cargo-test fallback OOMed during unrelated integration-test linking; corrected scoped commands passed
Open work: publish the exact formatting-only commit, final diff inspection, Agent 3 review, Agent 4 evidence refresh
Decision: validation is green locally; publication gate remains open until the tested formatted tree is published and reviewed
```
