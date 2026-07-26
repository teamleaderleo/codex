# Patch 1 public documentation package

Status: unpublished; final review package.

This package keeps the code candidate separate from the publication documents.

## Canonical branches

### Code-only PR candidate

- Branch: [`fix/code-mode-live-session-summary-clean`](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-summary-clean)
- Head: [`760216784efaee1ba6a3b1250349f31d5f91c7ca`](https://github.com/teamleaderleo/codex/commit/760216784efaee1ba6a3b1250349f31d5f91c7ca)
- Upstream base: [`61a44880a85d2fd0d8770908dea5733495e571c8`](https://github.com/openai/codex/commit/61a44880a85d2fd0d8770908dea5733495e571c8)
- [Exact comparison](https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...760216784efaee1ba6a3b1250349f31d5f91c7ca)

This branch contains only the focused production and test changes. It contains no investigation notes, publication drafts, raw logs, or research history.

For a fork-based pull request, the branch name remains `fix/code-mode-live-session-summary-clean`. GitHub will display the head as `teamleaderleo:fix/code-mode-live-session-summary-clean`; the username should not be embedded in the branch name.

### Documentation and publication package

- Branch: `docs/code-mode-public-package`
- Directory: `notes/code-mode-orphan-fix/publication-drafts/`

This branch contains the readable issue, PR proposal, plain-language synthesis, deep dive, and works-cited index. These documents are not part of the code candidate and should not be merged into the production PR.

## Core deliverables

1. [Plain-language summary](plain-language-summary.md)
   - a short, readable explanation of the failure, fix, boundaries, impact, and validation;
   - suitable for human editing or adoption without requiring Rust knowledge.

2. [Polished standalone issue proposal](standalone-issue-layered.md)
   - problem, impact, minimal reproduction, actual and expected behaviour, visibility-only boundary, bounded validation, and related issues;
   - independently understandable without opening the deep dive.

3. [PR-ready technical proposal](pull-request-layered.md)
   - implementation data flow, behavioural boundaries, alternatives, test convention, focused validation, and immutable code links;
   - replace `#ISSUE_NUMBER` only after the issue exists.

4. [Public technical deep dive](public-deep-dive.md)
   - runtime and ownership model;
   - historical architecture;
   - detailed code explanation;
   - threat model and limitations;
   - test evolution and rejected designs.

5. [Works cited](works-cited.md)
   - primary code and test sources;
   - executable-result summaries;
   - upstream history and conventions;
   - secondary synthesis and privacy boundaries.

## Publication sequence

The current upstream contribution guide says external code contributions are by invitation only and that uninvited pull requests will be closed without review. Re-check the [current guide](https://github.com/openai/codex/blob/main/docs/contributing.md) immediately before publication.

1. Publish the standalone issue after explicit human approval.
2. Use the issue to present the reproduction, evidence, and proposed narrow solution.
3. Do **not** open the upstream PR unless a Codex maintainer explicitly invites the contribution.
4. If invited, insert the issue number into the PR body and open the PR from `teamleaderleo:fix/code-mode-live-session-summary-clean` to `openai/codex:main`.
5. A draft PR is technically possible, but it should still be opened only after invitation. Mark it ready for review only when the branch is mergeable and the requested checks are current.
6. Cross-link the issue and PR if the PR is opened.

A draft PR against the fork's own `main` would create a public rehearsal object but would not improve the upstream submission. The Markdown PR proposal in this package is the cleaner pre-invitation review artifact.

## Public-copy rules

- Treat `#34866` as related prior symptom coverage, not as a substitute for the standalone issue.
- Do not paste private logs, raw chats, machine paths, user data, agent identities, research branches, or launcher troubleshooting into the upstream issue or PR.
- Do not call the defect a literal Rust memory leak.
- Do not assign a security severity without evidence.
- Do not imply automatic process cleanup or a lifecycle-policy change.
- Do not claim the broad `codex-core` suite or complete workspace suite passed.
- Pin evidence links to immutable commits where the cited content must not move.
- Upstream publication requires explicit human approval.

## Human wording layer

The plain-language summary is a reviewable synthesis, not a claim that its current wording is already the human coordinator's personal account. The human coordinator may edit or explicitly adopt it before using it publicly.

Operational incidents and measured resource use should be stated only to the level supported by preserved evidence or clearly labelled first-person recollection.
