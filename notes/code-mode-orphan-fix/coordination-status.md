# Code-mode orphan fix: coordination status

Last updated: 2026-07-26

Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`

## Current phase

Patch 1 correctness work is complete. The remaining work is submission hygiene, one final team sanity review, the user's wording and presentation review, and publication sequencing.

Active clean-candidate dispatch:

- File: `notes/code-mode-orphan-fix/agent-1-clean-candidate-dispatch.md`
- Dispatch commit: `f039be83561aeeb2a82868394f7b17f783efee12`

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

## Final reviewed implementation

Branch: `fix/code-mode-live-session-summary`

Published formatted head: `73e5b9fc28de0815975fad3c3d70a6a0b38399b1`

Integrated merge parent: `4263facaf3c7d30b26cae33fd1e679278ac02105`

Reviewed comparison:

`20dafe201d91d4405eef05ecd1db0257f13a9ac8...73e5b9fc28de0815975fad3c3d70a6a0b38399b1`

The formatting commit changes only:

- `codex-rs/core/src/tools/code_mode/mod.rs`;
- `codex-rs/core/src/unified_exec/process_manager.rs`.

That delta is formatter line wrapping only.

## Verified evidence

### Negative reproduction

- Branch: `research/code-mode-live-session-test`
- Commit: `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
- Result: `1 passed; 0 failed; 0 ignored`

The test proves that two nested unified-exec processes can remain manager-owned and live after JavaScript discards both copied `session_id` values and the outer cell reports terminal completion without either ID.

### Corrected acceptance lineage

- Branch: `research/code-mode-live-session-acceptance`
- Head: `89ffd99b81e872e3a961767e67fb8ec410df7eae`
- Negative proof: `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
- Initial acceptance: `528171c72c06d8be3471752322b7755a1eac3ac8`
- Contract and two-cell isolation correction: `0ba57a73ea5895883a21aeb88e923d75a74ed38d`
- Truncation assertion correction: `89ffd99b81e872e3a961767e67fb8ec410df7eae`

Coverage includes:

- two discarded surviving IDs reported once and in numeric order;
- exited-process exclusion with one survivor;
- warning placement outside emitted-output truncation;
- yielded-response neutrality;
- exact creator-cell isolation;
- panic-safe cleanup with no registered test terminal left behind.

### Canonical validation

Detailed report: `notes/code-mode-orphan-fix/agent-2-test-runtime-report.md`

Validation dispatch: `ddaad65e0ad98c8bc3400937b11f53fb14dd52b9`

Platform: Linux aarch64 under Lima.

Results on the Rust-formatted tree published as `73e5b9fc28de0815975fad3c3d70a6a0b38399b1`:

- compile/check: passed;
- focused code-mode library tests: `3 passed; 0 failed`;
- focused unified-exec library tests: `3 passed; 0 failed`;
- complete acceptance target: `5 passed; 0 failed; 0 ignored`;
- no skips or flakes on the correctly scoped commands;
- panic-safe acceptance cleanup remained active.

A broad ad hoc Cargo command selected unrelated integration binaries and exhausted runner memory during linking. This was a command-selection and runner event, not a Patch 1 compile or assertion failure. Full workspace validation is not claimed.

## Final correctness review

Review file: `notes/code-mode-orphan-fix/final-net-diff-review-73e5b9f.md`

Review commit: `8577cea6c925dde7453641b7587190285979a3ad`

Verdict: pass.

Confirmed:

- typed creator-cell attribution reaches stored `ProcessEntry`;
- exact-cell lookup excludes exited processes and sorts logical IDs;
- lookup is read-only and does not change lifecycle policy;
- only `Result` and `Terminated` report surviving sessions;
- `Yielded` remains completion-neutral;
- output is truncated before the status header is prepended;
- nested call IDs remain opaque;
- the JavaScript result schema is unchanged;
- no termination, persistence, pruning, shutdown, interrupt, dispatch, subagent, remote-exec, recovery, or public-protocol policy expansion was found.

No further Patch 1 code change is requested by the correctness review.

## Agent 4 publication preparation

Report: `notes/code-mode-orphan-fix/agent-4-history-issue-report.md`

Completion commit: `4e29825feef368329a8588bd2b5f1d35d1b934e5`

Completed:

- final reviewed head and comparison recorded;
- stale unpublished-head wording removed;
- issue draft updated;
- one-PR title and body prepared;
- related issues and newer-fix search refreshed;
- privacy scrub completed for proposed public copy;
- recommendation recorded to publish the issue and immediately follow with the PR;
- issue and PR remain unpublished.

Agent 4 found no newer exact duplicate or merged typed-creator-cell visibility fix. `#34866` remains the closest symptom. Recheck immediately before publication if publication is delayed.

## Current agent states

### Agent 1

Implementation, integration, formatting publication, and tested branch work are complete.

Next responsibility: execute `notes/code-mode-orphan-fix/agent-1-clean-candidate-dispatch.md` from dispatch commit `f039be83561aeeb2a82868394f7b17f783efee12`, preserving the reviewed net effect without prototype, investigation, or research ancestry.

### Agent 2

Regression, acceptance, and focused validation work are complete.

Next responsibility: help classify only concrete clean-candidate validation failures. Do not broaden validation claims beyond the recorded focused runs.

### Agent 3

Final correctness review is complete.

Next responsibility: compare the clean candidate against `73e5b9fc28de0815975fad3c3d70a6a0b38399b1` and reject any late lifecycle-policy expansion.

### Agent 4

Evidence and publication-copy work are complete at `4e29825feef368329a8588bd2b5f1d35d1b934e5`.

Next responsibility: participate in the final sanity review and update only concrete clean-candidate metadata, wording decisions, and eventual issue/PR links.

## Remaining pre-PR engineering hygiene

These are submission tasks, not unresolved Patch 1 correctness findings.

1. Prepare a clean candidate branch or commit sequence from current upstream `openai/codex` main.
2. Preserve only the six production-file changes and dedicated acceptance test represented by the reviewed net effect.
3. Exclude all coordination, research, audit, and agent-handoff Markdown from the upstream candidate.
4. Record the upstream-main sync result.
5. Run the repository-native formatter, lint/fix, and agreed test commands on the clean candidate.
6. Record actual final repository inspection output, including `git status --short` and `git diff --check`.
7. Publish a clean comparison and verify semantic equivalence to the reviewed head.
8. Complete one final team sanity review.
9. Complete the user's wording and presentation review.
10. Approve issue/PR ordering.
11. Publish and cross-link only after all preceding items are complete.

## Final reconvene agenda

Each agent should answer these questions against the clean candidate and final public drafts:

1. **Code:** Is the candidate semantically equivalent to `73e5b9fc28de0815975fad3c3d70a6a0b38399b1`?
2. **Scope:** Is the change still visibility-only, with no lifecycle-policy expansion?
3. **Tests:** Which repository-native commands actually ran, and what passed, skipped, failed, or was not run?
4. **History:** Is the commit sequence concise and reviewable, with no research notes or prototype history?
5. **Issue framing:** Does the issue describe loss of model-visible control information rather than intended process persistence as the defect?
6. **PR framing:** Does the PR explain the typed ownership path, behavioural boundary, and acceptance coverage without overselling validation?
7. **Privacy:** Does the public copy omit machine paths, private logs, usernames, prompts, tokens, and unrelated incident details?
8. **Related work:** Are the distinctions from `#34866`, `#32411`, `#33816`, `#14731`, `#15723`, and `#32188` still current?
9. **Publication:** Is issue-first-then-PR still the preferred sequence after final checks?
10. **Follow-ups:** Are delayed dispatch, shutdown races, remote termination, stale bookkeeping, hidden-subagent policy, and macOS recovery still clearly excluded?

## Patch 2 and Patch 3 question

Patch 1 is formally defined and complete. The repository notes do not contain an equally precise, approved contract for Patch 2 or Patch 3.

At the final reconvene, Agent 1 should clarify whether Patch 2 and Patch 3 were concrete planned changes in the original discussion or merely labels for follow-up families. Do not create or publish additional patches based only on reconstructed intent.

A plausible but unconfirmed grouping is:

- Patch 2: lifecycle and product-policy decisions, such as automatic termination, persistence opt-in, or hidden-subagent ownership;
- Patch 3: resilience and recovery work, such as dispatch races, shutdown races, remote termination confirmation, stale bookkeeping, or macOS orphan recovery.

Treat that grouping as a hypothesis until Agent 1 confirms the original framing.

## Publication preparation gate

Completed:

- [x] Negative reproduction preserved and passed.
- [x] Corrected acceptance suite integrated.
- [x] Exact creator-cell isolation covered.
- [x] Formatted tested head published.
- [x] Focused compile and tests passed.
- [x] Final net-diff review passed.
- [x] Agent 4 issue and PR drafts prepared.
- [x] Related-issue refresh completed.
- [x] Public-copy privacy scrub completed.

Open:

- [ ] Clean candidate history exists.
- [ ] Upstream-main sync is recorded.
- [ ] Repository-native validation is recorded.
- [ ] Final repository inspection is recorded.
- [ ] Clean candidate equivalence review passes.
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
