# Agent 4 publication-conventions review

Agent: 4
Lane: history, related work, privacy, and publication conventions
Reviewed base: `61a44880a85d2fd0d8770908dea5733495e571c8`
Reviewed candidate: `3778e1fae6e7e3d885252282a7c5ce67e06730ff`
Verdict: pass with notes

Concrete findings:
- The issue draft explains the user-visible defect clearly: a terminal code-mode result can say `Script completed` while still-live nested exec sessions remain manager-owned but their copied IDs have been discarded by JavaScript and are absent from the model-visible result.
- The issue should remain problem-led. Its summary, reproduction, actual behaviour, and expected behaviour are sufficient; detailed ownership plumbing belongs mainly in the PR.
- The PR has the right implementation outline, but it should state the design rationale explicitly: the existing unified-exec process manager remains the sole source of liveness, while typed creator-cell metadata scopes a read-only lookup and avoids both a second registry and ownership inference from JavaScript values or call-ID strings.
- The behavioural boundary is correct and should be stated compactly in both documents: disclosure occurs only for terminal `Result` and `Terminated` responses; ordinary `Yielded` responses remain neutral; the JavaScript result schema, opaque nested call IDs, persistence, pruning, termination, shutdown, interrupt, dispatch, and recovery policy remain unchanged.
- Validation claims must be bounded. Repository-native formatting and scoped fix passed; all six focused code-mode and unified-exec tests passed; the dedicated acceptance target passed 5/5 with no skips. The broad `just test -p codex-core` suite was red on both the candidate and exact upstream base and must not be described as green.
- The matched differential supports a baseline/environment-limited classification: persistent failures were shared or attributable to missing helpers, sandbox/runner limitations, timeouts, or unrelated upstream assertions; the two differing broad-run failures passed repeatedly on both refs; no persistent candidate-only failure remained.
- Patch 2 and Patch 3 should be omitted from public copy entirely. They were internal planning labels for separate follow-up families, not approved commitments.
- The related-issue distinctions remain serviceable: #34866 is the closest symptom; #32411 is broader awaited-but-unemitted-result loss; #33816 concerns abandonment after an ID was already exposed; #14731 concerns blocking completion; #15723 and #32188 concern wake-up/eventing after completion.
- The privacy scrub remains appropriate. Public copy should omit agent identities, research branches, coordination commits, review filenames, machine paths, private prompts, raw logs, the earlier ad hoc linker incident, and other investigation-only provenance.
- Issue-first-then-PR remains the preferred publication sequence, with immediate cross-linking in the same working session.

Required code or test changes:
- none

Public-copy corrections:
- Replace investigation-head references with clean candidate `3778e1fae6e7e3d885252282a7c5ce67e06730ff` and comparison `61a44880a85d2fd0d8770908dea5733495e571c8...3778e1fae6e7e3d885252282a7c5ce67e06730ff`.
- In the issue, shorten the ownership section to three points: yielded processes are intentionally manager-owned; JavaScript may discard copied session IDs; terminal rendering needs creator attribution to recover exact-cell live IDs.
- In the PR, add one explicit rationale sentence preserving the process manager as the sole liveness source and rejecting a second registry or string-based ownership inference.
- State terminal-only reporting and yielded neutrality directly rather than relying on readers to infer them from implementation bullets.
- Use bounded validation wording: focused and acceptance targets passed; the broad project suite was baseline/environment-limited on both refs and is not claimed green; a complete workspace suite was not run.
- Remove the draft's internal submission-metadata placeholder block before publication. GitHub will identify the final branch and comparison.
- Keep #34866 first and prominent; combine #15723 and #32188 into one wake-up/eventing distinction for brevity.
- Omit Patch 2, Patch 3, agent labels, research ancestry, internal review artifacts, and unrelated infrastructure incidents from public copy.

Likely maintainer concerns:
- Why typed creator-cell ownership is necessary instead of deriving ownership from call IDs or JavaScript values.
- Whether the manager lookup is read-only and exact-cell/live-only.
- Whether terminal disclosure changes the meaning of `Script completed` or any process lifecycle policy.
- Whether validation wording overstates the broad suite result.
- Whether the 521-line acceptance file is justified by the concurrency, truncation, one-survivor, and two-cell isolation contracts.

Deferred follow-ups:
- unreproduced cross-turn dispatch behaviour;
- shutdown/store-after-drain races;
- remote bulk-termination completion semantics;
- natural-exit stale bookkeeping;
- hidden-subagent lifecycle policy;
- event-driven wake-up after process or subagent completion;
- macOS or runtime-loss orphan recovery;
- any complete workspace validation request;
- all Patch 2 and Patch 3 planning families.

Human decisions requested:
- approve the final wording and presentation of the issue and PR;
- approve issue-first-then-PR publication order;
- approve the exact moment of external publication and cross-linking;
- decide whether any additional complete workspace validation is worth its cost, without treating it as required for the completed matched differential;
- confirm that the final related-issue search is refreshed immediately before publication if upstream state has moved.
