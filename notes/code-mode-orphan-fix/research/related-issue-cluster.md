# Related issue cluster: live exec sessions, false completion, and orphaned children

Internal follow-up note for [openai/codex#35613](https://github.com/openai/codex/issues/35613).

This is not part of the publication package and should not be linked from the public issue unless new evidence makes a cross-link useful.

## Current publication state

- Focused issue: [#35613](https://github.com/openai/codex/issues/35613)
- Broader wrapper/process report: [#34866](https://github.com/openai/codex/issues/34866)
- A substantive scope comment linking #35613 has been posted on #34866.
- The duplicate bot suggested #34866 on #35613.
- No reply to that bot is needed unless a maintainer treats #35613 as an exact duplicate.
- Do not open the exploratory pull request without an explicit maintainer invitation.

## Failure-layer map

### 1. No wake-up after process exit

A process exits while the model is idle, but the thread is not resumed. This is a scheduling or notification problem. It does not by itself imply that a handle was never exposed or later discarded.

Representative reports include the wake-up issues referenced by #33816 and #34866.

### 2. Model loses an exposed session handle

[#33816](https://github.com/openai/codex/issues/33816) reports that the model received and initially acknowledged a live `session_id`, later asserted completion without observing an exit, and attempted another `exec_command` while the first process remained live.

Relationship to #35613: adjacent consequence, different failure point. In #33816 the handle reached the model and was then lost model-side. In #35613 nested code-mode JavaScript can discard the result object before the outer completion response exposes the handle.

Default action: do not comment unless evidence shows that the affected turn used the same nested code-mode discarded-result path.

### 3. Wrapper completion disagrees with nested process state

[#34866](https://github.com/openai/codex/issues/34866) reports that the outer code-mode wrapper can say `Script completed` while a nested shell process remains active. It asks broader lifecycle and state-representation questions.

Relationship to #35613: closest umbrella issue. #35613 isolates one independently fixable lost-handle path and does not redefine wrapper completion or nested-process lifecycle semantics.

Default action: the existing cross-link is sufficient. Do not add another comment unless a maintainer asks for clarification or new evidence changes the scope boundary.

### 4. Handle never becomes visible after nested code-mode dispatch

[#35613](https://github.com/openai/codex/issues/35613) is the focused case. JavaScript can keep only `.output`, discard nested `session_id` values, and finish while the unified-exec manager still owns the processes. Manager entries lack the creator-cell provenance needed to recover those handles for the outer status.

Proposed narrow invariant: report every manager-observed live process attributed to the exact completing code-mode cell.

### 5. Process-group or child-process orphaning

A wrapper or tracked process exits or is lost while descendants continue. This concerns ownership, process groups, cleanup, and termination semantics rather than only handle visibility.

[#35482](https://github.com/openai/codex/issues/35482) has strong symptom overlap: an outer exec result appeared complete while `zsh -> zip` remained active and continued writing to an unlinked log. However, that report also covers sandbox inspection, process-group termination, interactive EOF handling, disk quotas, and warnings.

Relationship to #35613: potentially relevant only if the incident used nested code-mode dispatch and lost the handle through the same result-discard path. #35613 would not solve the wider safety failures.

Default action: hold off on commenting. A future conditional cross-link should explicitly state what #35613 might explain and what it would not fix.

### 6. General task incompleteness or model misrepresentation

[#35035](https://github.com/openai/codex/issues/35035) reports that Codex produced a toy implementation, did not fulfil the requested task, and acted as though it had. No yielded process, live manager entry, missing handle, or wrapper/process mismatch is demonstrated.

Relationship to #35613: probably none. The duplicate-bot match appears semantic rather than diagnostic.

Default action: do not comment.

## Commenting rule

Do not add cross-links merely because two reports contain words such as `completed`, `session`, `background`, or `running`.

A comment is warranted only when it adds at least one of:

1. evidence that the same execution path was involved;
2. a precise scope distinction that the thread does not already contain;
3. a reproduction or source finding that changes diagnosis;
4. a concrete explanation of which requested behaviours the narrow fix would and would not address.

When evidence is incomplete, use conditional language. Never imply that #35613 fixes process cleanup, wake-up, sandbox observability, process-group termination, resource quotas, or model-side memory.

## Follow-up TODO

- Track maintainer responses or closure reasons on #35613 and #34866.
- Revisit #33816 only if code-mode provenance is established for its uploaded turn.
- Revisit #35482 only if the reporter or maintainer confirms nested code-mode dispatch or a discarded handle.
- Build a broader issue-triage study separately; do not use this small cluster as a representative sample of the repository.
- If invited to contribute code, derive the final PR from maintainer-approved scope rather than publishing the exploratory branch unchanged.
