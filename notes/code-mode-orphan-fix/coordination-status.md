# Code-mode orphan fix: coordination status

Last updated: 2026-07-26
Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`

## How to use this file

This is the canonical cross-agent execution board for the code-mode orphan investigation.

- Every agent should read this file before starting or resuming work.
- The integrator owns updates to this file so parallel agents do not conflict while editing it.
- Each agent should keep detailed work in its own report or implementation branch, then leave a compact handoff containing branch/ref, changed files, tests actually run, blockers, and decisions needed.
- Do not overwrite another agent's report.
- Do not publish the upstream issue or open an upstream PR until the publication preparation items below are complete.

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
- Environment: Linux aarch64 in Lima
- Result: `1 passed; 0 failed; 0 ignored`

The test confirms that two nested `exec_command` calls can yield, JavaScript can discard both copied `session_id` fields, the outer cell can report `Script completed`, and both manager-owned processes can remain alive without their IDs appearing in the outer result. Panic-safe teardown removed all test processes.

### Corrected acceptance lineage

- Branch: `research/code-mode-live-session-acceptance`
- Verified head: `89ffd99b81e872e3a961767e67fb8ec410df7eae`
- Negative proof: `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
- Initial acceptance: `528171c72c06d8be3471752322b7755a1eac3ac8`
- Contract/isolation correction: `0ba57a73ea5895883a21aeb88e923d75a74ed38d`
- Truncation assertion correction: `89ffd99b81e872e3a961767e67fb8ec410df7eae`

Coverage:

- both discarded surviving session IDs appear exactly once and in numeric order;
- one exited process is excluded while the survivor is reported;
- large emitted output cannot truncate or displace the separately prepended session summary;
- ordinary yielded cells remain completion-neutral;
- exact creator-cell isolation excludes Cell A's process from Cell B's summary;
- panic-safe teardown leaves no registered background terminals.

### Canonical integrated and formatted branch

- Branch: `fix/code-mode-live-session-summary`
- Integrated merge head: `4263facaf3c7d30b26cae33fd1e679278ac02105`
- Published formatted head: `73e5b9fc28de0815975fad3c3d70a6a0b38399b1`
- First merge parent: implementation `cea3f73d97897ca5ede37010cbd96addbabda6a5`
- Second merge parent: acceptance `89ffd99b81e872e3a961767e67fb8ec410df7eae`

The published head is exactly one commit ahead of the integrated merge head. The formatting commit changes only:

- `codex-rs/core/src/tools/code_mode/mod.rs`;
- `codex-rs/core/src/unified_exec/process_manager.rs`.

The complete patch is Rust formatter line wrapping. No semantic code, test, lifecycle, or protocol change was introduced.

### Canonical validation run

Detailed report: `notes/code-mode-orphan-fix/agent-2-test-runtime-report.md`

Dispatch commit: `ddaad65e0ad98c8bc3400937b11f53fb14dd52b9`

Platform: Linux aarch64 in Lima.

Formatting:

- full repository `just fmt` was unavailable because `just`, `dotslash`, and `uv` were absent;
- `cargo fmt --all` was run from `codex-rs` because Patch 1 changes Rust files only;
- only the two expected files changed;
- the published formatting commit matches those recorded changes.

Validation results on the Rust-formatted descendant now published as `73e5b9fc28de0815975fad3c3d70a6a0b38399b1`:

- `cargo check --manifest-path codex-rs/Cargo.toml -p codex-core --tests`: passed in 7m48s;
- focused code-mode library tests: `3 passed; 0 failed`;
- focused unified-exec library tests: `3 passed; 0 failed`;
- complete `code_mode_orphan_sessions` target: `5 passed; 0 failed; 0 ignored` in 17.12s;
- no skips, flakes, or retries on the correctly scoped commands;
- panic-safe acceptance cleanup remained active.

Infrastructure note:

- one incorrectly broad `cargo test -p codex-core <test-name>` fallback widened the build to unrelated integration binaries and linkers were killed with signal 9;
- this was a runner/resource and command-selection failure, not a Patch 1 compile failure or test assertion failure;
- the corrected explicit `--lib` selections all passed;
- full workspace validation is not claimed.

## Final net-diff review

Preliminary review:

- File: `notes/code-mode-orphan-fix/preliminary-net-diff-review-4263fac.md`
- Commit: `85e3324b2dd6fc78305a1bdd843dd1ec024a33f9`

Final review:

- File: `notes/code-mode-orphan-fix/final-net-diff-review-73e5b9f.md`
- Commit: `8577cea6c925dde7453641b7587190285979a3ad`
- Verdict: pass

Final baseline comparison:

- seven changed files;
- six production files plus one dedicated acceptance file;
- 664 changed lines, including the 521-line acceptance file;
- no shutdown, interrupt, dispatch-broker, recovery, code-mode runtime, process implementation, session-cleanup, subagent, macOS recovery, or public protocol file changed.

Confirmed:

- typed `ToolCallSource::CodeMode` attribution flows through `UnifiedExecContext` into stored `ProcessEntry`;
- manager lookup uses exact `CellId` equality, excludes exited processes, and sorts logical process IDs;
- manager lookup is read-only and does not change removal, pruning, persistence, or termination policy;
- only `Result` and `Terminated` query for live sessions;
- `Yielded` remains completion-neutral;
- emitted output is truncated before the status header is prepended;
- nested call IDs remain opaque UUID-based IDs;
- the JavaScript-visible result schema is unchanged;
- no lifecycle-policy expansion was found;
- the formatting descendant contains no semantic delta from the validated integrated tree.

Minor notes, not blockers:

- process IDs are sorted in the manager and again by the formatter;
- prototype/research ancestry remains and should be replaced by a clean candidate comparison before upstream publication;
- Unix/network-backed test limitations remain documented.

No further Patch 1 code change is requested by the final review.

## Current workstreams

### Agent 1: implementation and integration owner

State: implementation, integration, formatting publication, and branch validation are complete.

Published head:

- `fix/code-mode-live-session-summary`
- `73e5b9fc28de0815975fad3c3d70a6a0b38399b1`

Next actions:

1. Preserve the published head while publication materials are prepared.
2. Do not squash the research branch until a clean candidate comparison is intentionally prepared.
3. Help resolve only concrete discrepancies found during final publication preparation.
4. Do not open an upstream PR without the agreed publication sequence.

### Agent 2: regression, acceptance, and validation owner

State: Patch 1 work complete.

Preserve:

- negative proof `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`;
- acceptance head `89ffd99b81e872e3a961767e67fb8ec410df7eae`;
- validation dispatch `ddaad65e0ad98c8bc3400937b11f53fb14dd52b9`.

Next actions:

1. Avoid further branch changes unless a concrete test-contract defect is found.
2. Help classify any later failure as implementation, test, environment, or command-selection related.
3. Do not claim full workspace validation.

### Agent 3: final review owner

State: final Patch 1 net-diff sign-off complete.

Completed:

- ownership-boundary audit;
- typed creator-cell API recommendation;
- implementation and acceptance review;
- preliminary net-diff review;
- canonical validation review;
- published formatting comparison;
- final baseline net-diff sign-off.

Next actions:

1. Support the clean candidate or draft PR comparison review.
2. Reject any late change that expands lifecycle policy without a separate reproduction and decision.
3. Keep the cross-turn dispatch work separate from Patch 1.

### Agent 4: evidence and unpublished issue owner

State: publication preparation is now the critical path.

Next actions:

1. Record published head `73e5b9fc28de0815975fad3c3d70a6a0b38399b1`.
2. Record that its parent is integrated head `4263facaf3c7d30b26cae33fd1e679278ac02105` and its patch is formatting-only in the two expected files.
3. Record compile/check, focused `3 + 3` library tests, acceptance `5/5`, no skips/flakes, and the unrelated broad-command OOM incident.
4. Record final review file and commit `8577cea6c925dde7453641b7587190285979a3ad` with verdict pass.
5. Refresh related-issue status and recent maintainer discussion.
6. Fill all remaining final-SHA, validation, and review placeholders.
7. Preserve both publication variants: issue immediately before the PR, and issue linked alongside a draft PR.
8. Keep the issue and PR unpublished until the clean candidate comparison and publication sequence are approved.

## Publication preparation gate

Implementation and validation items are complete. Do not publish until the remaining preparation items are complete.

- [x] Baseline negative reproduction is preserved and passed.
- [x] Typed creator-cell implementation is prepared.
- [x] Corrected acceptance suite is integrated.
- [x] Exact creator-cell isolation is covered.
- [x] Rust formatting completed with only the two expected files changed.
- [x] Exact formatted tested commit is published on `fix/code-mode-live-session-summary`.
- [x] Published formatting diff is confirmed limited to the two expected Rust files.
- [x] Canonical formatted descendant passed compile/check.
- [x] Six focused library tests passed.
- [x] Complete five-test acceptance target passed with panic-safe teardown.
- [x] No skips or flakes were observed in the correctly scoped validation.
- [x] Final baseline net-diff review found no lifecycle-policy expansion.
- [ ] Clean candidate commit or draft PR comparison exists.
- [ ] Agent 4 fills all evidence placeholders.
- [ ] Related-issue status and recent maintainer discussion are refreshed.
- [ ] Issue/PR publication sequence is approved.

## Immediate execution order

1. Agent 4 updates the private report with final SHA, validation, and review evidence.
2. Agent 4 refreshes related issues and recent maintainer discussion.
3. Prepare a clean candidate commit or draft PR comparison from the reviewed net diff.
4. Agent 3 reviews that clean comparison against `73e5b9fc28de0815975fad3c3d70a6a0b38399b1`.
5. Choose and approve issue/PR ordering.
6. Publish only after the remaining gate items are complete.

## Separate candidate follow-ups

These must not expand Patch 1:

- delayed old-cell invocation crossing into a later turn worker;
- session shutdown racing with a dispatched nested exec that stores after the manager drain;
- remote exec-server bulk termination without confirmed completion in one path;
- natural exit leaving process-manager bookkeeping until later refresh/removal;
- hidden-subagent lifecycle policy;
- macOS orphan recovery after abrupt runtime death.

The cross-turn dispatch path remains a high-confidence static finding only. It has not been reproduced. Do not call it a bug without executable evidence of wrong-turn execution or a bounded no-successor failure/hang condition.

Each follow-up needs an independent reproduction, ownership statement, and issue decision.

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
