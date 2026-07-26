# Agent 2 test/runtime report: code-mode orphan sessions

Date: 2026-07-26

## Preserved negative reproduction

- Branch: `research/code-mode-live-session-test`
- Commit: `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
- Test: `code_mode_completion_does_not_surface_discarded_live_exec_sessions`
- Verified runtime: Linux aarch64 in the local Lima `smolrunner` VM
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

The passing negative regression confirms that two nested `exec_command` calls can yield, JavaScript can discard both returned `session_id` values, both manager-owned processes can remain alive after cell completion, and the outer completion result can omit both live IDs. Panic-safe teardown removed every registered process and verified no survivors.

This commit remains intentionally unchanged as the clean executable baseline proof of the defect.

## Corrected acceptance branch

- Branch: `research/code-mode-live-session-acceptance`
- Current verified head: `89ffd99b81e872e3a961767e67fb8ec410df7eae`
- Base negative commit: `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
- Initial acceptance commit: `528171c72c06d8be3471752322b7755a1eac3ac8`
- Contract/isolation correction: `0ba57a73ea5895883a21aeb88e923d75a74ed38d`
- Truncation-assertion correction: `89ffd99b81e872e3a961767e67fb8ec410df7eae`
- Documentation-only branch commit: `1ae28a191a7885438abf15f61de273ab37551768`
- Test file: `codex-rs/core/tests/code_mode_orphan_sessions.rs`

The branch ref was confirmed to resolve exactly to `89ffd99b81e872e3a961767e67fb8ec410df7eae` after the successful run.

## Verified positive integration run

The complete acceptance file was run against Agent 1's typed creator-cell implementation:

- Agent 1 implementation head: `cea3f73d97897ca5ede37010cbd96addbabda6a5`
- Applied test commits, in order:
  1. `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
  2. `528171c72c06d8be3471752322b7755a1eac3ac8`
  3. `0ba57a73ea5895883a21aeb88e923d75a74ed38d`
  4. `89ffd99b81e872e3a961767e67fb8ec410df7eae`
- Environment: Linux aarch64 under Lima
- Cargo cache: `/home/lima/.cache/codex-orphan-target`
- Result: `5 passed; 0 failed; 0 ignored`
- Test execution time reported by the harness: `16.37s`

Exact successful test command:

```sh
RUST_MIN_STACK=8388608 \
CARGO_BUILD_JOBS=4 \
CARGO_INCREMENTAL=1 \
CARGO_PROFILE_TEST_DEBUG=0 \
CARGO_TARGET_DIR=/home/lima/.cache/codex-orphan-target \
RUST_BACKTRACE=1 \
cargo test -p codex-core \
  --test code_mode_orphan_sessions \
  -- --nocapture --test-threads=1
```

Verified tests:

```text
code_mode_completion_reports_only_sessions_created_by_current_cell ... ok
code_mode_completion_reports_only_surviving_nested_session ... ok
code_mode_completion_surfaces_discarded_live_exec_sessions ... ok
large_emitted_output_does_not_truncate_live_session_warning ... ok
yielded_cell_response_does_not_include_completion_session_warning ... ok

result: ok. 5 passed; 0 failed; 0 ignored
```

The local host log path is intentionally omitted.

## What the positive suite now proves

1. A terminal code-mode result surfaces both actual surviving session IDs exactly once and in deterministic numeric order.
2. The status begins with `Script completed\n`, places a tolerant session-summary line before `\nWall time `, and does not depend on matching the complete warning sentence.
3. When one nested process exits before completion, only the actual surviving process is reported.
4. A large emitted payload may be truncated normally, but it cannot truncate or displace the separately prepended live-session status warning.
5. An ordinary yielded cell remains completion-neutral and does not receive the terminal live-session warning.
6. Two-cell creator isolation is enforced: a process created by Cell A is not reported as belonging to Cell B.
7. Every case retains panic-safe cleanup and verifies that no background terminals survive test teardown.

The first integrated run reached `4 passed; 1 failed` because the large-output test incorrectly required the truncated emitted payload to start with raw `x` characters. Commit `89ffd99b81e872e3a961767e67fb8ec410df7eae` corrected only that over-specific test assertion. The complete five-test file then passed.

## Integration guidance for Agent 1

For a minimal implementation branch, start from:

```text
cea3f73d97897ca5ede37010cbd96addbabda6a5
```

Then apply the code/test commits in this order:

```text
7298dcf44f61164ffc25b8bdf5f136281caeb9f5
528171c72c06d8be3471752322b7755a1eac3ac8
0ba57a73ea5895883a21aeb88e923d75a74ed38d
89ffd99b81e872e3a961767e67fb8ec410df7eae
```

`1ae28a191a7885438abf15f61de273ab37551768` is documentation-only and optional for the implementation branch.

No new public test API is required. The tests derive expected IDs from the existing `CodexThread::list_background_terminals()` API.

## Remaining scope and limitations

- Verified platform: Linux aarch64 under Lima.
- Shell fixtures use `printf` and `sleep`; this coverage is intended for Linux/macOS Unix environments.
- Tests remain ignored on Windows because `exec_command` is unavailable there in this path.
- The complete focused acceptance file passed; this report does not claim that the full `codex-core` or workspace suite has passed.
- Formatting and broader focused unit validation remain Agent 1/integrator responsibilities.
- The canonical `coordination-status.md` remains integrator-owned and was not edited by Agent 2.

## Compact handoff

```text
Agent: 2 / regression and acceptance-test owner
Negative proof: research/code-mode-live-session-test @ 7298dcf44f61164ffc25b8bdf5f136281caeb9f5 (unchanged, verified 1/1)
Acceptance head: research/code-mode-live-session-acceptance @ 89ffd99b81e872e3a961767e67fb8ec410df7eae
Implementation tested: fix/code-mode-live-session-summary @ cea3f73d97897ca5ede37010cbd96addbabda6a5
Tests run: complete code_mode_orphan_sessions file, serial, Linux aarch64 Lima
Result: 5 passed; 0 failed; 0 ignored
Confirmed: disclosure, numeric ordering, one-survivor filtering, large-output separation, yielded neutrality, exact creator-cell isolation, panic-safe cleanup
Open work: Agent 1 integrates the ordered commits, formats, runs focused unit tests and broader validation, then publishes a clean tested implementation head
```