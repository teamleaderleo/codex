# Code-mode lost-handle issue package

This branch contains the finished issue material and its supporting technical record.

## Publication drafts

- [Standalone issue](issue.md)
- [Cross-link comment for #34866](related-34866-comment.md)

The cross-link has one unavoidable placeholder, `#<new-issue>`, which is replaced with the standalone issue number after it is created.

## Supporting record

- [Technical deep dive](deep-dive.md)
- [Prototype validation](validation.md)
- [Sources](sources.md)
- [Concise summary](summary.md)
- [Implementation draft](pull-request.md)

The standalone issue is self-contained. The deep dive is linked once at the bottom as optional supporting evidence.

## Prototype refs

- Branch: [`fix/code-mode-live-session-ids`](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-ids)
- Head: [`77e7e3149df366236db2426596c23ebbe1d6bb48`](https://github.com/teamleaderleo/codex/commit/77e7e3149df366236db2426596c23ebbe1d6bb48)
- Selected base: [`61a44880a85d2fd0d8770908dea5733495e571c8`](https://github.com/openai/codex/commit/61a44880a85d2fd0d8770908dea5733495e571c8)
- Verified upstream snapshot: [`95637f7056835fea66bdd0044414af480fc0fd74`](https://github.com/openai/codex/commit/95637f7056835fea66bdd0044414af480fc0fd74)

The verified upstream snapshot is five commits ahead of the selected base and changes none of the four production files touched by the prototype.

Four acceptance cases exercised the Docker remote executor. The exited-process/survivor case ran locally only, so remote stale-exit behaviour remains untested.