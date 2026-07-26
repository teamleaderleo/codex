# Code-mode orphan fix: coordination status

Last updated: 2026-07-26
Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`

## How to use this file

This is the canonical cross-agent execution board for the code-mode orphan investigation.

- Every agent should read this file before starting or resuming work.
- The integrator owns updates to this file so parallel agents do not conflict while editing it.
- Each agent should keep detailed work in its own report or implementation branch, then leave a compact handoff containing branch/ref, changed files, tests actually run, blockers, and decisions needed.
- Do not overwrite another agent's report.
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

### Canonical validation run

Detailed report: `notes/code-mode-orphan-fix/agent-2-test-runtime-report.md`

Dispatch commit: `ddaad65e0ad98c8bc3400937b11f53fb14dd52b9`

Validated starting branch/head:

- Branch: `fix/code-mode-live-session-summary`
- Remote starting head: `4263facaf3c7d30b26cae33fd1e679278ac02105`
- First parent: implementation `cea3f73d97897ca5ede37010cbd96addbabda6a5`
- Second parent: acceptance `89ffd99b81e872e3a961767e67fb8ec410df7eae`
- Platform: Linux aarch64 in Lima

Formatting:

- Full repository `just fmt` was unavailable because `just`, `dotslash`, and `uv` were absent.
- `cargo fmt --all` was run from `codex-rs` because Patch 1 changes Rust files only.
- Rust formatting changed only:
  - `codex-rs/core/src/tools/code_mode/mod.rs`
  - `codex-rs/core/src/unified_exec/process_manager.rs`
- The changes were formatting-only.
- The local formatting-only commit SHA was not captured.
- The remote branch still resolves to unformatted merge head `4263facaf3c7d30b26cae33fd1e679278ac02105`.

Validation results on the local Rust-formatted descendant:

- `cargo check --manifest-path codex-rs/Cargo.toml -p codex-core --tests`: passed in 7m48s.
- Focused code-mode library tests: `3 passed; 0 failed`.
- Focused unified-exec library tests: `3 passed; 0 failed`.
- Complete `code_mode_orphan_sessions` target: `5 passed; 0 failed; 0 ignored` in 17.12s.
- No skips, flakes, or retries were observed for the correctly scoped commands.
- Panic-safe acceptance cleanup remained active.

Infrastructure note:

- One incorrectly broad `cargo test -p codex-core <test-name>` fallback widened the build to unrelated integration binaries and linkers were killed with signal 9.
- This was a runner/resource and command-selection failure, not a Patch 1 compile failure or test assertion failure.
- The corrected explicit `--lib` selections all passed.
- Full workspace validation is not claimed.

## Preliminary net-diff review

Review file: `notes/code-mode-orphan-fix/preliminary-net-diff-review-4263fac.md`

Review commit: `85e3324b2dd6fc78305a1bdd843dd1ec024a33f9`

Preliminary static verdict for `4263facaf3c7d30b26cae33fd1e679278ac02105` against the baseline: pass, with final sign-off reserved.

Confirmed:

- typed `ToolCallSource::CodeMode` attribution flows through `UnifiedExecContext` into stored `ProcessEntry`;
- manager lookup uses exact `CellId` equality, excludes exited processes, and sorts logical process IDs;
- manager lookup is read-only and does not change removal, pruning, persistence, or termination policy;
- only `Result` and `Terminated` query for live sessions;
- `Yielded` remains completion-neutral;
- emitted output is truncated before the status header is prepended;
- nested call IDs remain opaque UUID-based IDs;
- no shutdown, interrupt, dispatch, recovery, cell-runtime, or public protocol policy is changed.

Minor notes:

- process IDs are sorted in the manager and again by the formatter;
- prototype history remains and should not be squashed until the published formatted head is reviewed;
- Unix/network-backed test limitations remain documented.

Final sign-off is still reserved until the exact formatted tested tree is pushed and compared.

## Current workstreams

### Agent 1: publish the exact tested tree

Current remote branch/head:

- `fix/code-mode-live-session-summary`
- `4263facaf3c7d30b26cae33fd1e679278ac02105`

Next actions:

1. Recover the local formatting-only commit or recreate it with `cargo fmt --all` from `codex-rs` on `4263facaf3c7d30b26cae33fd1e679278ac02105`.
2. Confirm only the two expected Rust files change.
3. Push that exact formatting-only commit to `fix/code-mode-live-session-summary` and record the published SHA.
4. Run and record:
   - `git status --short`;
   - `git diff --check`;
   - `git log --oneline --decorate -8`;
   - baseline `git diff --stat`;
   - baseline `git diff --name-status`.
5. Do not squash yet.
6. Do not open an upstream PR yet.

### Agent 2: validation owner

State: Patch 1 regression, acceptance, and runtime-validation work is complete.

Preserve:

- negative proof `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`;
- acceptance head `89ffd99b81e872e3a961767e67fb8ec410df7eae`.

Next actions:

1. Avoid further branch changes unless the published formatted tree differs from the tested tree or a concrete test-contract defect is found.
2. Help classify any later failure as implementation, test, environment, or command-selection related.
3. Do not claim full workspace validation.

### Agent 3: final review owner

Completed:

- ownership-boundary audit;
- typed creator-cell API recommendation;
- implementation and acceptance review;
- preliminary net-diff review;
- confirmation of the canonical validation record.

Next actions:

1. Wait for Agent 1 to publish the exact formatting-only descendant.
2. Compare the published head against `4263facaf3c7d30b26cae33fd1e679278ac02105` and verify only the two expected formatting changes.
3. Re-run the net-diff inspection against the baseline.
4. Confirm attribution, liveness filtering, terminal-only placement, yielded neutrality, opaque IDs, and absence of lifecycle-policy expansion.
5. Give or withhold final sign-off based on the published tested tree.

### Agent 4: evidence and unpublished issue owner

Next actions:

1. Record dispatch commit `ddaad65e0ad98c8bc3400937b11f53fb14dd52b9` and the canonical validation results.
2. Record the formatting runbook deviation and the two expected formatting-only files.
3. Record compile/check, focused `3 + 3` library tests, acceptance `5/5`, no skips/flakes, and the unrelated broad-command OOM incident.
4. Keep the final formatted SHA and Agent 3 sign-off placeholders open.
5. Keep the issue and PR unpublished.
6. Refresh related-issue status and maintainer discussion only after Agent 1 publishes the final head and Agent 3 completes review.

## Publication gate

Do not publish the upstream issue or open the upstream PR until all items are complete.

- [x] Baseline negative reproduction is preserved and passed.
- [x] Typed creator-cell implementation is prepared.
- [x] Corrected acceptance suite is integrated.
- [x] Exact creator-cell isolation is covered.
- [x] Preliminary net-diff review found no lifecycle-policy expansion.
- [x] Rust formatting completed locally with only the two expected files changed.
- [x] Canonical local formatted descendant passed compile/check.
- [x] Six focused library tests passed.
- [x] Complete five-test acceptance target passed with panic-safe teardown.
- [x] No skips or flakes were observed in the correctly scoped validation.
- [ ] Exact formatted tested commit is published on `fix/code-mode-live-session-summary`.
- [ ] Published formatting diff is confirmed limited to the two expected Rust files.
- [ ] Final baseline net-diff review is completed on the published tested head.
- [ ] Clean candidate commit or draft PR comparison exists.
- [ ] Agent 4 fills all evidence placeholders and refreshes related research.

## Immediate execution order

1. Agent 1 publishes the exact formatting-only tested descendant and records inspection output.
2. Agent 3 performs final comparison and sign-off review.
3. Agent 4 fills the final SHA/review evidence and refreshes related issues.
4. Prepare a clean candidate comparison.
5. Decide issue/PR ordering only after the publication gate is otherwise complete.

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
