# Agent 3 review: test-polish commit `cc01596`

Date: 2026-07-26

Reviewed base: `3778e1fae6e7e3d885252282a7c5ce67e06730ff`

Reviewed head: `cc01596b75abb38335ecdfe07688f155b0dd15a9`

## Verdict

**Change requested: narrow validation-and-coverage supplement only.**

The original roundtable test-polish scope is implemented correctly. No production file changed, and no rewrite of the accepted production design is requested. The head is not yet approved as the final clean candidate because the later external-review triage added four concrete requirements that are not present in this commit or receipt.

## Confirmed good changes

1. The branch is one commit ahead of the reviewed clean candidate and changes only two logical test paths.
2. The standalone `codex-rs/core/tests/code_mode_orphan_sessions.rs` target is removed and represented as a rename into `codex-rs/core/tests/suite/code_mode/orphan_sessions.rs`.
3. The child module is registered from `tests/suite/code_mode.rs` and reuses the parent response extraction, text-item, feature setup, and turn-preparation helpers.
4. Preparation is split from submission, so every process-creating `submit_turn` call in the five cases is inside `run_with_background_terminal_cleanup`.
5. Cleanup handles success, returned error, and panic while preserving the original panic.
6. The one-survivor case replaces fixed process sleeps with a bounded PID/filesystem handshake.
7. The yielded case directly asserts absence of `Background sessions still running:`.
8. The five behavioural contracts remain present: ordering, exited-session exclusion, truncation placement, yielded neutrality, and completing-cell attribution.
9. `pretty_assertions::assert_eq` is used in the child module.

## Remaining required supplement

### 1. Direct manager-query unit coverage

The external-review triage requested a network-independent unit test for `live_process_ids_created_by_cell`. The `cc01596` diff changes only the aggregate integration-test files, so no such test was added.

Add focused unit coverage proving:

- exact creator-cell matching;
- another creator cell is excluded;
- `creator_cell_id: None` is excluded;
- exited processes are excluded;
- returned IDs are numerically sorted.

This should use the existing unified-exec test fixtures and must not alter production code.

### 2. Existing aggregate-suite compatibility evidence

The receipt runs only the five new aggregate acceptance cases. It does not run the two existing tests identified by the external review as exposed to the optional terminal-summary race:

- `code_mode_can_run_multiple_yielded_sessions`;
- `code_mode_wait_can_terminate_and_continue`.

Run those tests repeatedly on both:

- candidate/test-polish head;
- exact upstream base `61a44880a85d2fd0d8770908dea5733495e571c8`;

using the same runner and target cache. Record repetition counts and exact outcomes. If a candidate-only header race appears, adjust only the affected expectations to accept the correct optional point-in-time session summary.

### 3. Repository-native test invocation

The receipt records direct `cargo test` commands. Repository guidance requires `just test`, whose recipe runs `cargo nextest run --no-fail-fast` with the repository profile and stack configuration.

Rerun the affected unit tests, the five aggregate acceptance cases, and the two compatibility tests through the repository-native `just test` route. No broad project or workspace run is requested.

A suitable nextest filter shape is:

```text
just test -p codex-core --test all -E 'test(/suite::code_mode::orphan_sessions::/)' --no-capture
```

Use the repository-supported equivalent if the local nextest version requires slightly different filter syntax, and record the exact successful command.

### 4. Large-output assertion remains over-specific

The revised large-output case still asserts `items.len() == 2`. The accepted external-review triage asked to avoid an exact content-item-count assertion when the actual contract is only that:

- the status header remains separate and contains the session warning; and
- emitted output remains represented non-emptily after truncation.

Replace the exact count check with a contract-level assertion that locates the status header and verifies a separate non-empty emitted-output representation without pinning the complete serialization shape.

## Validation after supplement

Run only:

- `just fmt`;
- `just fix -p codex-core` if files changed;
- the new manager-query unit test and the three existing affected unit tests via `just test`;
- the five aggregate acceptance cases via `just test`;
- the two identified existing compatibility tests repeatedly on candidate and base;
- `git status --short --untracked-files=all`;
- `git diff --check` against `3778e1fae6e7e3d885252282a7c5ce67e06730ff`.

Do not run a broad project or workspace suite unless the focused compatibility comparison exposes a persistent candidate-only failure.

## Gate classification

The following coordination items may be marked complete:

- Agent 2 test-only revision prepared;
- five revised acceptance cases passed through the aggregate binary once.

The following remain open:

- supplemental manager-query unit coverage;
- repository-native focused rerun;
- repeated candidate/base compatibility evidence;
- Agent 3 final approval;
- final clean-head consolidation.
