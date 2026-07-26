# Agent 4 publication handoff

Date: 2026-07-26

## Status

- The standalone upstream issue and pull request remain unpublished.
- Final clean candidate: `760216784efaee1ba6a3b1250349f31d5f91c7ca`
- Upstream base: `61a44880a85d2fd0d8770908dea5733495e571c8`
- Canonical branch: `fix/code-mode-live-session-summary-clean`
- Clean comparison: `61a44880a85d2fd0d8770908dea5733495e571c8...760216784efaee1ba6a3b1250349f31d5f91c7ca`

## Shared publication drafts

The final reviewable proposals now live in separate shared Markdown files:

- Standalone issue: `notes/code-mode-orphan-fix/publication-drafts/standalone-issue.md`
- Pull request: `notes/code-mode-orphan-fix/publication-drafts/pull-request.md`

These files contain the proposed titles, complete public bodies, related-work wording, validation boundaries, and publication-time cross-link instructions.

## Publication strategy

1. Open the standalone issue first.
2. Treat openai/codex#34866 only as related prior symptom coverage.
3. Add the assigned standalone issue number to the PR body with a `Fixes` line.
4. Open the PR immediately afterward from `teamleaderleo:fix/code-mode-live-session-summary-clean`.
5. Add the PR URL to the issue and verify reciprocal links in the same working session.

## Final wording and evidence state

The drafts:

- use “stored live process entries” and “session-level unified-exec process manager”;
- use “session ID” for model-facing behaviour;
- mark numeric example IDs as illustrative;
- explain that the warning is outside code-mode emitted-output truncation but remains subject to later global history limits;
- state that no lifecycle, termination, pruning, recovery, protocol, or JavaScript-schema policy changed;
- report four focused unit tests and five aggregate acceptance cases as passed;
- report compatibility results as `20/20` on the final candidate and `20/20` on the exact upstream base;
- retain the baseline-red caveat for the broad `codex-core` run;
- state explicitly that the complete workspace suite was not run;
- omit agent identities, research ancestry, machine paths, raw logs, launcher troubleshooting, and unrelated follow-up planning.

## Related-issue position

- openai/codex#34866: related prior symptom coverage, not the canonical issue and not a substitute for the standalone issue.
- openai/codex#32411: broader un-emitted nested results and artifact handles.
- openai/codex#33816: abandonment after a session ID was already exposed.
- openai/codex#14731, #15723, and #32188: lifecycle blocking or wake-up/eventing, outside this visibility-only change.

## Human approval still required

- final public tone and title choices;
- exact publication moment;
- explicit approval to execute issue-first-then-PR;
- insertion of the actual issue number and reciprocal links at publication time.

## Reconvene point

Review the two files under `publication-drafts/` rather than reconstructing copy from investigation notes. No upstream issue, comment, or pull request has been created.