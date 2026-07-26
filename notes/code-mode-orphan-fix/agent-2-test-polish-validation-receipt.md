# Agent 2 test-polish validation receipt

Date: 2026-07-26

Owner: Agent 2

## Reviewed and published branch

- Branch: `review/code-mode-roundtable-test-polish`
- Base: `3778e1fae6e7e3d885252282a7c5ce67e06730ff`
- Head: `cc01596b75abb38335ecdfe07688f155b0dd15a9`
- Relationship: one commit ahead of the clean candidate, zero commits behind
- Scope: tests only; no production files changed

## Changed files

GitHub reports the test-polish commit as:

```text
M    codex-rs/core/tests/suite/code_mode.rs
R076 codex-rs/core/tests/code_mode_orphan_sessions.rs
     codex-rs/core/tests/suite/code_mode/orphan_sessions.rs
```

The standalone integration target is therefore removed and represented as a 76% rename into the existing aggregated code-mode suite.

## Test revision implemented

1. Registered `tests/suite/code_mode/orphan_sessions.rs` from the existing `tests/suite/code_mode.rs` aggregate module.
2. Reused the parent code-mode response extraction, text-item access, feature setup, and turn-preparation helpers.
3. Split preparation from submission so every process-creating `submit_turn` call runs inside the cleanup-protected future.
4. Kept cleanup active for success, returned error, and panic paths. The original panic is resumed after cleanup; cleanup errors are surfaced for non-panic failures and logged without hiding an original panic.
5. Replaced the yielded-response numeric-token scan with a direct absence assertion for `Background sessions still running:`.
6. Replaced fixed one-second/two-second sleeps in the exited-session case with a bounded filesystem/PID handshake:
   - the short shell writes its PID and waits for a release file;
   - a foreground nested command creates the release file;
   - it polls `kill -0` for that PID at 50 ms intervals;
   - it succeeds only after the short shell exits, with a five-second upper bound;
   - the long-lived session remains alive for the final summary assertion.
7. Preserved all five behavioural contracts:
   - multiple discarded live sessions are surfaced in numeric order;
   - exited sessions are excluded;
   - the warning remains outside emitted-output truncation;
   - yielded responses remain neutral;
   - only sessions created by the completing cell are reported.

## Exact validation commands

```text
just fmt
just fix -p codex-core
cargo test --manifest-path codex-rs/Cargo.toml -p codex-core --lib terminal_cell_id_excludes_yielded_responses
cargo test --manifest-path codex-rs/Cargo.toml -p codex-core --lib terminal_script_status_surfaces_sorted_live_background_sessions
cargo test --manifest-path codex-rs/Cargo.toml -p codex-core --lib yielded_script_status_does_not_surface_background_sessions
cargo test --manifest-path codex-rs/Cargo.toml -p codex-core --test all 'suite::code_mode::orphan_sessions::' -- --test-threads=1 --nocapture
git status --short --untracked-files=all
git diff --check 3778e1fae6e7e3d885252282a7c5ce67e06730ff cc01596b75abb38335ecdfe07688f155b0dd15a9
```

## Results

- `just fmt`: passed.
- `just fix -p codex-core`: passed.
- Three affected code-mode unit tests: `3 passed; 0 failed; 0 ignored`.
- Five revised aggregate acceptance cases: `5 passed; 0 failed; 0 ignored`.
- `git status --short --untracked-files=all`: no output after commit; clean.
- `git diff --check`: no output; passed.
- Git bundle verification: passed.
- Exact commit publication to `review/code-mode-roundtable-test-polish`: passed.
- Independent GitHub comparison confirms one test-only commit and only the two logical test paths above.

No new broad `codex-core` project run or workspace suite was performed. The prior broad-suite classification remains baseline/environment-limited and not green.

## Execution notes

The validation runner required user-local installation of the repository formatter prerequisites `just`, DotSlash, and `uv`. Several launcher defects were found and corrected before the final successful run: compact untracked-directory status handling, child-module `assert_eq!` macro ambiguity, Cargo workspace manifest location, and an unsupported first deterministic-exit handshake. None of those failed attempts committed or pushed branch changes; each stopped fail-closed before publication.

## Review handoff

Agent 3 should review:

```text
3778e1fae6e7e3d885252282a7c5ce67e06730ff...cc01596b75abb38335ecdfe07688f155b0dd15a9
```

Review focus:

1. test-only scope and unchanged production tree;
2. correct aggregate-module registration and removal of the standalone target;
3. reuse of parent code-mode helpers;
4. cleanup coverage beginning before every process-creating submission;
5. bounded deterministic exit without fixed process races;
6. direct yielded-warning absence assertion;
7. preservation of all five behavioural contracts.

Agent 1 should perform only the requested short contract sanity check. Agent 4 should continue to keep upstream drafts unpublished until Agent 3 approves this diff and the final clean head is consolidated.
