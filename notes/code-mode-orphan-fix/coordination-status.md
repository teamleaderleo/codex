# Code-mode orphan fix: coordination status

Last updated: 2026-07-26

Investigation baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`

## Current phase

Patch 1 production correctness, clean-history reconstruction, architecture/API review, and matched project-suite differential classification are complete.

The final roundtable found one pre-publication test-conventions issue: the five acceptance cases should be moved from a standalone integration target into the repository's aggregated code-mode suite, with cleanup and timing robustness tightened. Production code should remain unchanged.

Remaining work:

1. Agent 2 prepares and validates the test-only roundtable revision on a separate branch.
2. Agent 3 reviews that test-only diff and validation receipt.
3. Agent 1 performs a short contract sanity check against the revised tests.
4. Agent 4 updates the unpublished issue and pull-request drafts against the final clean head.
5. The user completes wording, process-feedback, and publication review.
6. The user approves issue/PR sequencing and publication.
7. Publish and cross-link only after the preceding gates are complete.

Do not publish the upstream issue or open the upstream pull request yet.

## Selected Patch 1 contract

1. Patch 1 is visibility-only. It must not terminate background sessions or change intended cross-turn or interrupt persistence.
2. The unified-exec process manager remains the source of truth for current liveness.
3. Preserve typed creator attribution from `ToolCallSource::CodeMode { cell_id, ... }` through unified exec and onto the stored live process entry.
4. Do not infer ownership from JavaScript output or call-ID text.
5. Keep the JavaScript-visible `session_id` schema compatible.
6. Surface surviving logical process IDs in the outer status header after emitted-output truncation.
7. Report the summary only for terminal cell outcomes: successful `Result`, failed `Result`, and explicit `Terminated`.
8. Keep ordinary `Yielded` responses completion-neutral.
9. Preserve opaque nested tool-call IDs.

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
- Contract and two-cell correction: `0ba57a73ea5895883a21aeb88e923d75a74ed38d`
- Truncation assertion correction: `89ffd99b81e872e3a961767e67fb8ec410df7eae`

Coverage includes two sorted surviving IDs, exited-process exclusion, truncation placement, yielded neutrality, exact creator-cell isolation, and cleanup.

### Reviewed investigation implementation

- Branch: `fix/code-mode-live-session-summary`
- Reviewed formatted head: `73e5b9fc28de0815975fad3c3d70a6a0b38399b1`
- Final review: `notes/code-mode-orphan-fix/final-net-diff-review-73e5b9f.md`
- Review commit: `8577cea6c925dde7453641b7587190285979a3ad`
- Verdict: pass

The investigation branches and Markdown are preserved as provenance and are not part of the upstream candidate.

## Current clean candidate

Upstream base:

`61a44880a85d2fd0d8770908dea5733495e571c8`

Branch:

`fix/code-mode-live-session-summary-clean`

Current clean head before roundtable test polish:

`3778e1fae6e7e3d885252282a7c5ce67e06730ff`

Comparison:

`61a44880a85d2fd0d8770908dea5733495e571c8...3778e1fae6e7e3d885252282a7c5ce67e06730ff`

Shape:

- one coherent commit over current upstream main;
- six production/internal-test files plus one standalone acceptance-test file;
- 660 insertions and 4 deletions;
- no research, coordination, audit, review, runtime-report, issue-draft, retrospective, or handoff Markdown;
- no upstream conflict adaptation.

Agent 1 handoff:

- `notes/code-mode-orphan-fix/agent-1-clean-candidate-handoff.md`
- commit `0a6e63cb5e97db6cf076a9559f71697ea21bce70`

Machine-readable receipt:

- branch `automation/agent1-clean-candidate-results`

## Production code review

Final clean-candidate review:

- file: `notes/code-mode-orphan-fix/final-clean-candidate-review-3778e1f.md`
- initial commit: `0600d13b39780f359f83543cbfde308974f22634`
- validation-closure update: `02bede7640df40661de2640156e7e51656b8ffdf`

Architecture/API review:

- file: `notes/code-mode-orphan-fix/agent-3-architecture-api-conventions-review.md`
- commit: `d73f6b99224589d9696d23ef8912f37b39f4921a`

Production verdict: **pass**.

Confirmed:

- typed creator-cell attribution reaches stored `ProcessEntry` metadata;
- manager state remains the sole liveness authority;
- lookup is exact-cell, live-only, read-only, and deterministically ordered;
- only terminal `Result` and `Terminated` disclose surviving sessions;
- ordinary `Yielded` remains neutral;
- the status survives output truncation;
- nested call IDs remain opaque;
- the JavaScript schema remains unchanged;
- no lifecycle or protocol expansion is present.

No production-code change is requested by the roundtable.

## Matched project-suite differential

Failure inventory:

- file: `notes/code-mode-orphan-fix/agent-1-clean-candidate-project-failure-inventory.md`
- commit: `a3cdd18d2cd8e60e5997c25dd41d55b1af2ec2db`

Command on both refs:

`just test -p codex-core`

Candidate result:

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
- all eight Patch 1-added tests passed on the current candidate.

Classification: **pass with baseline-red caveat**.

The broad project suite was not green on either ref. No persistent candidate-only failure remains, and nothing remains potentially related to Patch 1 or unclassified. Public copy must not claim that the complete project or workspace suite passed.

## Final roundtable

Directory:

`notes/code-mode-orphan-fix/final-roundtable/`

Integrated reviews:

- `agent-1-implementation-conventions.md` — pass with notes;
- `agent-2-testing-conventions.md` — change requested;
- `agent-4-publication-conventions.md` — pass with notes;
- Agent 3 architecture review remains at its existing path.

Synthesis:

- file: `notes/code-mode-orphan-fix/final-roundtable/synthesis.md`
- commit: `ecf6459c856a28b154d86ea9feca7336d478c99c`

Roundtable conclusion:

- production implementation passes;
- public framing passes with bounded wording corrections;
- one test-only revision is required before publication.

## Required test-only revision

Agent 2 should prepare a separate branch from clean head `3778e1fae6e7e3d885252282a7c5ce67e06730ff`.

Recommended branch:

`review/code-mode-roundtable-test-polish`

Required scope:

1. remove the standalone `codex-rs/core/tests/code_mode_orphan_sessions.rs` target;
2. move the five acceptance cases into a focused child module of the existing code-mode suite, preferably `codex-rs/core/tests/suite/code_mode/orphan_sessions.rs`, registered from `tests/suite/code_mode.rs`;
3. reuse existing code-mode helpers;
4. include turn submission and process-creating setup inside cleanup protection;
5. assert directly that the terminal-only warning is absent from yielded output;
6. replace fixed sleeps with bounded polling or a deterministic completion handshake;
7. preserve all five behavioural contracts;
8. make no production-code changes.

Focused validation only:

- `just fmt`;
- `just fix -p codex-core` if needed;
- three affected module unit tests;
- five revised acceptance cases through the aggregated `all` binary;
- `git status --short`;
- `git diff --check`.

No new broad or workspace run is requested unless the focused revision exposes a concrete differential failure.

## Agent states

### Agent 1

Clean-candidate implementation and failure inventory are complete.

Next: after Agent 2's test-only branch is reviewed, perform a brief sanity check that the revised tests still express the intended contract. Do not reopen production architecture broadly.

### Agent 2

Roundtable testing review found a concrete test-layout and robustness issue.

Next: prepare and validate the test-only polish branch described above. Do not modify production code or publish upstream.

### Agent 3

Production, differential, conventions, and roundtable synthesis reviews are complete.

Next: review Agent 2's test-only diff and focused validation receipt, then consolidate the final clean head.

### Agent 4

Publication review is complete, but drafts remain unpublished.

Next: wait for the final clean head after test polish, then update issue/PR drafts with final metadata and bounded validation wording. Do not call the broad suite green.

## Patch 2 and Patch 3

Patch 2 and Patch 3 are planning labels for separate follow-up families, not approved implementation contracts.

- Patch 2: ownership and cleanup-policy questions, including hidden/subagent completion with live yielded work.
- Patch 3: runtime-loss and macOS recovery mechanisms, including durable process-group tracking, stale-process sweeps, guardians, or stronger termination reporting.

Each future item requires its own executable reproduction, ownership statement, policy decision, issue, implementation review, and validation. Omit Patch 2 and Patch 3 from public Patch 1 copy.

## Publication gate

Completed:

- [x] Negative reproduction preserved and passed.
- [x] Corrected acceptance lineage preserved.
- [x] Production implementation reviewed.
- [x] Clean candidate reconstructed on current upstream main.
- [x] Repository-native format and scoped fix passed.
- [x] Focused production tests passed.
- [x] Current five acceptance cases passed.
- [x] Matched upstream-base differential recorded and classified.
- [x] Architecture/API conventions review passed.
- [x] Final roundtable reviews integrated and synthesized.
- [x] Agent 4 publication draft and privacy preparation completed.

Open:

- [ ] Agent 2 test-only revision is prepared.
- [ ] Revised acceptance cases pass through the aggregate suite.
- [ ] Agent 3 approves the test-only diff and receipt.
- [ ] Agent 1 confirms contract coverage remains intact.
- [ ] Final clean head and comparison are recorded.
- [ ] Agent 4 updates the public drafts against the final head.
- [ ] User wording and presentation review completes.
- [ ] Publication sequence is approved.
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
