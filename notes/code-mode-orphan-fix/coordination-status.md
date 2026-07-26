# Code-mode orphan fix: coordination status

Last updated: 2026-07-26
Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`

## How to use this file

This is the canonical cross-agent execution board for the code-mode orphan investigation.

- Every agent should read this file before starting or resuming work.
- The integrator owns updates to this file so parallel agents do not conflict while editing it.
- Each agent should keep detailed work in its own report file or implementation branch, then leave a compact handoff containing branch/ref, changed files, tests actually run, blockers, and decisions needed.
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

## Verified evidence

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

### Positive integration run

Agent 2 applied the corrected acceptance lineage to Agent 1's typed-attribution implementation and ran the complete focused integration file.

- Implementation tested: `cea3f73d97897ca5ede37010cbd96addbabda6a5`
- Acceptance branch verified head: `89ffd99b81e872e3a961767e67fb8ec410df7eae`
- Ordered test commits:
  1. `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
  2. `528171c72c06d8be3471752322b7755a1eac3ac8`
  3. `0ba57a73ea5895883a21aeb88e923d75a74ed38d`
  4. `89ffd99b81e872e3a961767e67fb8ec410df7eae`
- Environment: Linux aarch64 under Lima
- Result: `5 passed; 0 failed; 0 ignored`
- Harness-reported execution time: `16.37s`
- Agent 2 report update: `8739905480cc02753e8e7e57dcc4f5170335480e`

Exact successful command:

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

Verified cases:

- both discarded surviving session IDs appear exactly once and in numeric order;
- one exited process is excluded while the survivor is reported;
- large emitted output cannot truncate or displace the separately prepended session summary;
- ordinary yielded cells remain completion-neutral;
- exact creator-cell isolation excludes Cell A's process from Cell B's summary;
- panic-safe teardown leaves no registered background terminals.

The first integrated run reached `4 passed; 1 failed` because the large-output test over-specified the retained text excerpt. Commit `89ffd99b81e872e3a961767e67fb8ec410df7eae` corrected only that test assertion; the complete file then passed.

Keep machine-specific log paths private.

## Current workstreams

### Agent 1: typed-attribution implementation and integration owner

Branch: `fix/code-mode-live-session-summary`

Current integrated head: `4263facaf3c7d30b26cae33fd1e679278ac02105`

Integration details:

- First parent: reviewed implementation head `cea3f73d97897ca5ede37010cbd96addbabda6a5`.
- Second parent: verified acceptance head `89ffd99b81e872e3a961767e67fb8ec410df7eae`.
- The merge tree adds `codex-rs/core/tests/code_mode_orphan_sessions.rs` to the implementation tree.
- Agent 2's documentation-only handoff file is intentionally omitted from the production branch.
- The original negative reproduction and corrected positive acceptance lineage are now preserved in branch ancestry.
- The two-cell integration case supplies exact creator-cell isolation coverage, so no duplicate manager-level test was added.

Current code state:

- `ExecCommandHandler` converts `ToolCallSource::CodeMode` into optional typed `CellId` attribution on `UnifiedExecContext`.
- `store_process` copies that attribution onto each stored `ProcessEntry`.
- `UnifiedExecProcessManager::live_process_ids_created_by_cell` uses exact typed matching, excludes exited processes, and returns sorted IDs.
- Outer code-mode reporting queries that method only for `Result` and `Terminated`.
- Nested call IDs are opaque.
- Existing JavaScript results and persistence policy are unchanged.
- Formatter-level unit tests cover success, failure, termination, sorting, and yielded exclusion.
- The combined production-and-test state matches the state Agent 2 exercised successfully.

Validation still pending on the canonical integrated branch:

1. Run the repository formatting command and inspect the net diff.
2. Compile or run a focused no-run test build before the repeated integration run.
3. Run relevant code-mode and unified-exec unit tests.
4. Repeat the complete `code_mode_orphan_sessions` file from `4263facaf3c7d30b26cae33fd1e679278ac02105` using the verified VM settings.
5. Record exact commands, results, platform skips, and flakes.
6. Review the net diff from the baseline for unintended lifecycle-policy changes.
7. Do not squash prototype history until this integrated branch is green and reviewed.
8. Do not open an upstream PR yet.

Static net comparison from the baseline currently contains seven changed files and 663 changed lines, below the repository's 800-line change-size guidance. No GitHub Actions run was attached automatically to the merge head.

### Agent 2: regression and acceptance-test owner

Negative branch: `research/code-mode-live-session-test`

Negative commit: `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`

Acceptance branch: `research/code-mode-live-session-acceptance`

Verified acceptance head: `89ffd99b81e872e3a961767e67fb8ec410df7eae`

Report update: `8739905480cc02753e8e7e57dcc4f5170335480e`

State: acceptance work complete for Patch 1.

- The negative reproduction remains unchanged as clean baseline evidence.
- The header assertion allows the session-summary line before wall time.
- One-survivor timing respects the unified-exec yield floor.
- A two-cell integration test proves exact creator-cell isolation.
- The large-output test checks the intended contract without over-specifying truncator output.
- The complete five-test file passed against Agent 1's implementation.

Agent 2 next actions:

1. Avoid further changes unless the canonical integrated run exposes a genuine test defect.
2. Preserve the verified branch head and ordered ancestry.
3. Help interpret any clean-branch failure, distinguishing implementation, test, and environment causes.
4. Do not claim full `codex-core` or workspace validation; only the focused file has been verified.

### Agent 3: ownership audit and review

Completed Patch 1 work:

- confirmed the callback-task versus manager-owned process boundary;
- identified typed creator-cell attribution as the smallest reliable ownership API;
- reviewed Agent 1's implementation and Agent 2's acceptance suite;
- identified the original header assertion mismatch before execution;
- confirmed the corrected acceptance branch and five-test result;
- kept lifecycle-policy changes out of Patch 1.

Current parallel research:

- Audit: `notes/code-mode-orphan-fix/follow-up-cross-turn-dispatch-audit.md`
- Test assignment: `notes/code-mode-orphan-fix/follow-up-cross-turn-dispatch-test-assignment.md`
- Assignment commit: `477a911ee39f2110b6e3bd512fc43e3accdd6e9c`
- Topic: whether a delayed nested invocation from an old yielded cell can be consumed by a later turn worker through the shared dispatch receiver.
- Status: high-confidence static crossover path; not yet reproduced.

Agent 3 next actions:

1. Review integrated head `4263facaf3c7d30b26cae33fd1e679278ac02105` and the eventual repeated validation results.
2. Check the final net diff for attribution correctness, liveness filtering, output placement, and lifecycle-policy expansion.
3. Keep the cross-turn dispatch test separate from Patch 1.
4. Do not call the follow-up a reproduced bug until a test observes wrong-turn execution or indefinite no-successor wait.

### Agent 4: history, evidence, and unpublished issue owner

Research file: `notes/code-mode-orphan-fix/agent-4-history-issue-report.md`

Current state:

- The report correctly describes intended persistence, the ownership boundary, the verified negative reproduction, typed attribution, non-goals, and the publication gate.
- It remains private; no issue, PR, or comment has been published.
- A canonical combined implementation branch now exists, but formatting, focused unit validation, repeated acceptance validation, and final net review remain pending.

Agent 4 next actions:

1. Record integrated head `4263facaf3c7d30b26cae33fd1e679278ac02105` and its two-parent ancestry.
2. Record Agent 2's exact command and `5 passed; 0 failed; 0 ignored` result as verified on the equivalent combined state.
3. Keep formatting, focused-unit, repeated canonical-branch validation, and final review placeholders open.
4. Keep the issue unpublished.
5. Refresh related issue status and recent maintainer discussion after Agent 1 supplies the green reviewed head.
6. Preserve both publication variants: issue immediately before the PR, and issue linked alongside a draft PR.

## Publication gate

Do not publish the upstream issue or open the upstream PR until all of the following are true:

- [x] Baseline negative reproduction is preserved at a clean commit.
- [x] Baseline negative reproduction has passed in the local VM.
- [x] Typed creator-cell implementation is prepared.
- [x] Positive acceptance suite is prepared.
- [x] Incorrect completion-header assertion is fixed.
- [x] Exact creator-cell isolation is covered.
- [x] Corrected tests are integrated onto Agent 1's branch.
- [x] Equivalent combined implementation and acceptance state compiles.
- [x] Full positive acceptance file passes with panic-safe teardown on the equivalent combined state.
- [x] One-survivor and truncation cases pass deterministically.
- [x] Yielded-cell behaviour remains completion-neutral.
- [ ] Formatting completes with an inspected diff on the canonical branch.
- [ ] Relevant code-mode and unified-exec unit tests pass on the canonical branch.
- [ ] Full positive acceptance file is repeated from the canonical integrated branch.
- [ ] Clean tested implementation commit or PR comparison exists.
- [ ] Agent 4 fills all evidence placeholders and refreshes related-issue research.
- [ ] Final net-diff review finds no lifecycle-policy expansion.

## Immediate execution order

1. Agent 1 formats the canonical integrated branch and inspects the resulting diff.
2. Agent 1 compiles, runs focused unit tests, and repeats the five-test acceptance file.
3. Agent 3 reviews the clean net diff and validation record.
4. Agent 4 fills the remaining evidence placeholders and refreshes related issues.
5. Prepare a clean candidate commit or draft PR comparison.
6. Decide issue/PR ordering only after the publication gate is otherwise complete.

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
