# Compact five-agent plan

This plan replaces the twelve-prompt menu with a maximum of five active agents. The goal is to reduce coordination overhead while preserving independent review.

## Shared context

- Repository: `teamleaderleo/codex`
- Upstream: `openai/codex`
- Baseline commit: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
- Main implementation branch: `fix/code-mode-live-session-summary`
- Coordination branch: `research/code-mode-orphan-handoffs`
- Do not open an issue or pull request.
- Do not push to `main`.
- Distinguish confirmed behavior from inference.

## Active wave: four agents total

### Agent 1 — Integrator

This conversation owns `fix/code-mode-live-session-summary`.

Responsibilities:

- reconcile scout reports;
- write or cherry-pick the failing regression test;
- implement the smallest visibility fix;
- keep commits atomic;
- run focused formatting, lint, and tests;
- prepare the final issue draft;
- remain responsible through review and revision.

No other agent should make broad production edits on the Patch 1 branch.

### Agent 2 — Test and runtime prototype lead

Copy-paste prompt:

```text
You are the test and runtime prototype lead for a Codex bug fix.

Repository: teamleaderleo/codex
Baseline commit: 20dafe201d91d4405eef05ecd1db0257f13a9ac8
Suggested scratch branch: research/code-mode-live-session-test

Confirmed bug:
A code-mode JavaScript cell can call multiple tools.exec_command() operations. When nested commands hit yield_time_ms, each result can contain a live unified-exec session_id. JavaScript can consume only result.output, discard those IDs, and finish. The outer cell then says Script completed while nested sessions remain alive.

Tasks:
1. Trace the path from nested tools.exec_command() through ExecCommandToolOutput to the JavaScript-visible result and outer RuntimeResponse::Result.
2. Find the best existing deterministic cross-platform helper for a command that remains alive long enough to yield.
3. Implement the smallest regression test proving that two nested commands yield, JavaScript discards session_id, the outer cell completes, and current output does not surface the live sessions.
4. Make teardown terminate every spawned process even when an assertion fails.
5. Do not modify production behavior.

Deliver:
- one focused scratch-branch commit if the test is reliable;
- compact call graph with exact files and symbols;
- test command and result;
- platform concerns and teardown guarantees;
- recommendation for where the production fix should hook in.

Do not open a PR or issue. Do not merge into the Patch 1 branch.
```

This combines the former test scout, runtime data-flow scout, and regression-test prototype roles.

### Agent 3 — Ownership, API, and adjacent-defect reviewer

Copy-paste prompt:

```text
You are reviewing resource ownership and API safety around Codex code mode and unified exec.

Repository: teamleaderleo/codex
Baseline commit: 20dafe201d91d4405eef05ecd1db0257f13a9ac8
Scope: read-only.

Question:
Who owns a nested unified-exec process from spawn through yield, polling, cell completion, turn completion, session shutdown, and runtime loss?

Tasks:
1. Build a state machine for UnifiedExecProcessManager entries and code-mode cells.
2. Identify ownership transitions, cleanup triggers, and places where ownership is implicit or can be lost.
3. Evaluate the JavaScript API as a resource-handling interface: session_id naming, discarded handles, completion wording, and backwards-compatible ways to surface live sessions.
4. Audit for at most five adjacent defects in the same family: dropped task handles, ignored terminate errors, Drop-only cleanup, stale registry entries, or outer completion while nested work remains live.
5. Compare at least three Patch 1 implementation options and recommend the smallest one that changes visibility only.

Deliver under 1,800 words:
- state machine and compact call graph;
- recommended Patch 1 design;
- race and compatibility risks;
- no more than five precise adjacent findings, each with file, symbol, scenario, confidence, and test coverage.

Do not edit code or publish anything.
```

This combines ownership/lifecycle, API ergonomics, adjacent bug hunting, and free-range architecture review.

### Agent 4 — History and upstream issue editor

Copy-paste prompt:

```text
You are researching upstream intent and preparing an issue draft for a Codex lifecycle bug.

Repositories:
- public source and history: openai/codex
- implementation fork: teamleaderleo/codex
Baseline reference: 20dafe201d91d4405eef05ecd1db0257f13a9ac8
Scope: public GitHub history plus a private draft. Do not publish.

Tasks:
1. Trace the changes that made unified-exec processes persist across turns or interrupts.
2. Trace code-mode nested tool calls, yielded cells, and wait/terminate behavior.
3. Find maintainer comments and possible duplicate issues involving background terminals, orphaned processes, hidden subagents, or macOS cleanup.
4. Separate intended persistence from accidental loss of visibility and ownership.
5. Draft an upstream-quality issue under 1,200 words containing impact, network-free reproduction, expected/actual behavior, confidence-labelled root cause, narrow Patch 1 proposal, and separate Patch 2/Patch 3 follow-ups.
6. Phrase the implementation note to invite maintainer direction rather than demand review.

Deliver:
- chronological source summary with links or issue/PR numbers;
- likely maintainer constraints and terminology;
- duplicate candidates;
- unpublished issue draft.

Do not open or comment on any issue or PR.
```

This combines historical-intent research and issue drafting.

## Later wave: one additional active agent at a time

### Agent 5A — Lifecycle and macOS recovery lead

Start after Agent 2 has a reliable live-session test. This agent carries both follow-up branches through initial design so the user does not manage two separate chats.

```text
You are the follow-up lifecycle and operating-system recovery lead.

Repository: teamleaderleo/codex
Baseline commit: 20dafe201d91d4405eef05ecd1db0257f13a9ac8
Branches for later prototypes:
- fix/subagent-yielded-cell-cleanup
- fix/macos-orphan-recovery
Scope: begin read-only. Do not edit Patch 1.

Tasks:
1. Trace hidden-subagent completion, residency, eviction, thread shutdown, code-mode cell ownership, and unified-exec ownership.
2. Compare completion policies: terminate, explicit persistence opt-in, parent transfer, block completion, or warn only.
3. Preserve legitimate dev-server and watcher workflows.
4. Compare macOS recovery designs: death pipe, guardian, persisted PGID registry, startup reconciliation, and other viable mechanisms.
5. Explain PID/PGID reuse hazards and safe process identity checks.
6. Separate a reviewable Patch 2 proposal from a reviewable Patch 3 proposal.

Deliver:
- recommended hidden-subagent default and exceptions;
- ranked macOS recovery designs by safety, complexity, and testability;
- exact files and tests;
- prototype plan for each branch;
- questions requiring maintainer direction.

Do not open a PR or issue.
```

### Agent 5B — Adversarial reviewer

Agent 5B replaces Agent 5A or Agent 4 after Patch 1 has implementation commits. Do not run both unless there is a specific reason.

```text
You are the blocking reviewer for Patch 1.

Repository: teamleaderleo/codex
Base: 20dafe201d91d4405eef05ecd1db0257f13a9ac8
Head: fix/code-mode-live-session-summary

Review correctness and scope only. Look for:
- races between nested process exit and summary generation;
- stale, reused, or duplicate session IDs;
- incorrect association between cells and nested calls;
- warning text hidden by truncation;
- leaks in per-cell bookkeeping;
- behavior for Result, Yielded, Terminated, failed, cancelled, and missing cells;
- direct exec calls accidentally affected;
- flaky or leaky tests;
- unnecessary API expansion.

Deliver blocking findings first, each with a concrete scenario and suggested test. Then list non-blocking improvements. Do not rewrite or publish the patch.
```

## Recommended schedule

1. Keep this conversation as Agent 1.
2. Start Agents 2, 3, and 4 now.
3. Reconcile their reports here.
4. Land the failing test and Patch 1 implementation.
5. Replace Agent 4 with Agent 5B for review.
6. Start Agent 5A when Patch 1 is stable enough that its test machinery and terminology can support follow-up work.

At no point should more than five agents be active, including the integrator. In ordinary operation, only four are active.