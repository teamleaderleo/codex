# Patch 1 public documentation package

Status: unpublished; review branch only.

Branch: `docs/code-mode-public-package`

This package separates the maintainer-facing issue and pull request from the optional exhaustive record.

## Reading order

1. [Layered standalone issue draft](standalone-issue-layered.md)
   - problem, impact, minimal reproduction, actual/expected behaviour, scope, bounded validation, related issues;
   - intended to remain readable without opening the deep dive.

2. [Layered pull-request draft](pull-request-layered.md)
   - implementation data flow, behavioural boundaries, alternatives, test convention, focused validation;
   - insert the real issue number before publication.

3. [Public technical deep dive](public-deep-dive.md)
   - runtime and ownership model;
   - historical architecture;
   - Rust-beginner explanation;
   - threat model;
   - test evolution;
   - rejected and deferred designs;
   - validation limits and methodology.

4. [Works cited](works-cited.md)
   - classified primary and secondary sources;
   - commit-pinned code and tests;
   - executable receipts;
   - upstream history and conventions;
   - privacy boundaries.

## Publication rules

- Open the standalone issue first.
- Insert the assigned issue number into the PR body.
- Open the PR immediately afterward from `teamleaderleo:fix/code-mode-live-session-summary-clean`.
- Cross-link the issue and PR.
- Treat `#34866` as related prior symptom coverage, not as a substitute for the standalone issue.
- Do not paste private logs, raw chats, machine paths, user data, agent identities, research branches, or launcher troubleshooting into the upstream issue or PR.
- Do not call the defect a literal Rust memory leak.
- Do not claim the broad `codex-core` suite or complete workspace suite passed.
- Pin all documentation links to an immutable commit before publication.
- Upstream publication requires explicit human approval.

## Human-authored layer

The human coordinator may add or replace the opening two paragraphs in the issue with a first-person synthesis. That synthesis should remain concise and should not claim that AI-generated prose is independently human-authored.

Suggested conceptual core:

> Code mode did not lose the processes internally; it lost the model-visible session IDs needed to control them. This patch preserves the existing creator-cell association and reports the exact still-live session IDs when that cell finishes, without changing process-lifecycle policy.

The operational incident and any measured resource use should be stated only to the level supported by preserved evidence or clearly labelled first-person recollection.