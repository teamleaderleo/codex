# Code-mode lost-handle issue package

This branch contains the finished issue material and the technical record behind it.

## Public drafts

- [Standalone issue](issue.md)
- [Cross-link comment for #34866](related-34866-comment.md)

The cross-link has one unavoidable placeholder, `#<new-issue>`, which gets replaced with the standalone issue number.

## Supporting material

- [Technical deep dive](deep-dive.md)
- [Prototype validation](validation.md)
- [Sources](sources.md)
- [Concise summary](summary.md)
- [Implementation draft](pull-request.md)

The issue stands on its own. The deep dive is linked once at the bottom for readers who want the implementation reasoning and evidence.

## Branch roles

- [`review/code-mode-issue-ready`](https://github.com/teamleaderleo/codex/tree/review/code-mode-issue-ready/notes/code-mode-orphan-fix/publication) contains the issue and supporting documents.
- [`fix/code-mode-live-session-ids`](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-ids) is the exploratory implementation branch and includes its tests.

There isn't a separate test branch that needs to be linked. The validation record points to historical commits and workflow runs only where a specific result depends on them.

The implementation branch name is clear enough to keep: it says what the code does, while the deep dive labels the work as exploratory. Renaming it now would add another ref without improving the technical record.

## Prototype refs

- [Exploratory head `77e7e314`](https://github.com/teamleaderleo/codex/commit/77e7e3149df366236db2426596c23ebbe1d6bb48)
- [Selected base `61a44880`](https://github.com/openai/codex/commit/61a44880a85d2fd0d8770908dea5733495e571c8)
- [Verified upstream snapshot `95637f70`](https://github.com/openai/codex/commit/95637f7056835fea66bdd0044414af480fc0fd74)

The verified upstream snapshot is five commits ahead of the selected base and changes none of the four production files touched by the prototype.

Four acceptance cases exercised the Docker remote executor. The exited-process/survivor case ran locally only, so remote stale-exit behaviour remains untested.
