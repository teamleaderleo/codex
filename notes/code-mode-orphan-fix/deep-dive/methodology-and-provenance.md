# Patch 1 methodology and provenance

Status: internal by default. This document explains how the investigation was conducted and how claims were checked. It is not part of the upstream issue or pull request unless the human coordinator explicitly chooses to disclose it.

## Purpose

This record separates four things that are easy to blur in an AI-assisted engineering investigation:

1. human judgement and approval;
2. AI-generated analysis, code, tests, and prose;
3. executable verification against the repository;
4. independent external static review.

The public Codex issue should describe the defect and evidence, not announce or defend an AI workflow. Methodology belongs in a separate appendix for readers who care about provenance.

## Coordination model

The investigation was coordinated by one human across four regular ChatGPT chat instances. They were not treated as one shared omniscient agent. Each instance had a defined lane, separate working context, explicit handoffs, and bounded write authority.

### Lane 1: implementation and clean-candidate construction

Primary responsibilities:

- inspect the runtime and unified-exec ownership path;
- implement the selected visibility-only change;
- preserve a clean candidate separate from research ancestry;
- classify the broad `codex-core` differential against the exact upstream base;
- perform a final contract sanity check after test polish.

Representative outputs:

- clean candidate branch and commit history;
- implementation-conventions review;
- matched project-failure inventory;
- final implementation handoff.

### Lane 2: reproduction, acceptance tests, and validation

Primary responsibilities:

- preserve an executable negative reproduction;
- define and implement the positive acceptance contract;
- run repository-native focused validation;
- revise test packaging and robustness after review;
- produce machine-readable or structured validation receipts.

Representative outputs:

- negative proof and acceptance lineage;
- aggregate code-mode acceptance module;
- test-polish receipts;
- repeated candidate/base compatibility evidence.

### Lane 3: ownership audit, architecture review, and independent gatekeeping

Primary responsibilities:

- audit ownership and liveness authority independently of implementation intent;
- review exact comparisons rather than branch names alone;
- distinguish blocking findings from non-blocking API-shape concerns;
- review test-polish changes and validation receipts;
- synthesise roundtable and external-review findings.

Representative outputs:

- final net-diff review;
- architecture/API conventions review;
- roundtable synthesis;
- external-review triage;
- final test-polish approval.

### Lane 4: history, related work, privacy, and publication

Primary responsibilities:

- research related upstream issues and distinguish overlap from duplication;
- prepare and audit issue/PR copy;
- keep validation claims bounded;
- scrub machine-specific, private, and irrelevant material;
- design a layered publication package and evidence index.

Representative outputs:

- related-issue distinctions;
- final unpublished issue and PR drafts;
- publication-conventions review;
- this deep-dive publication architecture and evidence index.

## What the human coordinator decided

The human coordinator retained authority over decisions that tests cannot settle:

- whether the observed behaviour was important enough to pursue;
- the selected Patch 1 contract: restore visibility without changing lifecycle policy;
- whether to keep a standalone issue rather than only commenting on #34866;
- whether to accept a baseline-red broad-suite differential after exact-base comparison;
- whether a complete workspace run was worth its cost;
- whether to retain the full point-in-time session-ID list rather than add a display cap;
- privacy and disclosure boundaries;
- final severity language;
- title, wording, publication order, publication time, and actual upstream publication.

AI recommendations informed these decisions but did not replace explicit human approval.

## What AI-generated work contributed

Across the four chat instances, AI-generated work included:

- code-path analysis and ownership hypotheses;
- implementation patches;
- test cases and test-harness revisions;
- validation command selection;
- failure classification proposals;
- related-issue searches and distinctions;
- review notes, handoffs, and publication drafts;
- this methodology record.

AI-generated text was treated as a proposal until checked against one or more of:

- commit-pinned source;
- executable tests;
- exact candidate/base comparison;
- retained command output;
- independent review;
- explicit human decision.

No claim should be accepted merely because multiple AI instances repeated it. Agreement can still reproduce a shared misunderstanding.

## Executable verification

The strongest evidence came from repository execution and exact comparisons.

### Negative reproduction

A baseline test demonstrated the failure mode:

- nested `exec_command` calls yielded live session IDs;
- JavaScript projected the returned values to `.output`;
- the outer cell reported completion;
- the session-level manager still tracked live sessions;
- the model-visible result lacked their IDs.

The negative proof was preserved in commit history rather than described from memory alone.

### Focused production and acceptance validation

At the final candidate:

- repository formatting passed;
- scoped fix/lint passed;
- four focused unit tests passed;
- five aggregate acceptance cases passed;
- two existing compatibility tests passed 20/20 executions on the candidate;
- the same tests passed 20/20 on the exact upstream base;
- worktree inspection and `git diff --check` passed.

The acceptance cases exercised:

- multiple discarded live session IDs and numeric ordering;
- exited-session exclusion;
- exact completing-cell isolation;
- warning placement outside code-mode emitted-output truncation;
- yielded neutrality.

### Matched broad-suite differential

The broad `codex-core` suite was not green on either the candidate or exact upstream base. The candidate and base were run with the same repository-native command and comparable hosted-runner setup.

The retained record corrected an early transcription error and established:

- candidate: 3,110 run; 3,015 passed including one flaky retry pass; 94 failed; one timed out; nine skipped;
- base: 3,102 run; 3,007 passed; 94 failed; one timed out; nine skipped;
- 93 failure names and the timeout were shared;
- the candidate-only and base-only broad-run failures passed repeated focused runs on both refs;
- no persistent candidate-only failure remained;
- no persistent failure remained potentially related to Patch 1 or unclassified.

This supports a baseline/environment-limited classification. It does not support saying the broad suite passed.

### What was not run

The complete workspace suite was not run. The focused validation exercised `codex-core` and the affected code-mode paths; it did not build and run every Codex product surface on every platform.

## Independent external review

Two independent static reviews were received after an external review packet was prepared:

- one Codex review;
- one Claude review.

They independently inspected the production design and raised test-convention and robustness concerns. They did not compile or run the candidate.

Their contribution was therefore:

- independent static scrutiny;
- identification of plausible review risks;
- pressure-testing of ownership, liveness, truncation, schema, and lifecycle claims.

Their contribution was not:

- executable validation;
- proof that tests passed;
- proof of cross-platform runtime behaviour.

Static findings that affected test behaviour were subsequently checked through repository-native tests before being accepted.

## Claim classes used in the investigation

A useful provenance model is:

### Observed

Directly present in source, test output, a commit comparison, or a preserved artifact.

Example: the final code queries the manager only for `Result` and `Terminated` responses.

### Reproduced

Demonstrated by an executable test with a defined assertion.

Example: JavaScript can discard two live session IDs and the terminal result can omit them on the baseline.

### Differentially classified

A failure or behaviour compared on candidate and exact base under matched conditions.

Example: the broad suite is baseline/environment-limited with no persistent candidate-only failure.

### Independently reviewed

Inspected by a reviewer separate from the authoring lane, but not necessarily executed.

Example: external Codex and Claude static reviews.

### Inferred

Supported by code and evidence but not directly reproduced.

Example: some deferred cross-turn or shutdown race concerns. These must not be described as confirmed bugs.

### Human decision

A scope or policy choice not mechanically established by tests.

Example: retaining the full live-session list and relying on later global history limits rather than adding a display cap.

Public copy should use the strongest accurate verb and no stronger one.

## Mistakes and reversals

The investigation was not linear. The following corrections are part of the provenance and should not be erased from the internal record.

### 1. The first test packaging did not follow repository convention

The initial acceptance cases were placed in a standalone integration target. Review found that `codex-rs/core/tests/all.rs` intentionally defines one aggregate integration binary and that code-mode already had a shared suite module.

Correction:

- remove the standalone target;
- move the five cases into `tests/suite/code_mode/orphan_sessions.rs`;
- reuse the parent code-mode helpers and assertion imports.

Lesson: repository test topology is part of correctness and maintainability, not cosmetic packaging.

### 2. Cleanup protection began too late

Several tests originally submitted the process-creating turn before entering the panic/error cleanup wrapper. A submission error after process creation could bypass cleanup.

Correction:

- move every process-creating submission inside cleanup protection;
- preserve an original panic after cleanup;
- surface cleanup errors when no original panic exists.

The final public wording states the structural property. It does not claim the five acceptance cases deliberately execute every cleanup path.

### 3. Fixed sleeps created avoidable race risk

The one-survivor case initially depended on fixed process sleeps.

Correction:

- use a bounded PID/filesystem handshake;
- release the short process deterministically;
- poll for confirmed exit with an upper bound;
- keep the survivor live for the terminal assertion.

### 4. A yielded assertion tested an incidental symptom

The initial yielded-neutrality check scanned numeric tokens, which could fail for unrelated numbers.

Correction:

- assert directly that `Background sessions still running:` is absent from a yielded response.

### 5. The large-output test pinned incidental serialization shape

The initial test expected exactly two content items.

Correction:

- locate the separate status item by its completion prefix;
- assert the live-session warning and IDs there;
- require a separate non-empty emitted-output representation without fixing the complete item count.

### 6. The broad-suite summary was transcribed incorrectly

An early handoff said 93 failures and 3,017 passes. Retained nextest output showed 94 failures, 3,015 passes, one timeout, nine skips, and one flaky retry pass.

Correction:

- update the inventory and all publication wording;
- treat raw retained output as authoritative over compact handoff prose.

### 7. Differential failures were initially ambiguous

The candidate broad run had one failure name not present on base; the base had a different unique failure.

Correction:

- run both tests repeatedly on both refs in one shared runner/cache;
- all 12 focused executions passed;
- classify them as run-order/concurrency flakes rather than candidate regressions.

### 8. A display cap was considered but not added

External review noted that the exact-cell summary has no independent hard cardinality cap.

Decision:

- retain the complete point-in-time list so the patch does not knowingly omit live control handles;
- document that the complete tool result remains subject to later global conversation-history limits;
- leave a maintainer-requested cap as a review-time option;
- do not change pruning or lifecycle policy to solve a presentation concern.

### 9. Some validation-launch attempts failed before the final run

There were failures involving local tool prerequisites, launcher assumptions, workspace paths, macro ambiguity, and an unsupported first deterministic-exit handshake.

Correction:

- fail closed;
- do not publish failed attempts as candidate results;
- correct the command or test and rerun repository-native validation;
- keep raw troubleshooting out of public copy unless needed to explain a limitation.

### 10. Research history and public candidate history had to be separated

The investigation accumulated prototype, correction, review, and coordination commits.

Correction:

- preserve research branches and notes as provenance;
- reconstruct a clean candidate on the selected upstream base;
- add only reviewed test-polish commits after the production implementation;
- keep all research Markdown out of the candidate history.

## Limitations

### Platform coverage

Focused and acceptance validation was recorded on Linux aarch64. Windows-specific acceptance cases are ignored because the relevant `exec_command` path is unavailable there. This does not establish behaviour on every supported platform.

### Broad-suite state

The broad `codex-core` suite remained red on both candidate and exact base. Exact-base comparison and focused reruns support the conclusion that no persistent candidate-only failure remained, but they do not turn the suite green.

### Workspace coverage

The complete workspace suite was not run.

### External review scope

External reviewers performed static inspection only.

### Runtime timing

The manager query is a point-in-time liveness check. A process can change state immediately afterward. The patch reports what the manager considers live at query time; it does not promise a durable future state.

### Remote exit state

Review noted a possible point-in-time over-report window where cached remote exit state may lag. No demonstrated correctness failure was established, and no recovery or remote-exec policy change was included.

### Terminated-path acceptance

Unit coverage exercises terminal status formatting for terminated responses, but the five aggregate acceptance cases focus on successful terminal completion, exited filtering, truncation, yielded neutrality, and cell isolation. There is no separate end-to-end `Terminated` acceptance case.

### Memory and security claims

The evidence does not show unreachable allocated memory, so the behaviour should not be called a literal memory leak. It may create operational resource-leak risk because live processes can retain resources. No security severity has been established.

### Deferred concerns

The following remain separate and should not be smuggled into Patch 1 claims:

- generic process-origin modelling;
- hidden/subagent ownership and cleanup policy;
- automatic termination or completion blocking;
- unreproduced cross-turn dispatch behaviour;
- shutdown/store-after-drain races;
- remote bulk-termination confirmation;
- natural-exit stale bookkeeping;
- event-driven wake-up;
- macOS/runtime-loss orphan recovery.

## Why the public issue should not describe the AI workflow

Maintainers need to evaluate:

- the user-visible defect;
- the reproduction;
- the expected behaviour;
- the proposed design;
- the scope boundaries;
- the validation.

They do not need the issue body to explain four chat lanes, prompt history, model identities, failed drafting attempts, or internal coordination mechanics. Adding that material would:

- distract from the bug;
- increase review burden;
- make executable evidence harder to find;
- risk exposing irrelevant private material;
- imply that workflow provenance substitutes for technical proof.

If methodology is shared, link it as optional background after the technical package stands on its own.

## Private-by-default disclosure path

Raw chat and log material should not be committed or published automatically.

### 1. Retain privately

Store raw materials in access-controlled storage separate from the upstream candidate and public issue/PR:

- complete chat exports;
- raw JSONL or terminal logs;
- external-review prompts and full responses;
- machine-specific validation logs;
- environment inventories;
- any artifact containing user data, paths, tokens, credentials, or unrelated repository content.

### 2. Create a private manifest

For each retained artifact, record:

- stable local identifier;
- date/time;
- owner/custodian;
- content type;
- relevant claim(s);
- cryptographic hash;
- sensitivity classification;
- retention period;
- whether a scrubbed derivative exists.

Do not put secrets or private paths into the public manifest.

### 3. Produce scrubbed derivatives

When an artifact is genuinely useful:

- extract only the relevant lines or result summary;
- remove tokens, credentials, usernames, home directories, cache paths, and unrelated conversation text;
- preserve enough context to avoid quote mining;
- state whether the excerpt is complete or selective;
- attach a hash or reference to the private original when appropriate.

### 4. Require explicit approval

Raw or scrubbed disclosure should require a separate human decision from code publication. Approval should identify:

- exactly which artifact or excerpt is being disclosed;
- the intended audience;
- the reason disclosure is necessary;
- the redactions applied;
- whether third-party or user data is present.

### 5. Prefer evidence substitution

When possible, replace raw-chat or raw-log disclosure with stronger public evidence:

- a commit-pinned test;
- a minimal reproduction;
- a command and bounded result summary;
- an exact comparison;
- a scrubbed failure inventory;
- an independent review note.

Raw chats are provenance, not proof.

## Recommended public provenance statement, if requested

If maintainers ask how the work was produced, a bounded disclosure could be:

> This investigation was human-coordinated across separate AI-assisted implementation, testing, review, and publication lanes. All technical claims in this issue and PR are grounded in commit-pinned code, executable tests, matched candidate/base comparisons, or explicitly labelled static review. Raw chat and machine logs are retained privately and are not part of the correctness claim.

Do not add this proactively to the issue or PR unless the human coordinator decides it is useful.

## Final provenance rules

1. A chat statement is not evidence until grounded.
2. Multiple AI agreements do not create independence by themselves.
3. Static review is not runtime validation.
4. A green focused suite does not make a red broad suite green.
5. An exact-base differential can classify failures without proving every product surface.
6. Human scope and publication decisions must be labelled as decisions, not test results.
7. Mistakes and reversals should remain in the internal record.
8. Raw private material should be opt-in, minimised, and separately approved.
9. The public issue must stand on reproduction and impact.
10. The public PR must stand on code, design rationale, boundaries, and bounded validation.
