You are researching upstream intent and preparing an issue draft for a Codex lifecycle bug.

Repositories:
- public source and history: `openai/codex`
- implementation fork: `teamleaderleo/codex`

Baseline reference: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
Scope: public GitHub history plus a private draft. Do not publish.

Tasks:
1. Trace the changes that made unified-exec processes persist across turns or interrupts.
2. Trace code-mode nested tool calls, yielded cells, and wait/terminate behavior.
3. Find maintainer comments and possible duplicate issues involving background terminals, orphaned processes, hidden subagents, or macOS cleanup.
4. Separate intended persistence from accidental loss of visibility and ownership.
5. Draft an upstream-quality issue under 1,200 words containing impact, a network-free reproduction, expected and actual behavior, a confidence-labelled root-cause analysis, a narrow Patch 1 proposal, and separate Patch 2/Patch 3 follow-ups.
6. Phrase the implementation note to invite maintainer direction rather than demand review.

Deliver:
- chronological source summary with links or issue/PR numbers;
- likely maintainer constraints and terminology;
- duplicate candidates;
- unpublished issue draft.

Do not open or comment on any issue or PR. Do not push to `main`.