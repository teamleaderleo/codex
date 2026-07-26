# Code-mode orphan fix: coordination status

Last updated: 2026-07-26

Investigation baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`

## Current phase

Patch 1 production correctness, clean-history reconstruction, architecture/API review, test-conventions polish, focused validation, and matched project-suite differential classification are complete.

The final clean candidate is approved and consolidated. No upstream issue or pull request has been published.

Remaining work:

1. Agent 1 performs the short final contract sanity check against the aggregate tests.
2. Resolve and state the display-cardinality/global-history-limit position in final public copy.
3. Agent 4 updates the standalone issue and pull-request drafts against the final clean head.
4. The user completes wording, process-feedback, and publication review.
5. The user explicitly approves publication sequencing.
6. Publish the standalone issue, then the PR, and cross-link them in the same working session.

Do not publish upstream before the remaining gates close.

## Selected Patch 1 contract

1. Patch 1 is visibility-only. It must not terminate background sessions or change intended cross-turn or interrupt persistence.
2. The session-level unified-exec process manager remains the source of truth for current liveness.
3. Preserve creator attribution from `ToolCallSource::CodeMode { cell_id, ... }` through unified exec and onto the stored live process entry.
4. Do not infer ownership from JavaScript output or call-ID text.
5. Keep the JavaScript-visible `session_id` schema compatible.
6. Surface surviving logical session IDs in the outer status header after emitted-output truncation.
7. Report the summary only for terminal cell outcomes: successful `Result`, failed `Result`, and explicit `Terminated`.
8. Keep ordinary `Yielded` responses completion-neutral.
9. Preserve opaque nested tool-call IDs.

## Preserved evidence

### Negative reproduction

- Branch: `research/code-mode-live-session-test`
- Commit: `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
- Result: `1 passed; 0 failed; 0 ignored`

### Corrected acceptance lineage

- Branch: `research/code-mode-live-session-acceptance`
- Head: `89ffd99b81e872e3a961767e67fb8ec410df7eae`
- Negative proof: `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
- Initial acceptance: `528171c72c06d8be3471752322b7755a1eac3ac8`
- Contract and two-cell correction: `0ba57a73ea5895883a21aeb88e923d75a74ed38d`
- Truncation assertion correction: `89ffd99b81e872e3a961767e67fb8ec410df7eae`

Coverage includes sorted surviving IDs, exited-process exclusion, truncation placement, yielded neutrality, exact creator-cell isolation, and cleanup.

### Reviewed implementation lineage

- Investigation implementation branch: `fix/code-mode-live-session-summary`
- Reviewed formatted head: `73e5b9fc28de0815975fad3c3d70a6a0b38399b1`
- Final net-diff review: `notes/code-mode-orphan-fix/final-net-diff-review-73e5b9f.md`
- Review commit: `8577cea6c925dde7453641b7587190285979a3ad`

The investigation branches and research Markdown are provenance only and are not part of the upstream candidate.

## Final clean candidate

Upstream base:

`61a44880a85d2fd0d8770908dea5733495e571c8`

Canonical branch:

`fix/code-mode-live-session-summary-clean`

Final clean head:

`760216784efaee1ba6a3b1250349f31d5f91c7ca`

Comparison:

`61a44880a85d2fd0d8770908dea5733495e571c8...760216784efaee1ba6a3b1250349f31d5f91c7ca`

History shape:

- three commits over the selected upstream base;
- production implementation commit followed by two test-only polish commits;
- no research, coordination, audit, review, runtime-report, issue-draft, retrospective, or handoff Markdown in the candidate history;
- no production file changed by the two test-polish commits.

Changed paths relative to upstream base:

1. `codex-rs/core/src/tools/code_mode/mod.rs`
2. `codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs`
3. `codex-rs/core/src/unified_exec/mod.rs`
4. `codex-rs/core/src/unified_exec/mod_tests.rs`
5. `codex-rs/core/src/unified_exec/process_manager.rs`
6. `codex-rs/core/src/unified_exec/process_manager_tests.rs`
7. `codex-rs/core/tests/suite/code_mode.rs`
8. `codex-rs/core/tests/suite/code_mode/orphan_sessions.rs`

Final test-polish approval:

- file: `notes/code-mode-orphan-fix/agent-3-final-test-polish-approval-7602167.md`
- commit: `c7a71520adb8437eea997109e9e3097c08efc5d2`
- verdict: approved

## Production review

Final clean-candidate review:

- file: `notes/code-mode-orphan-fix/final-clean-candidate-review-3778e1f.md`
- initial commit: `0600d13b39780f359f83543cbfde308974f22634`
- validation-closure update: `02bede7640df40661de2640156e7e51656b8ffdf`

Architecture/API review:

- file: `notes/code-mode-orphan-fix/agent-3-architecture-api-conventions-review.md`
- commit: `d73f6b99224589d9696d23ef8912f37b39f4921a`

Production verdict: **pass**.

Confirmed:

- creator-cell attribution reaches stored `ProcessEntry` metadata;
- manager state remains the liveness authority;
- lookup is exact-cell, live-only, read-only, and numerically ordered;
- only terminal `Result` and `Terminated` disclose surviving sessions;
- ordinary `Yielded` remains neutral;
- the status is outside code-mode emitted-output truncation;
- nested call IDs remain opaque;
- the JavaScript schema remains unchanged;
- no lifecycle or protocol expansion is present.

## Test-polish and focused validation

Original test-polish head:

`cc01596b75abb38335ecdfe07688f155b0dd15a9`

Supplemental/final head:

`760216784efaee1ba6a3b1250349f31d5f91c7ca`

Receipts:

- `notes/code-mode-orphan-fix/agent-2-test-polish-validation-receipt.md`
- `notes/code-mode-orphan-fix/agent-2-test-polish-supplemental-validation-receipt.md`

Confirmed changes:

- standalone acceptance binary removed;
- five cases moved into the aggregate code-mode suite;
- parent helpers reused;
- process-creating submission covered by cleanup protection;
- fixed sleeps replaced by a bounded deterministic exit handshake;
- yielded neutrality checks the named completion-only warning directly;
- a network-independent manager-query unit test covers exact-cell matching, another-cell exclusion, `None` exclusion, exited-process exclusion, and numeric ordering;
- the large-output case checks the behavioural contract without pinning exact content-item cardinality.

Repository-native focused results:

- `just fmt`: passed;
- `just fix -p codex-core`: passed;
- four focused unit tests: 4 passed, 0 failed;
- five aggregate acceptance cases: 5 passed, 0 failed;
- exact upstream-base compatibility: 10 repetitions × 2 tests = 20 passed, 0 failed;
- final candidate compatibility: 10 repetitions × 2 tests = 20 passed, 0 failed;
- no candidate-only optional-header race observed;
- clean worktree;
- `git diff --check`: passed.

## Matched project-suite differential

Failure inventory:

- file: `notes/code-mode-orphan-fix/agent-1-clean-candidate-project-failure-inventory.md`
- commit: `a3cdd18d2cd8e60e5997c25dd41d55b1af2ec2db`

Command on both refs:

`just test -p codex-core`

Candidate result at the pre-polish clean implementation:

- 3,110 run;
- 3,015 passed, including one flaky pass;
- 94 failed;
- one timed out;
- nine skipped.

Exact upstream-base result:

- 3,102 run;
- 3,007 passed;
- 94 failed;
- one timed out;
- nine skipped.

Differential:

- 93 failure names and the timeout were shared;
- the candidate-only and upstream-only broad-run failures each passed three of three times on both refs in one shared focused runner/cache;
- all Patch 1-focused tests passed.

Classification: **pass with baseline-red caveat**.

The broad project suite was not green on either ref. No persistent candidate-only failure remains. The complete workspace suite was not run. Public copy must not claim that the broad project or workspace suite passed.

## Final roundtable and external review

Roundtable directory:

`notes/code-mode-orphan-fix/final-roundtable/`

Synthesis:

- file: `notes/code-mode-orphan-fix/final-roundtable/synthesis.md`
- commit: `ecf6459c856a28b154d86ea9feca7336d478c99c`

External review packet:

`notes/code-mode-orphan-fix/external-review/`

External-review triage:

`notes/code-mode-orphan-fix/external-review/triage-2026-07-26.md`

The standalone issue remains the canonical planned public problem statement. Related issue `openai/codex#34866` should be acknowledged as overlapping prior symptom coverage, not used as a substitute for this issue.

## Agent states

### Agent 1

Implementation and failure inventory are complete.

Next: perform only the short final contract sanity check against head `760216784efaee1ba6a3b1250349f31d5f91c7ca`, covering ordering, exited-session exclusion, truncation placement, yielded neutrality, and completing-cell attribution.

### Agent 2

Test-conventions revision, supplement, and focused validation are complete. Re-enter only for a concrete test defect.

### Agent 3

Production, differential, conventions, roundtable synthesis, external-review triage, and final test-polish review are complete. Final clean head is consolidated.

### Agent 4

Next: update the standalone issue and PR drafts against final head `760216784efaee1ba6a3b1250349f31d5f91c7ca`. Keep them unpublished until the remaining human gates close. Do not call the broad suite green.

## Patch 2 and Patch 3

Patch 2 and Patch 3 remain planning labels for separate follow-up families, not approved implementation contracts.

- Patch 2: ownership and cleanup-policy questions, including hidden/subagent completion with live yielded work.
- Patch 3: runtime-loss and macOS recovery mechanisms, including durable process-group tracking, stale-process sweeps, guardians, or stronger termination reporting.

Each future item requires its own executable reproduction, ownership statement, policy decision, issue, implementation review, and validation. Omit Patch 2 and Patch 3 from public Patch 1 copy.

## Publication gate

Completed:

- [x] Negative reproduction preserved and passed.
- [x] Corrected acceptance lineage preserved.
- [x] Production implementation reviewed.
- [x] Clean candidate reconstructed on selected upstream main.
- [x] Repository-native format and scoped fix passed.
- [x] Focused production tests passed.
- [x] Matched upstream-base differential recorded and classified.
- [x] Architecture/API conventions review passed.
- [x] Final roundtable reviews integrated and synthesized.
- [x] Test-only revision prepared.
- [x] Revised acceptance cases passed through the aggregate suite.
- [x] Supplemental manager-query and compatibility validation passed.
- [x] Agent 3 approved the final test-only diff and receipts.
- [x] Final clean head and comparison recorded.
- [x] Canonical clean branch moved to the final head.

Open:

- [ ] Agent 1 confirms final contract coverage remains intact.
- [ ] Display-cardinality/global-history-limit wording is finalized.
- [ ] Agent 4 updates the standalone issue and PR drafts against the final head.
- [ ] User wording and presentation review completes.
- [ ] Publication sequence is explicitly approved.
- [ ] Issue and PR links are filled after publication.

## Separate deferred follow-ups

These must not expand Patch 1:

- generic process-origin modelling;
- delayed old-cell invocation crossing into a later turn worker;
- shutdown racing with a dispatched nested exec that stores after manager drain;
- remote bulk termination without confirmed completion;
- natural exit leaving stale manager bookkeeping;
- hidden/subagent lifecycle policy;
- event-driven wake-up after process or subagent completion;
- macOS or runtime-loss orphan recovery;
- reusable background-terminal cleanup guards;
- reusable repository-native validation profiles.

The cross-turn dispatch path remains a high-confidence static finding only. It is not reproduced and must not be described publicly as a confirmed bug.
