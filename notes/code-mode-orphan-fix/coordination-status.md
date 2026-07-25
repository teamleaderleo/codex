# Code-mode orphan fix: coordination status

Last updated: 2026-07-26
Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`

## How to use this file

This is the canonical cross-agent execution board for the code-mode orphan investigation.

- Every agent should read this file before starting or resuming work.
- The integrator owns updates to this file so parallel agents do not conflict while editing it.
- Each agent should keep detailed work in its own report or implementation branch, then leave a compact handoff containing branch/ref, changed files, tests actually run, blockers, and decisions needed.
- Do not overwrite another agent's report.
- Use a PR review when a PR exists. Otherwise record cross-branch reviews here.
- Do not publish the upstream issue or open an upstream PR until the publication gate below is met.

## Selected Patch 1 contract

1. Patch 1 is visibility-only. It must not terminate background sessions or change intended cross-turn or interrupt persistence.
2. The unified-exec process manager remains the source of truth for current liveness.
3. Preserve typed creator attribution from `ToolCallSource::CodeMode { cell_id, ... }` through unified exec and onto the stored live process entry.
4. Do not infer ownership from JavaScript output or call-ID text.
5. Keep the JavaScript-visible `session_id` schema compatible.
6. Surface surviving logical process IDs in the outer status header after emitted-output truncation.
7. Report the summary only for terminal cell outcomes: successful `Result`, failed `Result`, and explicit `Terminated`.
8. Keep ordinary `Yielded` responses completion-neutral.
9. Preserve opaque nested tool call IDs.

## Evidence already verified

### Baseline negative reproduction

- Branch: `research/code-mode-live-session-test`
- Commit: `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
- Test: `code_mode_completion_does_not_surface_discarded_live_exec_sessions`
- Environment: Linux aarch64 in a local Lima VM hosted on macOS
- Result: `1 passed; 0 failed; 0 ignored`

The test confirms that two nested `exec_command` calls can yield, JavaScript can discard both copied `session_id` fields, the outer cell can report `Script completed`, and both manager-owned processes can remain alive without their IDs appearing in the outer result. Panic-safe teardown removed all test processes.

Exact command:

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

Keep machine-specific log paths private.

## Current workstreams

### Agent 1: typed-attribution implementation and integration owner

Branch: `fix/code-mode-live-session-summary`

Reviewed head: `cea3f73d97897ca5ede37010cbd96addbabda6a5`

Current state:

- `ExecCommandHandler` converts `ToolCallSource::CodeMode` into optional typed `CellId` attribution on `UnifiedExecContext`.
- `store_process` copies that attribution onto each stored `ProcessEntry`.
- `UnifiedExecProcessManager::live_process_ids_created_by_cell` uses exact typed matching, excludes exited processes, and returns sorted IDs.
- Outer code-mode reporting queries that method only for `Result` and `Terminated`.
- Nested call IDs are opaque again.
- Existing JavaScript results and persistence policy are unchanged.
- Formatter-level unit tests cover success, failure, termination, sorting, and yielded exclusion.
- This head has not yet been formatted, compiled, or tested.

Agent 1 next actions:

1. Wait for Agent 2's corrected acceptance-test head or coordinate before editing the same test file.
2. Integrate the preserved negative reproduction and corrected positive acceptance suite onto the implementation branch.
3. Add focused exact-cell isolation coverage at the manager level if the integration suite does not cleanly create two distinct cells. The test must prove that Cell A's process is not returned for Cell B.
4. Run `cargo fmt` or the repository formatting command and inspect the net diff.
5. Run a compile check before the full integration test.
6. Run the code-mode formatter/unit tests and the relevant unified-exec tests.
7. Run the complete `code_mode_orphan_sessions` acceptance file with the VM environment settings above.
8. Record exact commands, results, platform skips, and any flakes.
9. Do not squash prototype history until the combined branch is green and reviewed.
10. Once green, provide a clean net comparison or squashed candidate commit for final review.

### Agent 2: regression and acceptance-test owner

Negative branch: `research/code-mode-live-session-test`

Negative commit: `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`

Acceptance branch: `research/code-mode-live-session-acceptance`

Acceptance commit: `528171c72c06d8be3471752322b7755a1eac3ac8`

Handoff-note commit: `1ae28a191a7885438abf15f61de273ab37551768`

Current acceptance coverage:

- two discarded live session IDs must appear once each and in numeric order;
- one process exits before completion, so only the survivor is reported;
- a large emitted payload cannot truncate or displace the header warning;
- an ordinary yielded cell does not receive a completion-oriented warning;
- all cases retain panic-safe process cleanup.

Known test defect:

The main positive test currently expects the header to start with:

```text
Script completed
Wall time ...
```

The selected output contract inserts the live-session line between those lines:

```text
Script completed
Background sessions still running: ...
Wall time ...
```

Agent 2 next actions:

1. Fix the main positive assertion so it requires `Script completed\n`, independently checks the exact session IDs and their order, and separately verifies that `\nWall time ` remains present after the session line.
2. Keep the warning-prose assertion tolerant: assert the actual IDs and order rather than hard-coding the entire message.
3. Re-check the one-survivor test timing against the minimum unified-exec yield clamp; make the test deterministic rather than depending on a `10 ms` request being honoured literally.
4. Add a two-cell creator-isolation integration case if the existing harness can do so without large new machinery. Otherwise document that Agent 1 must add the manager-level exact-cell unit test.
5. Preserve the negative reproduction commit unchanged.
6. Push the corrected acceptance head and leave a compact handoff with the new SHA and the precise integration order.
7. Do not claim the positive suite passes until it has run against Agent 1's implementation.

Expected integration ancestry must include both the negative reproduction and positive acceptance changes. Do not cherry-pick only the positive diff without ensuring its parent test file exists.

### Agent 3 / integrator review: ownership audit and follow-up research

Completed Patch 1 work:

- confirmed the callback-task versus manager-owned process boundary;
- identified typed creator-cell attribution as the smallest reliable ownership API;
- reviewed Agent 1's net implementation and Agent 2's acceptance suite;
- identified the incorrect positive header assertion before execution;
- kept lifecycle-policy changes out of Patch 1.

Current parallel research:

- File: `notes/code-mode-orphan-fix/follow-up-cross-turn-dispatch-audit.md`
- Topic: whether a delayed nested invocation from an old cell can be consumed by a later turn worker through the shared dispatch receiver.
- Status: plausible static finding, not yet reproduced.

Agent 3 next actions:

1. Refine a deterministic two-turn regression that distinguishes the originating turn's runtime from a successor turn's runtime.
2. Confirm whether cancellation and cell-gate closure fully prevent the suspected crossover before calling it a bug.
3. Keep this work read-only and separate from Patch 1 unless a minimal test-only branch becomes useful.
4. Review Agent 2's corrected acceptance head.
5. Review Agent 1's combined, formatted, tested net diff.
6. Check that no unrelated shutdown, cleanup, dispatch, or recovery policy slips into Patch 1.
7. Update this execution board when verified results or heads change.

### Agent 4: history, evidence, and unpublished issue owner

Research file: `notes/code-mode-orphan-fix/agent-4-history-issue-report.md`

Current state:

- The report correctly describes intended persistence, the ownership boundary, the verified negative reproduction, typed attribution, non-goals, and the publication gate.
- It remains private; no issue, PR, or comment has been published.
- It still contains evidence placeholders and some language that predates Agent 1's completed untested implementation head.

Agent 4 next actions:

1. Replace the baseline-command placeholder with the verified command recorded above.
2. Record Agent 1's current typed-attribution head `cea3f73d97897ca5ede37010cbd96addbabda6a5` as implementation prepared but not yet tested.
3. Record Agent 2's acceptance branch and commits as prepared but not yet run against the implementation.
4. Keep final implementation, positive test command, and positive result placeholders until the combined branch passes.
5. Keep the issue unpublished.
6. Re-check related issue status and recent maintainer discussion only after the positive suite passes, so the final review is current.
7. Prepare two publication variants: issue immediately before the PR, and issue linked alongside a draft PR. Do not choose or publish yet.
8. Remove scratch-branch wording only after stable tested commits or a clean PR comparison exist.

## Publication gate

Do not publish the upstream issue or open the upstream PR until all of the following are true:

- [x] Baseline negative reproduction is preserved at a clean commit.
- [x] Baseline negative reproduction has passed in the local VM.
- [x] Typed creator-cell implementation is prepared.
- [x] Positive acceptance suite is prepared.
- [ ] Incorrect completion-header assertion is fixed.
- [ ] Exact creator-cell isolation is covered.
- [ ] Formatting completes with an inspected diff.
- [ ] Implementation compiles.
- [ ] Relevant code-mode and unified-exec unit tests pass.
- [ ] Full positive acceptance file passes with panic-safe teardown.
- [ ] One-survivor and truncation cases pass deterministically.
- [ ] Yielded-cell behaviour remains completion-neutral.
- [ ] Clean tested implementation commit or PR comparison exists.
- [ ] Agent 4 fills all evidence placeholders and refreshes related-issue research.
- [ ] Final net-diff review finds no lifecycle-policy expansion.

## Immediate execution order

1. Agent 2 fixes the acceptance branch and publishes a new head.
2. Agent 1 integrates the negative and corrected positive test lineage.
3. Agent 1 adds exact-cell manager coverage if Agent 2 does not add a two-cell integration case.
4. Agent 1 formats, compiles, and runs focused unit and integration tests.
5. Agent 3 reviews the combined results and clean net diff.
6. Agent 4 fills tested evidence, refreshes related issues, and performs the final publication edit.
7. Decide issue/PR ordering only after the publication gate is otherwise complete.

## Separate candidate follow-ups

These must not expand Patch 1:

- delayed old-cell invocation crossing into a later turn worker;
- session shutdown racing with a dispatched nested exec that stores after the manager drain;
- remote exec-server bulk termination without confirmed completion in one path;
- natural exit leaving process-manager bookkeeping until later refresh/removal;
- hidden-subagent lifecycle policy;
- macOS orphan recovery after abrupt runtime death.

Each needs an independent reproduction, ownership statement, and issue decision.

## Compact handoff template

```text
Agent:
Branch/ref:
Baseline:
Changed files:
Tests run and results:
Confirmed findings:
Open risks:
Decision requested:
Recommended next action:
```
