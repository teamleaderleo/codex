# Code-mode orphan fix: coordination status

Last updated: 2026-07-26

Investigation baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`

## Current phase

Patch 1 correctness and clean-candidate code review are complete.

The remaining work is:

1. classify the repository-native `codex-core` project-suite failures against a matched upstream-base run;
2. complete the final team sanity review;
3. complete the user's wording and presentation review;
4. approve publication sequencing;
5. publish and cross-link the upstream issue and pull request.

Do not publish the upstream issue or open the upstream pull request until the remaining gate items below are complete.

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

## Preserved investigation evidence

### Negative reproduction

- Branch: `research/code-mode-live-session-test`
- Commit: `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
- Result: `1 passed; 0 failed; 0 ignored`

### Corrected acceptance lineage

- Branch: `research/code-mode-live-session-acceptance`
- Head: `89ffd99b81e872e3a961767e67fb8ec410df7eae`
- Negative proof: `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
- Initial acceptance: `528171c72c06d8be3471752322b7755a1eac3ac8`
- Contract and two-cell isolation correction: `0ba57a73ea5895883a21aeb88e923d75a74ed38d`
- Truncation assertion correction: `89ffd99b81e872e3a961767e67fb8ec410df7eae`

Coverage includes two sorted IDs, one-survivor filtering, truncation placement, yielded neutrality, exact creator-cell isolation, and panic-safe cleanup.

### Reviewed investigation implementation

- Branch: `fix/code-mode-live-session-summary`
- Reviewed formatted head: `73e5b9fc28de0815975fad3c3d70a6a0b38399b1`
- Final review file: `notes/code-mode-orphan-fix/final-net-diff-review-73e5b9f.md`
- Final review commit: `8577cea6c925dde7453641b7587190285979a3ad`
- Verdict: pass

The investigation branches and Markdown remain provenance. They are not part of the upstream candidate.

## Clean candidate

Upstream base:

`61a44880a85d2fd0d8770908dea5733495e571c8`

Current `openai/codex` main matched this SHA at Agent 3 review time.

Branch:

`fix/code-mode-live-session-summary-clean`

Clean head:

`3778e1fae6e7e3d885252282a7c5ce67e06730ff`

Clean comparison:

`61a44880a85d2fd0d8770908dea5733495e571c8...3778e1fae6e7e3d885252282a7c5ce67e06730ff`

Agent 1 handoff:

- File: `notes/code-mode-orphan-fix/agent-1-clean-candidate-handoff.md`
- Commit: `0a6e63cb5e97db6cf076a9559f71697ea21bce70`

Machine-readable receipt:

- Branch: `automation/agent1-clean-candidate-results`
- `notes/code-mode-orphan-fix/agent-1-clean-candidate-validation.txt`
- `notes/code-mode-orphan-fix/agent-1-clean-candidate-statuses.txt`

Candidate shape:

- one coherent commit over current upstream main;
- exactly seven reviewed files;
- 660 insertions and 4 deletions;
- no research, coordination, audit, review, runtime-report, issue-draft, retrospective, or handoff Markdown;
- no upstream conflict adaptation required.

## Final clean-candidate review

Review file:

`notes/code-mode-orphan-fix/final-clean-candidate-review-3778e1f.md`

Review commit:

`0600d13b39780f359f83543cbfde308974f22634`

### Code, scope, and history verdict

**Pass.**

Agent 3 independently confirmed that all seven clean-candidate files have the exact same Git blob SHA as the corresponding files at `73e5b9fc28de0815975fad3c3d70a6a0b38399b1`.

Therefore the clean candidate preserves the exact previously reviewed implementation and acceptance-test contents. It introduces no semantic adaptation and no lifecycle-policy expansion.

No Patch 1 code change is requested.

### Validation verdict

**Qualified / incomplete.**

Recorded clean-candidate results:

- `just fmt`: passed; no changes;
- `just fix -p codex-core`: passed; no changes;
- six Patch 1-focused code-mode and unified-exec tests: passed;
- dedicated `code_mode_orphan_sessions`: 5 passed, 0 skipped;
- `git status --short`: clean;
- `git diff --check`: clean;
- complete workspace test: not run pending explicit human approval.

Repository-native project run:

- command: `just test -p codex-core`;
- 3,110 tests executed;
- 3,017 passed;
- 93 failed;
- 9 skipped;
- exit 100.

The handoff identifies missing helper binaries, sandbox aborts, and unrelated assertions among the failures. This is not evidence that Patch 1 failed, because all changed-area focused tests and the complete dedicated acceptance target passed. However, the same project command was not run against the exact upstream base in the same environment, so the full failure set is not yet proven baseline-equivalent.

Do not describe the `codex-core` project suite as green.

## Minimal next validation step

Run the same command on upstream base `61a44880a85d2fd0d8770908dea5733495e571c8` in the same runner configuration:

`just test -p codex-core`

Compare failed-test names, skip set, failure classes, helper/sandbox failures, aggregate counts, and any code-mode or unified-exec failures.

Decision rule:

- no new candidate failures relative to upstream base: classify the project result as baseline/environment-limited and close the validation item;
- new candidate failures: investigate only the differential set before publication.

A complete workspace run is not required for this differential classification and remains subject to explicit human approval.

## Agent states

### Agent 1

Clean-candidate construction is complete.

Next responsibility: preserve `fix/code-mode-live-session-summary-clean` unchanged unless a concrete differential validation failure requires action.

### Agent 2

Focused and acceptance validation work is complete.

Next responsibility: run or classify the matched upstream-base `just test -p codex-core` result and report the differential failure set. Do not broaden the claim to a complete workspace run.

### Agent 3

Clean-candidate code, scope, and history review is complete.

Next responsibility: review the matched baseline differential and participate in the final team sanity review.

### Agent 4

Issue and PR drafts remain unpublished.

Next responsibility: update the drafts with clean head `3778e1fae6e7e3d885252282a7c5ce67e06730ff`, upstream base `61a44880a85d2fd0d8770908dea5733495e571c8`, and the qualified project-suite result. Do not call the broad suite green.

## Patch 2 and Patch 3 clarification

Agent 1 confirmed Patch 2 and Patch 3 were planning labels for separate follow-up families, not approved implementation contracts.

- Patch 2 grouped ownership and cleanup-policy questions such as hidden/subagent completion while yielded work remains live.
- Patch 3 grouped macOS or runtime-loss orphan-recovery mechanisms such as durable process-group tracking, stale-process sweeps, guardians, or stronger termination reporting.

Each family still requires its own executable reproduction, ownership statement, policy decision, and issue. Do not infer additional patch commitments from the labels.

## Final reconvene agenda

Each lane should review the same clean candidate and final public drafts:

1. Is the clean candidate still exactly equivalent to the reviewed Patch 1 tree?
2. Does the matched project-suite differential introduce any candidate-only failure?
3. Is the change still visibility-only?
4. Are validation claims bounded accurately?
5. Is the one-commit history concise and reviewable?
6. Does the issue describe loss of model-visible control information rather than intended process persistence as the defect?
7. Does the PR explain typed ownership, behavioural boundaries, and acceptance coverage without overselling validation?
8. Is the public copy privacy-safe?
9. Are related-issue distinctions still current?
10. Is issue-first-then-PR still the preferred publication order?

## Publication preparation gate

Completed:

- [x] Negative reproduction preserved and passed.
- [x] Corrected acceptance suite integrated.
- [x] Exact creator-cell isolation covered.
- [x] Reviewed investigation tree passed final net-diff review.
- [x] Clean candidate exists on current upstream main.
- [x] Clean candidate contains one reviewable commit and no research history.
- [x] Repository-native format passed.
- [x] Repository-native scoped fix passed.
- [x] Dedicated acceptance target passed 5/5.
- [x] Final repository inspection is clean.
- [x] Clean candidate exact-file equivalence review passed.
- [x] Agent 4 issue and PR drafts prepared.
- [x] Related-issue refresh completed.
- [x] Public-copy privacy scrub completed.

Open:

- [ ] Matched upstream-base project-suite differential is recorded.
- [ ] Broad project-suite result is classified without overstating it.
- [ ] Final team sanity review completes.
- [ ] User wording and presentation review completes.
- [ ] Publication sequence is approved.
- [ ] Issue and PR links are filled after publication.

## Separate follow-ups

These must not expand Patch 1:

- delayed old-cell invocation crossing into a later turn worker;
- session shutdown racing with a dispatched nested exec that stores after the manager drain;
- remote exec-server bulk termination without confirmed completion;
- natural exit leaving process-manager bookkeeping until later refresh or removal;
- hidden-subagent lifecycle policy;
- macOS orphan recovery after abrupt runtime death.

The cross-turn dispatch path remains a high-confidence static finding only. It has not been reproduced. Do not call it a bug without executable evidence of wrong-turn execution or a bounded no-successor failure or hang condition.
