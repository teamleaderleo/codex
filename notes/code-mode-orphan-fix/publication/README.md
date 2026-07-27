# Code-mode live session IDs

This directory contains the final review package for Patch 1.

## Start here

1. [Final review handoff](review.md)
2. [Summary](summary.md)
3. [Standalone issue draft](issue.md)
4. [Pull-request draft](pull-request.md)

The issue is reproduction-first. The pull-request draft follows a compact Why / What changed / Testing / Notes structure.

## Technical reference

- [Deep dive](deep-dive.md): implementation reasoning, current-upstream adaptation, and non-goals
- [Sources](sources.md): code, tests, history, related reports, and upstream context
- [Validation](validation.md): exact refs, commands, passes, blocked paths, and limitations

## Code

- Branch: [`fix/code-mode-live-session-ids`](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-ids)
- Current head: [`77e7e3149df366236db2426596c23ebbe1d6bb48`](https://github.com/teamleaderleo/codex/commit/77e7e3149df366236db2426596c23ebbe1d6bb48)
- Selected upstream base: [`61a44880a85d2fd0d8770908dea5733495e571c8`](https://github.com/openai/codex/commit/61a44880a85d2fd0d8770908dea5733495e571c8)
- [Base-to-current comparison](https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...77e7e3149df366236db2426596c23ebbe1d6bb48)

## Review status

This package is ready for coordinated final review on the fork. Nothing has been opened upstream. The issue should be considered first, and the pull request should be opened only after an upstream maintainer invites the contribution. Review changes should land on `review/code-mode-final-draft`; the code branch should remain focused on Patch 1 implementation and tests.
