# Code-mode orphan work: workflow retrospective

Date: 2026-07-26

Scope: internal research and workflow learning for `teamleaderleo/codex`.

This file is part of the investigation archive. It is not intended for the upstream Patch 1 pull request.

## Executive summary

The work succeeded because the team separated four concerns that are often mixed together:

1. understanding ownership and intended lifecycle policy;
2. implementing the smallest compatible fix;
3. proving the original failure and the corrected behaviour;
4. preparing a clear, privacy-safe public issue and pull request.

The central technical result is a narrow visibility fix. Background process persistence remains intentional. The patch restores model-visible session IDs when code-mode JavaScript discards copied handles before a terminal outer-cell response.

The central workflow result is equally useful: investigation history and final submission history should be different products.

- The investigation archive should preserve branches, intermediate commits, negative tests, rejected prototypes, decision logs, runtime reports, and handoffs.
- The upstream candidate should contain only the final production changes, focused tests, concise commit history, and public-facing explanation.

## Provenance retention policy

Preserve the following as an internal/public-fork audit trail:

- `research/code-mode-orphan-handoffs`;
- `research/code-mode-live-session-test`;
- `research/code-mode-live-session-acceptance`;
- the reviewed implementation branch `fix/code-mode-live-session-summary` at `73e5b9fc28de0815975fad3c3d70a6a0b38399b1`;
- coordination, decision, test-runtime, review, history, and follow-up research Markdown;
- the negative reproduction and corrected acceptance ancestry;
- the call-ID-prefix prototype as rejected feasibility evidence.

Do not force-push or delete those refs merely to make the upstream pull request look clean. Create a separate clean candidate from current upstream main.

Because the fork is public, this archive must be treated as publicly accessible. Provenance is valuable, but it is not a reason to retain secrets, private logs, tokens, prompts, machine-specific paths, or unrelated incident details.

Suggested retention lifecycle:

1. preserve all investigation refs through issue and PR review;
2. preserve them through merge or final upstream disposition;
3. optionally add a stable archive tag or manifest after the work concludes;
4. delete only accidental or sensitive material, not ordinary investigative history;
5. keep the clean upstream candidate separate from the archive permanently.

## What worked well

### A narrow contract was established before final implementation

The team converged on a precise Patch 1 boundary:

- typed creator-cell attribution;
- manager-owned liveness as source of truth;
- exact-cell live-only lookup;
- terminal-only disclosure;
- warning outside output truncation;
- opaque call IDs and unchanged JavaScript schema;
- no automatic termination or lifecycle-policy change.

That contract prevented the investigation from expanding into shutdown, interrupt, hidden-subagent, remote-exec, or macOS recovery policy.

### Ownership was investigated instead of guessed

The most important reasoning step was distinguishing:

- the code-mode callback task;
- the manager-owned live process;
- the copied JavaScript `session_id` handle.

That made the root cause legible: JavaScript can discard a handle without affecting the process manager's ownership. The defect is reporting and control visibility, not object lifetime in JavaScript.

### The negative proof was preserved separately

Keeping `7298dcf44f61164ffc25b8bdf5f136281caeb9f5` unchanged provided durable evidence of the baseline failure. The positive tests could evolve without destroying the clean reproduction.

This is a strong general pattern:

- one immutable failing proof;
- one evolving acceptance branch;
- one implementation branch;
- one later integrated candidate.

### Tests challenged the contract, not only the happy path

The acceptance work covered:

- multiple discarded live IDs;
- deterministic ordering;
- one process exiting before disclosure;
- large output and truncation placement;
- ordinary yielded-cell neutrality;
- exact creator-cell isolation;
- panic-safe cleanup.

The two-cell case was especially valuable because it tested the ownership design directly rather than merely observing that some IDs appeared.

### Static and runtime review were separated

The implementation received a preliminary net-diff review before canonical validation. Final sign-off was withheld until the formatted tested head was published and compared.

That sequence reduced two common risks:

- treating a plausible diff as a validated result;
- treating a passing test run on an unrecorded local tree as the final reviewed artifact.

### Agent specialisation was useful

The strongest division of labour was:

- Agent 1: implementation and integration;
- Agent 2: negative reproduction, acceptance contract, and runtime validation;
- Agent 3: ownership audit, design review, and net-diff sign-off;
- Agent 4: history, related issues, privacy, issue copy, and PR copy;
- human coordinator: handoff routing, sequencing, publication control, and final editorial judgement.

This reduced the chance that one agent would implement, write its own test, interpret its own result, and approve its own public framing without independent challenge.

### The human coordinator improved the outcome

Several coordinator behaviours were high leverage:

- relaying exact branch and commit references rather than vague status summaries;
- asking agents to read a shared coordination board;
- pausing publication despite a green implementation;
- explicitly requesting a final reconvene and personal wording pass;
- questioning Patch 1/2/3 scope instead of allowing reconstructed intent to become fact;
- recognising that research history should be preserved while the submission should be cleaned.

The coordinator's role was not merely administrative. It supplied the publication and scope judgement that individual technical lanes could not safely make alone.

## What could have gone better

These are process observations, not blame assignments.

### The coordination board became stale more than once

Branch heads, test results, and remaining gates changed faster than the central Markdown was updated. This created periods where the canonical board incorrectly described completed work as pending.

Improvement: every meaningful handoff should include an explicit board-update owner. A status item should contain both the tested SHA and the published SHA, because those can differ.

### Too many documents overlapped in purpose

The coordination board, decision log, Agent 2 runtime report, Agent 4 report, dispatch files, and review files sometimes repeated the same evidence. Repetition was useful for handoffs but increased stale-text risk.

Improvement: define document roles at the beginning:

- `coordination-status.md`: current state and next actions only;
- `decision-log.md`: durable design decisions and rejected alternatives;
- per-agent reports: detailed evidence owned by one lane;
- review files: immutable review verdicts for named SHAs;
- retrospective: workflow learning after correctness is complete.

### A test assertion initially contradicted the selected output contract

The first positive test expected `Wall time` immediately after `Script completed`, even though the fix intentionally inserted the live-session line between them.

Improvement: write the behavioural contract in plain text before encoding assertions. Assert independent invariants rather than one brittle full string when layout has multiple valid components.

### The formatted validation SHA was not captured during the original run

A local formatting-only commit was created and tested, but its SHA was absent from the first handoff. The team had to recreate and verify the exact formatting descendant later.

Improvement: every test report should begin and end with:

```text
base_sha=
worktree_sha_before=
worktree_dirty_before=
worktree_sha_after=
worktree_dirty_after=
```

If formatting changes files, commit or record the resulting tree before running expensive validation.

### An overly broad Cargo fallback exhausted runner memory

A command intended to select one test widened into unrelated integration binaries and linkers were killed by signal 9.

Improvement:

- resolve repository-native test selection before starting;
- inspect the command's target scope;
- prefer explicit `--lib` or named integration targets when repository wrappers are unavailable;
- record infrastructure failures separately from code/test failures;
- do not let an emergency fallback silently redefine the validation claim.

### Repository-native tooling was not bootstrapped early

`just`, `dotslash`, `uv`, and `cargo-nextest` were missing in the Lima environment. The team produced valid focused evidence, but only through documented deviations.

Improvement: the first runtime task should be an environment capability check. Install or explicitly waive required tools before code work reaches the validation gate.

### Clean-history planning happened late

The investigation branch accumulated prototype, correction, merge, formatting, and evidence history before the clean-candidate strategy was formalised.

That history is valuable and should be preserved, but the upstream-submission plan should have existed from the start.

Improvement: declare two products on day one:

- an append-only investigation archive;
- a disposable clean candidate reconstructed from the reviewed net effect.

### Confidence labels were not always visible enough

The delayed cross-turn dispatch path became a high-confidence static finding, but executable reproduction was absent. Without repeated reminders, it could easily have been described as a confirmed bug.

Improvement: maintain a claims ledger using explicit states:

- reproduced;
- validated fix;
- statically confirmed mechanism;
- high-confidence hypothesis;
- weak hypothesis;
- ruled out;
- deferred product decision.

Every public statement should map to one state.

### Branch monitoring initially omitted an important acceptance branch

The automated watch covered several branches but not the later acceptance branch. Manual handoffs repaired the gap.

Improvement: derive monitored refs from the coordination board or keep one explicit branch manifest, rather than hard-coding a list that can become incomplete.

### Public-fork privacy was recognised late

Some notes used the word “private” even though the fork and research branches were publicly accessible.

Improvement: classify storage visibility at project start. “Unpublished upstream” does not mean private.

## Recommended workflow for future large-codebase investigations

### Phase 0: establish the work map

Before parallel work begins, write:

- baseline SHA;
- upstream target branch;
- issue statement;
- confirmed facts versus hypotheses;
- selected narrow contract;
- non-goals;
- branch map;
- lane owners;
- required repository tooling;
- expected clean-submission strategy;
- publication/privacy classification.

### Phase 1: preserve a minimal negative proof

Create one clean commit that demonstrates the bug and performs safe cleanup. Do not modify it afterward except to repair a test that never actually reproduced the claimed condition.

### Phase 2: build a claims and decisions ledger

For each decision, record:

- file and symbol examined;
- intended upstream behaviour;
- evidence source;
- confidence state;
- chosen contract;
- alternatives rejected;
- test obligation;
- whether the decision is in scope now or deferred.

### Phase 3: separate implementation and acceptance ownership

The implementation owner should not be the sole author and interpreter of the acceptance contract. The test owner should try to break ownership isolation, liveness filtering, boundary timing, cleanup, and output placement.

### Phase 4: review before expensive validation

Perform a static net-diff review to catch:

- contract mismatch;
- hidden lifecycle changes;
- public schema changes;
- identifier coupling;
- missing isolation coverage;
- unnecessary file spread.

Do not call this final sign-off.

### Phase 5: validate a named tree

Record the exact tree before and after formatting. Run commands against a committed or otherwise uniquely identified tree. Separate:

- compile/check;
- focused unit tests;
- integration/acceptance tests;
- platform skips;
- infrastructure failures;
- repository-native validation;
- broader workspace validation not run.

### Phase 6: publish the tested tree, then review it

A local passing tree is not enough. Publish or otherwise identify the exact tested tree, compare it to the pre-validation head, and perform final net-diff review.

### Phase 7: prepare public materials independently

The issue editor should verify:

- the issue describes the defect rather than a non-bug symptom;
- related issues are current and correctly distinguished;
- validation claims are bounded;
- privacy-sensitive evidence is removed;
- non-goals are explicit;
- the proposed PR is one coherent stage.

### Phase 8: reconstruct a clean candidate

Create the final candidate from current upstream main. Preserve semantic equivalence, not investigative ancestry. Exclude coordination notes and research reports. Use one or two reviewable commits.

### Phase 9: reconvene before publication

Ask each lane to review the same clean candidate and public drafts. Require explicit answers for code, scope, tests, history, issue framing, PR framing, privacy, related work, and publication order.

## A lighter solo-development version

The multi-agent process can be reduced to a set of “hats” for solo work:

1. **Investigator hat:** establish the failure and ownership model.
2. **Designer hat:** write the narrow contract and non-goals.
3. **Implementer hat:** make the smallest change.
4. **Adversarial tester hat:** test isolation, races, truncation, and cleanup.
5. **Reviewer hat:** inspect the net diff against the contract.
6. **Release editor hat:** prepare clean history and public explanation.

The key is temporal separation. Do not wear all six hats in one uninterrupted pass.

A practical solo file set can be small:

- `work-status.md`: current state only;
- `decision-log.md`: durable reasoning;
- `test-log.md`: exact commands and named SHAs;
- `retrospective.md`: lessons after completion.

For small work, these can be sections in one scratch document. For large work, keeping them separate reduces context loss.

## Repository-level workflow ideas worth considering

These are possible future additions for the user's own workflow. They should not be added to the upstream Patch 1 candidate without a separate decision.

### A reusable investigation template

A template could request:

- problem statement;
- baseline and upstream refs;
- reproduction status;
- ownership map;
- contract and non-goals;
- branch/lane table;
- claims ledger;
- validation matrix;
- publication gate;
- clean-candidate plan;
- retrospective link.

### A handoff schema

Every agent or work session should report:

```text
lane:
branch:
base_sha:
head_sha:
changed_files:
commands_run:
results:
skips_or_flakes:
confirmed_findings:
hypotheses:
open_risks:
next_owner:
requested_decision:
```

### A named-tree validation helper

A small script could print and persist:

- current branch and SHA;
- dirty status;
- upstream divergence;
- tool availability;
- formatter result;
- command/result table;
- final SHA and diff check.

This would have prevented the missing formatted SHA and reduced ambiguity about which tree passed.

### A research-archive manifest

A manifest could list preserved branches, key commits, files, and sensitivity status. It should make clear which refs are provenance only and which branch is the clean submission candidate.

### A periodic reconvene trigger

Reconvene when any of these occurs:

- the selected design changes;
- a test invalidates an assumption;
- the tested tree differs from the published tree;
- a new related issue or upstream fix appears;
- publication copy is ready;
- cleanup or rebase begins;
- correctness is complete but submission work remains.

### A “definition of done” split

Track two independent states:

- **correctness done:** reproduced, fixed, tested, reviewed;
- **submission done:** synced, cleaned, repository-native checks run, public text reviewed, links created.

This project reached correctness done before submission done. Naming that distinction reduced pressure to publish prematurely.

## Questions for the final reconvene

1. Were Patch 2 and Patch 3 concrete original proposals or only names for follow-up families?
2. Which investigation branches and notes should receive a stable archive tag or manifest?
3. Should the clean candidate use one commit or separate implementation and tests?
4. Which repository-native checks are required before opening the PR, and which broader run needs explicit approval?
5. Is issue-first-then-PR still preferred after the clean candidate exists?
6. What wording should be shortened or made less implementation-heavy for maintainers?
7. Which workflow ideas belong in this fork as reusable templates, and which should remain informal personal practice?
8. How should future agents discover the canonical status document automatically?
9. Should a branch watcher derive its branch list from a manifest?
10. Which follow-up hypotheses deserve executable tests next, and which should be left alone until a real incident demands them?

## Final assessment

The team handled a large codebase and a long context successfully by externalising state into branches and documents, separating roles, preserving negative evidence, and refusing to turn plausible static findings into confirmed claims.

The main opportunity is to make that structure intentional earlier:

- define document roles;
- capture named trees automatically;
- bootstrap repository tooling before validation;
- distinguish archive history from submission history from day one;
- use explicit confidence labels;
- schedule reconvenes at state transitions rather than only when confusion accumulates.

The investigation archive is worth keeping. The clean PR should not contain it. Both are legitimate outputs serving different audiences.