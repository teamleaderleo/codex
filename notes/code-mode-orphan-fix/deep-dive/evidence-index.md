# Patch 1 evidence index

Status: internal index for publication review. Inclusion here does not mean that an artifact should be linked publicly.

Last reviewed: 2026-07-26.

## How to read this index

Evidence is classified by strength and disclosure status:

- **Executable:** produced by a test, comparison, repository inspection, or command whose result was preserved.
- **Code-grounded:** directly inspectable in a commit-pinned source or test file.
- **Independent static review:** review performed without executing the candidate.
- **Human decision:** product, scope, severity, privacy, or publication choice; not established by tests alone.
- **AI-generated analysis:** useful working material that must be checked against code or executable evidence before being treated as fact.

Disclosure labels:

- **Public-safe:** suitable for a maintainer-facing issue/PR after final human review.
- **Appendix-safe:** potentially public as optional depth, but not necessary in the issue/PR.
- **Internal-public-fork:** stored in a publicly accessible fork but intended as working material, not endorsed public copy.
- **Private-by-default:** raw chats, logs, machine-specific paths, tokens, user data, or unsanitised artifacts; disclose only by explicit human decision.

## Canonical code state

| Item | Reference | Strength | Disclosure |
|---|---|---|---|
| Upstream base | [`61a44880a85d2fd0d8770908dea5733495e571c8`](https://github.com/openai/codex/commit/61a44880a85d2fd0d8770908dea5733495e571c8) | Code-grounded | Public-safe |
| Final clean candidate | [`760216784efaee1ba6a3b1250349f31d5f91c7ca`](https://github.com/teamleaderleo/codex/commit/760216784efaee1ba6a3b1250349f31d5f91c7ca) | Code-grounded | Public-safe |
| Final comparison | [`61a44880...7602167`](https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...760216784efaee1ba6a3b1250349f31d5f91c7ca) | Code-grounded | Public-safe |
| Canonical branch | [`fix/code-mode-live-session-summary-clean`](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-summary-clean) | Code-grounded | Public-safe |
| Final readiness verdict | [`final-publication-readiness-2026-07-26.md`](../final-publication-readiness-2026-07-26.md) | Human/review synthesis | Appendix-safe |

Final candidate shape:

- three commits above the selected upstream base;
- production implementation followed by two test-only polish commits;
- eight changed paths;
- no research, coordination, review, or chat artifacts in the candidate history.

## Current unpublished public-copy drafts

| Draft | Reference | Status |
|---|---|---|
| Standalone issue | [`publication-drafts/standalone-issue.md`](../publication-drafts/standalone-issue.md) | Unpublished; do not overwrite from the deep-dive branch |
| Pull request | [`publication-drafts/pull-request.md`](../publication-drafts/pull-request.md) | Unpublished; insert the actual issue number only after issue creation |
| Layered publication proposal and copy audit | [`deep-dive/agent-4-publication-architecture.md`](agent-4-publication-architecture.md) | Internal recommendation |
| Methodology and provenance | [`deep-dive/methodology-and-provenance.md`](methodology-and-provenance.md) | Internal by default |

## Production code: commit-pinned map

### 1. Creator-cell attribution at nested exec dispatch

[`exec_command.rs` lines 132–138](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L132-L138)

What it proves:

- existing `ToolCallSource::CodeMode { cell_id, .. }` metadata is converted into typed `CellId` creator metadata;
- direct calls remain unattributed;
- the metadata is attached to `UnifiedExecContext` before process creation.

Strength: code-grounded. Disclosure: public-safe.

### 2. Invocation-scoped carrier and stored entry field

[`unified_exec/mod.rs` lines 76–99](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L76-L99)

What it proves:

- `UnifiedExecContext` carries `Option<CellId>`;
- the default remains `None`;
- attribution is crate-private and invocation-scoped.

[`unified_exec/mod.rs` lines 189–199](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L189-L199)

What it proves:

- stored live process entries retain the optional creator cell alongside the process and logical ID.

Strength: code-grounded. Disclosure: public-safe.

### 3. Exact-cell, live-only manager query

[`unified_exec/mod.rs` lines 168–180](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L168-L180)

What it proves:

- the existing session-level manager remains the liveness authority;
- the query uses exact `CellId` equality;
- exited processes are excluded;
- logical IDs are sorted deterministically;
- the query is read-only.

Strength: code-grounded. Disclosure: public-safe.

### 4. Terminal-only lookup, truncation ordering, and status rendering

[`code_mode/mod.rs` lines 199–255](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/code_mode/mod.rs#L199-L255)

What it proves:

- only terminal `Result` and `Terminated` responses supply a cell ID to the manager query;
- ordinary `Yielded` responses do not query for completion-only disclosure;
- emitted output is truncated before the status header is prepended.

[`code_mode/mod.rs` lines 268–300](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/code_mode/mod.rs#L268-L300)

What it proves:

- successful, failed, and terminated terminal results retain their existing first-line status;
- the warning is added only when matching live session IDs exist;
- IDs are rendered in numeric order;
- the warning text is `Background sessions still running:`.

Strength: code-grounded. Disclosure: public-safe.

## Executable reproduction and acceptance coverage

### Negative reproduction lineage

| Item | Reference | Notes | Disclosure |
|---|---|---|---|
| Baseline negative proof | [`7298dcf44f61164ffc25b8bdf5f136281caeb9f5`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5) | Demonstrated that copied session IDs could be projected away while manager-owned sessions remained live | Appendix-safe |
| Corrected acceptance head | [`89ffd99b81e872e3a961767e67fb8ec410df7eae`](https://github.com/teamleaderleo/codex/commit/89ffd99b81e872e3a961767e67fb8ec410df7eae) | Preserved negative lineage and corrected two-cell/truncation assertions | Appendix-safe |
| Final aggregate acceptance module | [`orphan_sessions.rs`](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs) | Final repository-conformant form | Public-safe |

### Five aggregate acceptance cases

1. Multiple discarded live session IDs in deterministic order: [`orphan_sessions.rs` lines 159–205](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs#L159-L205).
2. Exited-session exclusion with one survivor: [`lines 207–282`](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs#L207-L282).
3. Warning remains outside code-mode emitted-output truncation: [`lines 284–352`](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs#L284-L352).
4. Ordinary yielded response omits the terminal-only warning: [`lines 354–396`](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs#L354-L396).
5. Only sessions created by the completing cell are reported: [`lines 397–504`](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs#L397-L504).

The cleanup helper is structural test-harness evidence, not five separate cleanup-path tests: [`orphan_sessions.rs` lines 106–157](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs#L106-L157).

### Direct manager-query coverage

[`unified_exec/mod_tests.rs` lines 332–395](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod_tests.rs#L332-L395)

Covers in one network-independent unit test:

- exact creator-cell match;
- another-cell exclusion;
- `creator_cell_id: None` exclusion;
- exited-entry exclusion;
- deterministic numeric ordering.

Strength: executable and code-grounded. Disclosure: public-safe.

## Repository test conventions

| Convention | Reference | Effect on final candidate |
|---|---|---|
| One aggregate integration-test binary | [`codex-rs/core/tests/all.rs` lines 1–9](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/all.rs#L1-L9) | The initial standalone integration target was removed |
| Existing code-mode suite and shared helpers | [`tests/suite/code_mode.rs` lines 59–77](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode.rs#L59-L77) | Acceptance cases became a child module and reused parent helpers/assertion conventions |
| Final child module | [`tests/suite/code_mode/orphan_sessions.rs`](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs) | Keeps the large parent file manageable while using the aggregate binary |

Strength: code-grounded. Disclosure: public-safe in the PR; unnecessary in the issue.

## Focused validation receipts

### Test-polish receipt

[`agent-2-test-polish-validation-receipt.md`](../agent-2-test-polish-validation-receipt.md)

Established:

- standalone integration target removed;
- parent helpers reused;
- process-creating submission moved inside cleanup protection;
- fixed sleeps replaced with bounded deterministic exit handling;
- yielded neutrality assertion changed to check the named warning directly;
- three affected units and five aggregate cases passed at the intermediate test-polish head.

Strength: executable receipt plus code diff. Disclosure: appendix-safe. Launcher troubleshooting and user-local setup notes should not appear in the public PR.

### Supplemental validation receipt

[`agent-2-test-polish-supplemental-validation-receipt.md`](../agent-2-test-polish-supplemental-validation-receipt.md)

Final reported results:

- `just fmt`: passed;
- `just fix -p codex-core`: passed;
- four focused unit tests: 4 passed, 0 failed;
- five aggregate acceptance cases: 5 passed, 0 failed;
- candidate compatibility: 10 repetitions × 2 tests = 20 passed, 0 failed;
- exact-base compatibility: 10 repetitions × 2 tests = 20 passed, 0 failed;
- no candidate-only optional-header race observed;
- clean status and `git diff --check`.

Strength: executable receipt. Disclosure: public-safe as a bounded summary; exact commands and environment/cache details are appendix-safe or private-by-default.

### Final test-polish approval

[`agent-3-final-test-polish-approval-7602167.md`](../agent-3-final-test-polish-approval-7602167.md)

Verdict: approved. Confirmed no production-code change in either test-polish commit and accepted the final head.

Strength: independent code review plus receipt review. Disclosure: appendix-safe.

## Matched broad-suite differential

Primary inventory: [`agent-1-clean-candidate-project-failure-inventory.md`](../agent-1-clean-candidate-project-failure-inventory.md).

Corrected summary for the production-equivalent candidate and exact base:

- candidate: 3,110 run; 3,015 passed including one flaky retry pass; 94 failed; one timed out; nine skipped;
- exact base: 3,102 run; 3,007 passed; 94 failed; one timed out; nine skipped;
- 93 failure names and the timeout were shared;
- the candidate-only and base-only broad-run failures both passed repeated focused runs on both refs;
- potentially Patch-1-related persistent failures: zero;
- unclassified persistent failures: zero.

Classification:

- baseline/environment-limited;
- not green;
- no persistent candidate-only failure remained;
- complete workspace suite not run.

Strength: executable matched differential with retained summaries and focused reruns. Disclosure: one-paragraph public summary; full inventory appendix-safe. Raw logs and ephemeral runner paths are private-by-default.

## Implementation and contract reviews

| Review | Reference | Verdict | Disclosure |
|---|---|---|---|
| Final production net-diff review | [`final-net-diff-review-73e5b9f.md`](../final-net-diff-review-73e5b9f.md) | Pass on reviewed investigation tree | Appendix-safe |
| Clean-candidate review | [`final-clean-candidate-review-3778e1f.md`](../final-clean-candidate-review-3778e1f.md) | Pass; byte-equivalent production/test contents before test polish | Appendix-safe |
| Architecture/API conventions | [`agent-3-architecture-api-conventions-review.md`](../agent-3-architecture-api-conventions-review.md) | Pass with non-blocking notes | Appendix-safe |
| Final roundtable synthesis | [`final-roundtable/synthesis.md`](../final-roundtable/synthesis.md) | Production pass; requested test-only revision | Appendix-safe |
| External review triage | [`external-review/triage-2026-07-26.md`](../external-review/triage-2026-07-26.md) | Production pass; static reviewers prompted test hardening | Appendix-safe |
| Final Agent 1 contract sanity check | [`agent-1-clean-candidate-handoff.md`](../agent-1-clean-candidate-handoff.md#final-short-contract-sanity-check) | Pass | Appendix-safe |
| Final publication readiness | [`final-publication-readiness-2026-07-26.md`](../final-publication-readiness-2026-07-26.md) | Ready for human wording and explicit approval | Appendix-safe |

## External review

Two independent static reviews—one Codex review and one Claude review—were triaged in [`external-review/triage-2026-07-26.md`](../external-review/triage-2026-07-26.md).

What they can support:

- independent inspection of provenance path, manager liveness authority, exact-cell lookup, terminal-only reporting, yielded neutrality, truncation placement, schema compatibility, and lifecycle non-expansion;
- identification of test-convention and robustness concerns later addressed in executable tests.

What they cannot support:

- runtime correctness by themselves;
- claims that tests passed;
- claims about environment compatibility beyond the code inspected.

Neither external reviewer compiled or ran the candidate. Public wording should call this independent static review, not independent validation.

## Related upstream reports

These are related by symptom or neighbouring policy, not necessarily duplicates.

| Issue | Relationship | Recommended public use |
|---|---|---|
| [`openai/codex#34866`](https://github.com/openai/codex/issues/34866) | Closest prior symptom: `Script completed` while a nested shell remains live; also discusses generated JavaScript forwarding output while omitting session metadata | Mention prominently as related prior symptom coverage, not the canonical issue |
| [`openai/codex#32411`](https://github.com/openai/codex/issues/32411) | Broader loss of arbitrary awaited-but-unemitted nested results and artifact handles | Optional secondary context |
| [`openai/codex#33816`](https://github.com/openai/codex/issues/33816) | Model abandonment after a session ID was already exposed | Optional distinction |
| [`openai/codex#14731`](https://github.com/openai/codex/issues/14731) | Proposal to block completion while unified-exec work remains live | Appendix only; different lifecycle policy |
| [`openai/codex#15723`](https://github.com/openai/codex/issues/15723) | Parent wake-up after subprocess/subagent completion | Appendix only; different eventing policy |
| [`openai/codex#32188`](https://github.com/openai/codex/issues/32188) | Consolidated event-driven background-exec wake-up discussion | Appendix only; different eventing policy |

No upstream pull request or merged commit was found during the 2026-07-26 refresh that implemented the same typed creator-cell attribution plus terminal exact-cell live-session disclosure. This is time-sensitive and should be refreshed immediately before publication.

## Scope and non-goal evidence

The final code and reviews support these statements:

- background process persistence is intentional;
- the patch restores model-visible session IDs;
- it does not terminate processes;
- it does not block a cell or turn from completing;
- it does not add wake-up events;
- it does not change pruning, shutdown, interrupt, dispatch, recovery, remote-exec, or hidden-subagent policy;
- it does not change the JavaScript result schema;
- it does not encode cell identity in opaque call IDs;
- it does not prove a literal memory leak;
- it does not establish a security severity.

## Mistakes, reversals, and corrected records

These belong in the deep-dive, not the public issue body:

1. The original acceptance test was packaged as a standalone integration target; repository convention required the aggregate `all` binary.
2. Process-creating submission initially sat outside the cleanup-protected future; it was moved inside.
3. A one-survivor case initially used fixed sleeps; it was replaced by a bounded deterministic PID/filesystem handshake.
4. Yielded neutrality initially scanned numeric tokens; it now directly checks that the terminal-only warning is absent.
5. The large-output case initially pinned an exact content-item count; it now checks the behavioural contract without fixing incidental serialization shape.
6. The broad-suite summary was initially transcribed as 93 failures/3,017 passes; retained output corrected it to 94 failures/3,015 passes with one flaky retry pass.
7. A candidate-only broad-run failure and an upstream-only failure were initially ambiguous; both passed repeated focused runs on both refs.
8. A proposed hard display cap was considered; the final human/reviewer position retained the full point-in-time list and documented later global history limits.
9. Several launcher/setup attempts failed before the repository-native focused run; none became candidate commits. Their raw troubleshooting belongs private-by-default.

## Privacy and access matrix

| Material | Default | Reason | Disclosure path |
|---|---|---|---|
| Final candidate code and commit-pinned tests | Public-safe | Already in public fork; directly reviewable | Link from PR/issue |
| Scrubbed validation summaries | Public-safe | No secrets or machine-specific paths needed | Include bounded summary |
| Detailed failure inventory | Appendix-safe | Long and potentially distracting, but technically relevant | Link on request or from evidence index |
| Research notes and agent handoffs | Internal-public-fork | Publicly accessible but not maintainer-facing copy | Link selectively, never imply upstream endorsement |
| External review prompts/responses | Internal or private depending on content | May contain copied code, prompts, or irrelevant metadata | Publish only scrubbed excerpts with approval |
| Raw chat transcripts | Private-by-default | May contain user data, unreviewed reasoning, and irrelevant context | Explicit human approval, redaction, and provenance note |
| Raw test logs/JSONL | Private-by-default | May contain machine paths, environment details, tokens, or user data | Retain access-controlled; publish hashes or scrubbed excerpts |
| Machine paths and cache locations | Private-by-default | Irrelevant to maintainer review and potentially identifying | Omit |
| Launcher troubleshooting | Private-by-default | Process archaeology, not patch evidence | Summarise only if needed to explain a limitation |

## Publication freshness triggers

Re-run or refresh before publication if any of these changes:

- upstream `openai/codex` main moves from the selected base;
- #34866 or another related issue gains a linked fix or exact reproduction;
- a new upstream PR implements equivalent behaviour;
- the canonical candidate branch moves;
- validation is rerun on a different candidate;
- public wording changes a technical claim or test count;
- a maintainer requests a display cap, generic origin model, schema change, or lifecycle change.

## Citation policy for final public copy

- Prefer commit-pinned code links over links to a moving branch.
- Link the aggregate acceptance test rather than internal chat or research notes.
- State test counts and platform once; link receipts for depth.
- Cite repository convention only where it explains a non-obvious test-organisation decision.
- Do not cite raw chats as technical proof.
- Do not treat static external review as executable validation.
- Do not link the exhaustive appendix unless it improves maintainer review; its existence is not a reason to burden the issue.
