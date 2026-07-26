# Agent 2 test-polish supplemental validation receipt

Date: 2026-07-26

Owner: Agent 2

Requested by:

- `notes/code-mode-orphan-fix/agent-3-test-polish-review-cc01596.md`
- review commit `8224df4ef450e25c76612dff94bc5496fa1c4548`

## Published branch and commits

- Branch: `review/code-mode-roundtable-test-polish`
- Clean candidate before test polish: `3778e1fae6e7e3d885252282a7c5ce67e06730ff`
- Original test-polish head: `cc01596b75abb38335ecdfe07688f155b0dd15a9`
- Supplemental head: `760216784efaee1ba6a3b1250349f31d5f91c7ca`
- Supplemental commit message: `test: add code-mode compatibility coverage`
- Relationship to original test-polish head: one commit ahead, zero behind
- Relationship to clean candidate: two commits ahead, zero behind
- Scope: tests only; no production files changed

Independent GitHub comparison reports the supplemental commit changes only:

```text
M codex-rs/core/src/unified_exec/mod_tests.rs
M codex-rs/core/tests/suite/code_mode/orphan_sessions.rs
```

The full test-polish branch relative to the clean candidate changes only:

```text
M    codex-rs/core/src/unified_exec/mod_tests.rs
M    codex-rs/core/tests/suite/code_mode.rs
R074 codex-rs/core/tests/code_mode_orphan_sessions.rs
     codex-rs/core/tests/suite/code_mode/orphan_sessions.rs
```

## Supplemental changes

### Direct manager-query unit coverage

Added network-independent unit test:

`live_process_ids_created_by_cell_filters_exited_and_sorts`

It inserts deterministic process fixtures into the existing unified-exec test store and proves in one query that:

- entries whose `creator_cell_id` exactly matches the requested cell are included;
- entries attributed to another cell are excluded;
- entries with `creator_cell_id: None` are excluded;
- entries whose process state is exited are excluded;
- the returned process IDs are numerically sorted.

The expected result is exactly:

```text
[1001, 3003]
```

No production method or visibility was changed.

### Large-output acceptance contract

Removed the exact `items.len() == 2` requirement from `large_emitted_output_does_not_truncate_live_session_warning`.

The test now asserts the actual contract:

1. it locates a separate text item beginning with the completion status prefix;
2. that status item contains `Background sessions still running:`;
3. the status contains the correct live process ID summary;
4. at least one other text item contains non-empty emitted-output representation.

The assertion does not pin the complete content-item serialization shape.

### Compatibility expectations

No existing compatibility-test expectation was changed. The repeated candidate/base comparison did not expose a candidate-only optional-header race.

## Repository-native commands

All focused tests were run through the repository `just test` recipe, which invokes nextest with repository configuration.

Formatting and scoped fix:

```text
just fmt
just fix -p codex-core
```

Four focused unit tests:

```text
just test -p codex-core --lib -E 'test(/(live_process_ids_created_by_cell_filters_exited_and_sorts|terminal_cell_id_excludes_yielded_responses|terminal_script_status_surfaces_sorted_live_background_sessions|yielded_script_status_does_not_surface_background_sessions)$/)' --no-capture --no-tests=fail
```

Five aggregate acceptance cases:

```text
just test -p codex-core --test all -E 'test(/suite::code_mode::orphan_sessions::/)' --no-capture --no-tests=fail
```

Compatibility filter used for every repetition:

```text
just test -p codex-core --test all -E 'test(/suite::code_mode::(code_mode_can_run_multiple_yielded_sessions|code_mode_wait_can_terminate_and_continue)$/)' --no-capture --no-tests=fail
```

The compatibility command was run:

- ten times from a detached worktree at exact upstream base `61a44880a85d2fd0d8770908dea5733495e571c8`;
- ten times from candidate head `760216784efaee1ba6a3b1250349f31d5f91c7ca` before commit publication;
- on the same Linux aarch64 Lima runner;
- with the same target cache: `/home/lima/.cache/codex-orphan-target`.

Final checks:

```text
git status --short --untracked-files=all
git diff --check 3778e1fae6e7e3d885252282a7c5ce67e06730ff 760216784efaee1ba6a3b1250349f31d5f91c7ca
```

## Results

- `just fmt`: passed.
- `just fix -p codex-core`: passed.
- Focused unit tests: `4 passed; 0 failed`.
- Aggregate orphan-session acceptance cases: `5 passed; 0 failed`.
- Exact upstream-base compatibility repetitions: `10 repetitions x 2 tests = 20 passed; 0 failed`.
- Candidate compatibility repetitions: `10 repetitions x 2 tests = 20 passed; 0 failed`.
- Candidate-only optional-header race: not observed.
- Compatibility expectation changes: none.
- `git status --short --untracked-files=all`: no output after commit; clean.
- `git diff --check`: no output; passed.
- Exact commit bundle verification: passed.
- Fast-forward publication to `review/code-mode-roundtable-test-polish`: passed.
- Independent GitHub comparison: supplemental head is exactly one two-file test commit ahead of `cc01596`.

No broad `codex-core` project suite or complete workspace suite was run. The prior broad-suite classification remains baseline/environment-limited and not green.

Validation log filename retained by the user:

`code-mode-test-polish-supplement-20260726T113557Z.log`

## Handoff to Agent 3

Please review:

```text
cc01596b75abb38335ecdfe07688f155b0dd15a9...760216784efaee1ba6a3b1250349f31d5f91c7ca
```

Then review the complete test-polish branch against the clean candidate:

```text
3778e1fae6e7e3d885252282a7c5ce67e06730ff...760216784efaee1ba6a3b1250349f31d5f91c7ca
```

The four supplemental requests from the `cc01596` review are complete:

- direct manager-query unit coverage;
- repository-native focused rerun;
- repeated candidate/base compatibility evidence;
- contract-level large-output assertion.

Agent 2 requests final-head approval and consolidation of `760216784efaee1ba6a3b1250349f31d5f91c7ca` if the supplemental diff passes review.
