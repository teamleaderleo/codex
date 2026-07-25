# Agent 4 report: public history, duplicate scan, and unpublished issue draft

## Scope

- Public source of truth: [`openai/codex`](https://github.com/openai/codex)
- Implementation fork: [`teamleaderleo/codex`](https://github.com/teamleaderleo/codex)
- Baseline reviewed: [`20dafe201d91d4405eef05ecd1db0257f13a9ac8`](https://github.com/openai/codex/commit/20dafe201d91d4405eef05ecd1db0257f13a9ac8)
- Research date: 2026-07-26
- Publication status: private draft only. No issue, comment, or pull request was published.

## Executive conclusion

Cross-turn persistence of unified-exec processes is deliberate. The defect is the loss of visibility and control when a code-mode JavaScript cell receives a live nested `session_id`, discards that field, and then returns successfully. The outer result reports `Script completed` because the JavaScript cell ended; it does not summarize nested background terminals that remain live.

A narrow Patch 1 can preserve the intended persistence policy: track typed live session IDs per code-mode `CellId`, verify liveness at cell completion, and include surviving IDs in the outer status header. Turn/subagent ownership and macOS owner-loss recovery belong in separate follow-ups.

A near-exact public issue now exists: [#34866](https://github.com/openai/codex/issues/34866). Publishing a new standalone issue would likely create a duplicate. The unpublished draft below is best used as a proposed supplement to #34866 or as a new issue only after maintainer direction.

## Chronological public-source summary

### 1. Unified exec introduced resumable process sessions

- [PR #3288 — Unified execution](https://github.com/openai/codex/pull/3288) introduced the unified execution path with PTY-backed commands, bounded initial waits, buffered output, and resumable live sessions.
- The core contract became: a command that exits returns an exit code; a command still running returns a process/session handle that can be resumed.
- This is the origin of intentional background process persistence, rather than an accidental leak by itself.

### 2. Codex began owning process groups, with a Linux-only owner-death guard

- [PR #5258 — Kill shell tool process groups on timeout](https://github.com/openai/codex/pull/5258) moved shell commands into their own Unix process groups and killed the group on timeout or interruption so grandchildren could not keep the PTY open.
- The same path retained Linux `PR_SET_PDEATHSIG` handling. Current `spawn.rs` explicitly says the parent-death signal relies on Linux `prctl(2)`; macOS receives process-group detachment without the kernel owner-death signal.
- This history supports a separate macOS recovery track: graceful group termination exists, while abrupt runtime loss still has a Darwin gap.

### 3. Turn completion initially terminated unified-exec sessions

- [PR #8052 — close unified_exec at end of turn](https://github.com/openai/codex/pull/8052) added cleanup when the active turn completed or was aborted.
- A maintainer requested a long-running-process regression test with event assertions around the task-completion boundary. Review also favoured a no-op-safe cleanup method over extra conditionals.
- This establishes two review expectations: lifecycle tests should assert event ordering, and cleanup APIs should stay small and idempotent.

### 4. Interrupt became an explicit cleanup boundary

- [PR #8786 — clear background terminals on interrupt](https://github.com/openai/codex/pull/8786) made user interruption a clear terminal cleanup action.
- The project terminology around this period settled on **background terminals**.

### 5. Turn-end cleanup was deliberately reversed

- [PR #10799 — do not close unified exec processes across turns](https://github.com/openai/codex/pull/10799) intentionally preserved background terminals after normal turn completion.
- The retained cleanup boundaries were:
  - user interrupt;
  - explicit thread-level clean via experimental `thread/backgroundTerminals/clean` and `/clean`;
  - session/runtime shutdown, including `codex exec` shutdown.
- Its regression test asserts that a long-running process remains alive after `TurnComplete`, then exits during shutdown.
- Patch 1 therefore should avoid automatic termination at code-cell or turn completion. Such a change would reverse an explicit product decision.

### 6. Code mode gained nested tools and a turn-scoped dispatch worker

- [PR #14167 — Export tools module into code mode runner](https://github.com/openai/codex/pull/14167) exposed nested tools to JavaScript through `tools.js`.
- [PR #14437 — Dispatch tools when code mode is not awaited directly](https://github.com/openai/codex/pull/14437) started a code-mode worker once per turn and routed nested tool calls through a queue so cells could continue running after the initial `exec` response.
- Review on #14437 observed that “yield” behaves more like detaching focus/backgrounding, and flagged head-of-line blocking for concurrent JavaScript tool calls. The author response was: keep individual changes small and address concurrency separately.
- [PR #14494 — Add parallel tool call test](https://github.com/openai/codex/pull/14494) added coverage for concurrent nested calls.
- [PR #14496 — Reuse tool runtime for code mode worker](https://github.com/openai/codex/pull/14496) reused the turn-scoped `ToolCallRuntime` and router for nested tool calls.

### 7. Current baseline exposes the visibility gap

At the reviewed baseline:

- `ExecCommandToolOutput::code_mode_result` serializes a still-running unified-exec process as typed JSON with `session_id`.
- `call_nested_tool` returns that JSON to JavaScript and carries `ToolCallSource::CodeMode { cell_id, runtime_tool_call_id }` during dispatch.
- JavaScript may read only `result.output`, so the `session_id` can disappear without warning.
- `handle_runtime_response` formats any successful terminal JavaScript `RuntimeResponse::Result` as `Script completed`.
- No per-cell bookkeeping aggregates surviving nested `session_id` values into the terminal cell status.
- Unified exec stores live processes before the initial yield wait specifically so interruption of the current call cannot drop the final process reference.

This is the exact split between intended persistence and accidental handle loss.

## Confidence-labelled root-cause assessment

### High confidence: Patch 1 defect

1. A live nested unified-exec command returns `session_id` as typed data.
2. JavaScript can discard that data while still completing successfully.
3. The outer status describes JavaScript completion only.
4. No code-mode per-cell summary reports surviving background terminals.

Result: the process remains controllable inside the unified-exec manager, while the agent-visible code-cell result can lose the only handle needed to poll or terminate it.

### Medium confidence: Patch 2 ownership hazard

Code-mode cells are session-lived, while nested dispatch uses a turn-scoped worker and turn-scoped tool runtime. Hidden subagent completion can therefore leave a live cell or terminal whose original user-visible owner has completed. Existing public reports show adjacent failures in parent wake-up and subagent visibility. Exact ownership-transfer semantics require a dedicated lifecycle test before selecting termination, transfer, or completion-blocking policy.

### High confidence: Patch 3 platform gap

Unix commands are detached into process groups. Linux configures a parent-death signal; macOS does not. Graceful cleanup can kill the group, while force-quit, crash, upgrade, or SIGKILL can bypass Rust teardown and leave Darwin process groups adopted by PID 1. Any recovery design must use identity stronger than PID/PGID alone.

## Likely maintainer constraints and terminology

- Use **background terminal**, **session ID**, **cell ID**, **turn**, **interrupt**, **clean**, and **shutdown**.
- Treat persistence across normal turn completion as intended behavior.
- Keep Patch 1 small; leave completion policy and platform recovery to separate changes.
- Track typed IDs through dispatch. Avoid scraping output text or serialized model-facing strings.
- Verify current liveness before warning because a session may exit between nested return and outer completion.
- Put the warning in the status/header so output truncation cannot erase it.
- Clear per-cell bookkeeping on result, failure, explicit termination, runtime close, and shutdown.
- Use deterministic, network-free helpers and bounded waits.
- Assert lifecycle/event ordering around `TurnComplete`, interrupt, and shutdown.
- Make cleanup operations idempotent.
- Upstream contributions are invitation-based; start with evidence and design discussion.

## Duplicate and adjacent issue candidates

### Primary duplicate candidates

1. [#34866 — “Script completed” is reported while the nested shell session is still running](https://github.com/openai/codex/issues/34866)
   - Near-exact visible contradiction.
   - Uses one logical command with outer `cell_id` and inner `session_id`.
   - Best current home for Patch 1 discussion.

2. [#32411 — functions.exec silently discards un-emitted nested tool results and artifact handles](https://github.com/openai/codex/issues/32411)
   - Exact result-discard mechanism, including lost `session_id`.
   - Broader than process lifecycle because it covers output and artifact handles.

3. [#33816 — GPT-5.6 abandons yielded exec_command sessions and attempts duplicate commands](https://github.com/openai/codex/issues/33816)
   - Model-visible consequence of losing the live-session invariant.
   - References #14731, #15723, #13733, and #32188.

### Adjacent Patch 1 / Patch 2 reports

4. [#14731 — Turn completes prematurely when unified_exec background processes are still running](https://github.com/openai/codex/issues/14731)
   - Same completion-versus-live-process tension at turn level.
   - Its proposed completion guard would change persistence policy, so the per-cell visibility fix is narrower.

5. [#15723 — Background subprocesses/subagents do not wake the calling agent on completion](https://github.com/openai/codex/issues/15723)
   - Strong Patch 2 adjacency: completion notification and parent wake-up after the originating turn ends.

6. [#19197 — Persistent orphaned subagents, missing lifecycle controls, and eventual session freezes](https://github.com/openai/codex/issues/19197)
   - Hidden-subagent visibility and cleanup adjacency.

### Adjacent Patch 3 reports

7. [#28794 — Codex CLI native process can remain orphaned/headless and spin at 100% CPU](https://github.com/openai/codex/issues/28794)
   - macOS owner-loss evidence, though the hot process is the Codex worker rather than a unified-exec child.

8. [#21008 — orphaned MCP helpers under launchd](https://github.com/openai/codex/issues/21008)
   - Related macOS process-reaping class with a different owner and executable path.

## Publication recommendation

Do not publish the standalone issue draft unchanged while #34866 remains open. Preferred next action:

1. Ask whether maintainers want the deterministic discarded-handle reproduction and per-cell summary proposal added to #34866.
2. If they consider #34866 focused on one foreground command, open a separate issue scoped to discarded nested live-session handles and link both directions.
3. Keep hidden-subagent policy and macOS recovery out of the Patch 1 thread except as explicitly separate follow-ups.

---

# Unpublished upstream issue draft

**Title:** Code-mode completion can hide still-running nested background terminals

## Summary

A code-mode JavaScript cell can finish with `Script completed` while nested `exec_command` calls are still running. Each live nested call returns a typed `session_id`, but JavaScript can discard it by reading or printing only `result.output`. The background terminal remains alive across turns by design, while the outer result no longer exposes the handle needed to poll or terminate it.

This appears closely related to #34866 and #32411. I am opening this only if maintainers prefer a separate issue for the discarded-handle case.

## Impact

The transcript can present a terminal-looking code-cell result while retaining live processes that the agent can no longer identify. In the observed macOS incident, two screenshot processes survived for days after a `Promise.all` cell printed only their output strings and completed. The agent retried the work through another path, so duplicate background work continued invisibly.

The same mechanism can affect builds, test runners, browser automation, development servers, and any nested command that crosses its initial yield boundary.

## Network-free reproduction

A regression test can use two deterministic long-running test helpers:

1. Start both helpers from one code-mode cell with `Promise.all`.
2. Give each nested `exec_command` a short `yield_time_ms` so both return live `session_id` values.
3. Emit only `result.output` from each result, deliberately dropping both IDs.
4. Let the JavaScript cell return successfully.

Representative JavaScript:

```js
const [a, b] = await Promise.all([
  tools.exec_command({ cmd: HELPER_A, yield_time_ms: 250 }),
  tools.exec_command({ cmd: HELPER_B, yield_time_ms: 250 }),
]);
text(a.output);
text(b.output);
```

The test should avoid network access, use deterministic process IDs where available, enforce bounded waits, and terminate both sessions in teardown even if an assertion fails.

## Actual behavior

The outer result starts with:

```text
Script completed
```

The two background terminals remain live in the unified-exec process manager. Their session IDs are absent because the JavaScript did not emit them.

## Expected behavior

Successful JavaScript completion should still disclose nested background terminals that remain live, for example:

```text
Script completed with 2 background terminals still running
Session IDs: 6306, 11236
```

This keeps normal cross-turn persistence intact while preserving visibility and control.

## Root cause assessment

**High confidence:** `ExecCommandToolOutput::code_mode_result` includes `session_id` when the nested process remains alive. The nested dispatch path returns that JSON to JavaScript, which may discard fields. The terminal code-cell status is derived from `RuntimeResponse::Result`, so successful JavaScript becomes `Script completed` without checking nested unified-exec liveness.

**High confidence:** The current code already carries the originating code-mode `CellId` in `ToolCallSource::CodeMode`, but there is no per-cell live-session summary at outer completion.

**Medium confidence:** Hidden subagents and yielded cells introduce a broader ownership question because the code-mode session can outlive the turn-scoped dispatch worker. That deserves a separate lifecycle policy discussion.

## Narrow Patch 1 proposal

- Record typed live unified-exec session IDs from nested tool results, keyed by code-mode `CellId`.
- Before formatting a terminal code-cell result, query the unified-exec manager and retain only sessions still live.
- Prepend the surviving IDs to the status/header so output truncation cannot remove them.
- Deduplicate IDs and clear per-cell bookkeeping on completion, failure, explicit termination, cell close, and shutdown.
- Preserve the nested JavaScript result schema and current background-terminal persistence policy.

## Separate follow-ups

- **Patch 2:** define ownership when a hidden subagent or completed turn still owns live cells or background terminals; evaluate termination, parent transfer, explicit persistence, or completion blocking.
- **Patch 3:** address macOS owner loss, where detached process groups lack Linux `PR_SET_PDEATHSIG` protection and can survive abrupt runtime death.

Would maintainers prefer this case to be handled under #34866, and does a per-cell live-session summary fit the intended code-mode contract? I can prepare a focused regression test and minimal implementation after direction on issue scope and wording.
