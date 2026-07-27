# Code-mode lost-handle publication handoff

This branch contains the clean public-facing package for the standalone issue.

## Publication order

1. Open [issue.md](issue.md) as a new upstream issue.
2. Replace `#<new-issue>` in [related-34866-comment.md](related-34866-comment.md) with the assigned number and post it on [#34866](https://github.com/openai/codex/issues/34866).
3. Use the issue discussion to settle the terminal-response and exec-server liveness questions.
4. Open [pull-request.md](pull-request.md) only after a Codex maintainer invites the contribution.

## Why this is a separate issue

[#34866](https://github.com/openai/codex/issues/34866) covers the broader mismatch between wrapper completion and nested-process state and proposes richer lifecycle representation.

This issue isolates one smaller invariant: when code-mode JavaScript discards a nested command result, the completing cell loses the model-visible `session_id` even though the unified-exec manager still owns the live process.

The focused proposal restores those existing handles through a manager lookup. It changes no lifecycle policy or public protocol fields, so it can be evaluated independently from the broader redesign.

## Public drafts

- [Standalone issue](issue.md)
- [Cross-link comment for #34866](related-34866-comment.md)
- [Invited PR draft](pull-request.md)
- [Concise summary](summary.md)

## Technical archive

- [Deep dive](deep-dive.md)
- [Validation record](validation.md)
- [Sources](sources.md)

The archive supports factual review. The upstream issue should stand on its own without requiring maintainers to read the archive.

## Prototype status

- Prototype branch: [`fix/code-mode-live-session-ids`](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-ids)
- Prototype head: [`77e7e3149df366236db2426596c23ebbe1d6bb48`](https://github.com/teamleaderleo/codex/commit/77e7e3149df366236db2426596c23ebbe1d6bb48)
- Selected base: [`61a44880a85d2fd0d8770908dea5733495e571c8`](https://github.com/openai/codex/commit/61a44880a85d2fd0d8770908dea5733495e571c8)
- Verified upstream snapshot: [`95637f7056835fea66bdd0044414af480fc0fd74`](https://github.com/openai/codex/commit/95637f7056835fea66bdd0044414af480fc0fd74)

The verified upstream snapshot is five commits ahead of the selected base. Those commits do not touch the four production files changed by the prototype, so the design requires a clean rebase rather than adaptation.

## Before an invited PR

Create a smaller branch directly from then-current upstream `main` and carry only:

- the production provenance and manager lookup;
- focused manager and formatter tests;
- the primary discarded-handle end-to-end regression.

Apply these code cleanups during that rebase:

- convert the code-mode source ID with `cell_id.as_str().to_string()` instead of relying on `Display`;
- keep numeric ordering in one layer, preferably the formatter, and remove the manager's duplicate sort;
- omit the Wine-only routing commit and Wine validation narrative;
- record the accepted `Result` / failed `Result` / `Terminated` boundary from the issue discussion;
- document that exec-server liveness reflects manager-cached exit state.

Run every claimed check on the same final rebased SHA and place only that final record in the PR.