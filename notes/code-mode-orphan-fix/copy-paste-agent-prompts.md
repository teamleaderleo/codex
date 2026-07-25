# Copy-paste agent prompts

These prompts are designed for separate ChatGPT/Codex sessions working against `teamleaderleo/codex`.

Shared baseline:

- Repository: `teamleaderleo/codex`
- Upstream: `openai/codex`
- Baseline commit: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
- Main implementation branch: `fix/code-mode-live-session-summary`
- Coordination branch: `research/code-mode-orphan-handoffs`
- Do not open an issue or pull request.
- Do not push to `main`.
- Keep reports concise and distinguish confirmed behavior from inference.

## Prompt 1 — Patch 1 test scout

You are the test scout for a Codex bug fix.

Repository: `teamleaderleo/codex`
Baseline commit: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
Scope: read-only unless you create a clearly named scratch branch.

Confirmed bug:
A code-mode JavaScript cell can call multiple `tools.exec_command()` operations. When nested commands hit `yield_time_ms`, each result can contain a live unified-exec `session_id`. JavaScript can consume only `result.output`, discard those IDs, and finish. The outer cell then says `Script completed` while nested sessions remain alive.

Task:
1. Inspect existing code-mode and unified-exec tests.
2. Find the best deterministic cross-platform helper for a command that stays alive long enough to yield.
3. Design a regression test that recreates two yielded nested sessions inside `Promise.all`, discards their IDs, and proves the outer cell completes.
4. Specify safe teardown so no process survives a failed test.
5. Prefer existing fixtures over new binaries.

Deliver:
- proposed test name;
- exact test file and insertion area;
- helper/fixture choice;
- test code sketch;
- assertions before and after the proposed fix;
- platform concerns;
- commands to run the focused test.

Do not implement the production fix. Do not open a PR or issue.

## Prompt 2 — Runtime data-flow scout

You are tracing the smallest viable implementation for a Codex code-mode lifecycle bug.

Repository: `teamleaderleo/codex`
Baseline commit: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
Scope: read-only.

Trace this path precisely:
1. code-mode JavaScript invokes nested `tools.exec_command()`;
2. unified exec creates `ExecCommandToolOutput`;
3. that output becomes the JavaScript-visible object containing `session_id`;
4. JavaScript finishes while the session remains live;
5. the outer runtime becomes `RuntimeResponse::Result` and displays `Script completed`;
6. process-manager state remains available.

Task:
- produce a compact call graph with files, types, and key functions;
- identify where the originating `CellId` is available;
- identify where live session IDs can be recorded without parsing arbitrary JavaScript output;
- identify how to check whether an ID is still live when the outer result is generated;
- compare at least three implementation options;
- recommend the smallest change that only improves visibility and does not alter background-process persistence policy.

Pay special attention to races where a session exits between recording and reporting.

Deliver a report under 1,500 words. Do not edit code or open a PR/issue.

## Prompt 3 — Unified-exec ownership and lifecycle scout

You are investigating resource ownership in Codex unified exec.

Repository: `teamleaderleo/codex`
Baseline commit: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
Scope: read-only.

Question:
Who owns a unified-exec process from spawn through yield, polling, termination, turn completion, session shutdown, and runtime loss?

Inspect:
- `UnifiedExecProcessManager` and process store;
- process registration and release;
- `terminate_process` and `terminate_all_processes`;
- code-mode nested calls;
- turn/task cancellation;
- session shutdown;
- background-terminal cleanup;
- process events and persisted process metadata.

Deliver:
- a state machine for a process;
- ownership transitions and cleanup triggers;
- places where ownership is implicit or can be lost;
- whether the Patch 1 visibility proposal fits existing abstractions;
- adjacent lifecycle defects worth filing separately;
- exact symbols and tests relevant to each claim.

Do not propose a giant redesign. Separate confirmed bugs from suspicious edges.

## Prompt 4 — Code-mode API ergonomics reviewer

You are reviewing the JavaScript API contract exposed by Codex code mode.

Repository: `teamleaderleo/codex`
Baseline commit: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
Scope: read-only.

Confirmed incident:
`tools.exec_command()` returned live `session_id` values after yielding. User JavaScript printed only `.output`, so the handles disappeared. The outer cell later displayed `Script completed`.

Task:
Evaluate the API as a resource-handling interface, not only as JSON serialization.

Consider:
- whether `session_id` is named clearly enough;
- whether live sessions should be represented as explicit resources/handles;
- whether an outer cell should summarize unconsumed live resources;
- whether runtime warnings should depend on whether JavaScript reads a field;
- whether helper APIs such as `using`, scoped cleanup, or explicit persistence could help;
- compatibility with existing code-mode scripts.

Deliver:
- current contract as inferred from source/tests;
- dangerous but valid usage patterns;
- a minimal backwards-compatible improvement;
- one medium-term API improvement;
- tests or documentation changes needed.

Do not implement code. Avoid speculative language where source evidence is available.

## Prompt 5 — Cross-platform process semantics scout

You are comparing process-lifetime behavior across macOS, Linux, and Windows for Codex unified exec.

Repository: `teamleaderleo/codex`
Baseline commit: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
Scope: read-only.

Known macOS incident:
Detached Playwright process groups survived after their Codex owner disappeared and were adopted by PID 1. Linux has a parent-death-signal path; macOS does not.

Task:
- inspect PTY/process-group creation and termination code;
- document platform-specific behavior;
- verify which cleanup guarantees exist only during graceful Rust drop/shutdown;
- identify robust macOS options: death pipe, guardian, persisted PGID registry, launch-time reconciliation, or another approach;
- explain PID/PGID reuse hazards and process identity checks;
- identify what can be tested in CI and what requires a macOS integration test.

Deliver a design comparison, not production code. Rank proposals by safety, complexity, and reviewability.

## Prompt 6 — Hidden subagent lifecycle policy scout

You are investigating how Codex hidden subagents interact with yielded code-mode cells and background terminals.

Repository: `teamleaderleo/codex`
Baseline commit: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
Scope: read-only.

Confirmed incident:
A subagent turn completed after a code-mode cell had spawned live background sessions. The original work was retried and the old sessions were never terminated.

Task:
Trace:
- subagent creation and residency;
- completed/interrupted/errored subagent handling;
- task completion;
- thread shutdown and eviction;
- ownership of code-mode cells and unified-exec sessions;
- parent/child agent relationships.

Compare policies:
1. terminate live cells when a hidden subagent completes;
2. require explicit persistence opt-in;
3. transfer ownership to the parent agent;
4. block completion while resources remain;
5. warn only.

Preserve legitimate dev-server and watcher workflows.

Deliver:
- exact lifecycle call graph;
- recommended default for hidden subagents;
- exceptions/opt-ins required;
- regression tests;
- migration and compatibility risks.

Do not edit Patch 1.

## Prompt 7 — Adjacent bug hunter

You are doing a bounded audit for bugs in the same family as a confirmed Codex code-mode resource leak.

Repository: `teamleaderleo/codex`
Baseline commit: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
Scope: read-only and exploratory.

Theme:
Resources outlive the scope that created them because ownership, completion, cancellation, or cleanup is implicit.

Search for analogous patterns involving:
- spawned tasks whose handles are dropped;
- cancellation branches that abort without teardown;
- process IDs or cell IDs returned but easy to discard;
- `Drop`-only cleanup that fails on abrupt owner exit;
- errors ignored from kill/terminate operations;
- maps/stores whose entries survive after the underlying resource changes state;
- outer operations reporting completion while nested work remains live;
- MCP, browser, PTY, code-mode, subagent, and app-server resources.

Deliver no more than five findings. For each include:
- file and symbol;
- concrete failure scenario;
- confidence level;
- whether an existing test covers it;
- whether it belongs in the current issue or a separate one.

Do not report vague code smells. Every finding needs an executable or logically precise scenario.

## Prompt 8 — Historical intent and upstream-direction scout

You are researching the intended behavior behind Codex background terminals and code-mode cells.

Repository: `openai/codex`
Baseline reference: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
Scope: public GitHub history, issues, PRs, commits, and current source.

Task:
- trace changes that made unified-exec processes persist across turns or interrupts;
- trace changes that introduced code-mode nested tool calls and yielded cells;
- find maintainer comments explaining desired behavior;
- identify open or closed issues about orphaned processes, subagents, background terminals, or macOS cleanup;
- infer likely maintainer constraints for a Patch 1 visibility fix.

Deliver:
- chronological summary with links/IDs;
- explicit intended behavior versus accidental behavior;
- terminology used by maintainers;
- advice for framing the upstream issue;
- potential duplicate issues.

Use primary GitHub sources. Do not open or comment on anything.

## Prompt 9 — Regression-test prototype agent

You are allowed to create a scratch branch containing only a failing regression test or test helper.

Repository: `teamleaderleo/codex`
Baseline commit: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
Suggested scratch branch: `research/code-mode-live-session-test`

Task:
Implement the smallest deterministic test that proves:
1. a code-mode JavaScript cell starts two nested commands;
2. both nested commands yield and remain live;
3. JavaScript consumes only `.output` and discards `session_id`;
4. the outer cell completes;
5. current model-facing output does not surface the live sessions;
6. teardown terminates everything even when an assertion fails.

Requirements:
- reuse existing cross-platform helpers where possible;
- no Playwright or network access;
- no changes to production behavior;
- one focused commit;
- run formatting and the narrowest useful test command;
- report any flakiness or platform assumptions.

Do not merge into Patch 1. Push the scratch branch only if the test is clean enough to cherry-pick.

## Prompt 10 — Issue evidence editor

You are preparing an upstream-quality bug report, but you must not publish it.

Repository context: `openai/codex`
Implementation fork: `teamleaderleo/codex`
Baseline commit: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`

Confirmed evidence:
- code-mode cell launched two Playwright screenshot commands and one curl in `Promise.all`;
- each nested exec used `yield_time_ms: 30000`;
- outer cell first yielded, then a `wait` returned `Script completed` at the nested yield boundary;
- nested results had live session IDs, while JavaScript printed only `.output`;
- replacement commands later succeeded;
- the original two process groups survived for days on macOS under PID 1;
- local process metadata tied them to Codex Desktop, the conversation, commands, and working directory.

Task:
Draft an issue containing:
- concise title;
- impact;
- minimal network-free reproduction;
- expected and actual behavior;
- precise root-cause hypothesis with confidence labels;
- proposed narrow Patch 1 behavior;
- separate follow-up areas for subagent lifecycle and macOS recovery;
- privacy-safe evidence summary;
- invitation-friendly implementation note.

Keep it respectful, technically dense, and under roughly 1,200 words. Do not publish it.

## Prompt 11 — Adversarial Patch 1 reviewer

Use this only after `fix/code-mode-live-session-summary` has implementation commits.

You are the blocking reviewer for Patch 1.

Repository: `teamleaderleo/codex`
Base: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
Head: `fix/code-mode-live-session-summary`

Task:
Review only correctness and scope. Look for:
- races between nested process exit and summary generation;
- stale or reused session IDs;
- duplicate IDs;
- incorrect association between cells and nested calls;
- warning text hidden by truncation;
- leaks in per-cell bookkeeping;
- behavior for Result, Yielded, Terminated, failed, cancelled, and missing cells;
- direct exec calls accidentally affected;
- flaky or leaky tests;
- unnecessary API expansion.

Deliver blocking findings first, each with a concrete scenario and suggested test. Then list non-blocking improvements. Do not rewrite the patch unless explicitly asked.

## Prompt 12 — Free-range architecture scout

You are the intentionally open-ended scout. Explore the Codex repository for anything that changes how we should understand or fix this incident.

Repository: `teamleaderleo/codex`
Baseline commit: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
Scope: read-only.

Start from these concepts:
- resource ownership;
- nested asynchronous work;
- yielded code cells;
- background terminals;
- subagent residency;
- process-manager persistence;
- abrupt runtime loss.

You may follow adjacent code paths that seem relevant. Your job is to find surprising constraints, existing abstractions we should reuse, or a simpler explanation/fix than the current proposal.

Guardrails:
- do not repeat the known call graph unless it supports a new conclusion;
- no more than three major findings;
- cite exact files and symbols;
- label speculation;
- explain how each finding changes Patch 1, Patch 2, Patch 3, or the upstream issue.

Do not edit code or publish anything.
