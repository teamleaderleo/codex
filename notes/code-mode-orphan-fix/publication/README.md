# Code-mode live session IDs

This directory contains the publication and review package for a standalone Codex app bug report and a narrow proposed fix.

## Documents

1. [Issue form draft](issue.md): reproduction-first bug report for the Codex app issue form
2. [Technical deep dive](deep-dive.md): data flow, implementation evidence, limitations, validation, and related reports
3. [Proposed pull-request description](pull-request.md): compact description of the intended production change
4. [Proposed #34866 cross-link comment](related-34866-comment.md): explanation of the relationship and independent scope

## Exploratory code

- Implementation branch: [`fix/code-mode-live-session-ids`](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-ids)
- Prototype head: [`77e7e3149df366236db2426596c23ebbe1d6bb48`](https://github.com/teamleaderleo/codex/commit/77e7e3149df366236db2426596c23ebbe1d6bb48)
- Selected upstream base: [`61a44880a85d2fd0d8770908dea5733495e571c8`](https://github.com/openai/codex/commit/61a44880a85d2fd0d8770908dea5733495e571c8)
- [Base-to-head comparison](https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...77e7e3149df366236db2426596c23ebbe1d6bb48)
- [Earlier executable negative reproduction](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5)

## Review state

Review edits live on `review/code-mode-issue-ready`. The exploratory implementation branch remains unchanged.

The issue-form draft still contains the local `uname -mprs` placeholder, and the #34866 comment still contains the eventual new issue-number placeholder.