# Final Patch 1 publication-readiness review

Date: 2026-07-26

## Verdict

**Ready for human wording review and explicit publication approval.**

No upstream issue or pull request has been published.

## Canonical code state

- Upstream base: `61a44880a85d2fd0d8770908dea5733495e571c8`
- Final clean candidate: `760216784efaee1ba6a3b1250349f31d5f91c7ca`
- Canonical branch: `fix/code-mode-live-session-summary-clean`
- Comparison: `61a44880a85d2fd0d8770908dea5733495e571c8...760216784efaee1ba6a3b1250349f31d5f91c7ca`
- Upstream `openai/codex` `main` was rechecked immediately before this review and remained identical to the selected base.

## Final agent results

### Agent 1

Final short contract sanity check: **pass**.

Confirmed:

- multiple discarded live sessions are reported once each in numeric order;
- exited sessions are excluded;
- the warning remains separate from emitted-output truncation;
- yielded responses remain free of the terminal-only warning;
- only sessions created by the completing cell are reported;
- the direct manager-query unit test covers exact-cell matching, another-cell exclusion, `None` exclusion, exited-entry exclusion, and numeric ordering.

No code change, test change, or public-copy correction was requested.

Agent 1 handoff commit: `3dd992136e5a3403542d8d0e85ba40b2f243d9cf`.

### Agent 4

Final standalone issue and pull-request drafts: **pass with one editorial correction applied**.

The original wording said that the aggregate harness "verifies" cleanup across success, returned errors, and panics. The five acceptance cases do not deliberately trigger all three paths. The drafts now state the precise structural fact: the harness uses cleanup protection that runs after success, returned errors, and panics while preserving an original panic.

Final draft paths:

- `notes/code-mode-orphan-fix/publication-drafts/standalone-issue.md`
- `notes/code-mode-orphan-fix/publication-drafts/pull-request.md`

Editorial correction commits:

- issue draft: `ac224f8366e76d2fd0314661495c013cf0308cb6`
- PR draft: `f1c252940fb61eb50480d83fa802d4ff87d570ba`

## Display-cardinality position

Patch 1 will retain the complete point-in-time list returned by the exact-cell, live-only manager query. It will not introduce a separate display-cardinality cap in this patch.

Rationale:

- the purpose of Patch 1 is to preserve model-visible control handles;
- truncating the list would knowingly omit some currently live handles;
- the manager has a normal process bound, even though that bound can be temporarily soft while locked exited entries finish publication;
- the complete tool result remains subject to the existing later global conversation-history limits;
- no process pruning or lifecycle policy should be changed to solve a presentation-only concern.

The public drafts explicitly state the later global-history-limit caveat. A maintainer-requested display cap can be evaluated during review without pre-emptively broadening the submitted patch.

## Publication strategy

1. Publish the standalone issue.
2. Insert the assigned issue number into the PR body with `Fixes #<number>`.
3. Open the PR immediately from `teamleaderleo:fix/code-mode-live-session-summary-clean`.
4. Add the PR URL to the issue and verify reciprocal links.
5. Treat `openai/codex#34866` as related prior symptom coverage, not as the canonical issue or a substitute for the standalone issue.

## Remaining human gates

- approve or edit the issue title and body;
- approve or edit the PR title and body;
- explicitly approve issue-first-then-PR publication;
- approve the exact publication moment.

The broad `codex-core` suite remains baseline/environment-limited and red on both compared refs. The complete workspace suite was not run. Neither may be described as green.
