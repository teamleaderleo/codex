# Agent 4 report: upstream history and issue draft

## Status

- Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
- Research date: 2026-07-26
- Publication status: private draft. No upstream issue, comment, or pull request was published.

## Revised conclusion

This work supports a strong standalone issue.

Several public reports touch adjacent symptoms, but none currently combines the same concise failure sequence, a regression test that reproduces it, exact code-path analysis, and a narrow implementation prototype.

The central bug is:

1. A code-mode JavaScript cell launches nested `tools.exec_command()` calls.
2. The commands cross `yield_time_ms` and return live `session_id` values.
3. JavaScript consumes only `.output`, discarding those handles.
4. The JavaScript cell returns successfully.
5. The outer result says `Script completed` while the nested processes remain alive.
6. The agent no longer has the IDs required to poll or terminate them.

Background-terminal persistence across turns is intended. Silent loss of the handles is the defect.

## Current team evidence

### Agent 2 regression test

Branch: [`research/code-mode-live-session-test`](https://github.com/teamleaderleo/codex/tree/research/code-mode-live-session-test)

Test: `code_mode_completion_does_not_surface_discarded_live_exec_sessions`

The test:

- starts two nested long-running commands through `Promise.all`;
- sets `yield_time_ms: 250`;
- destructures only `{ output }`, deliberately discarding both session IDs;
- confirms that two distinct background terminals remain alive after cell completion;
- confirms the outer header says `Script completed` and contains no session information;
- terminates every background terminal during teardown, including after a panic.

This is direct executable proof of the interface failure. The current helper uses shell commands and skips Windows, so a later refinement may replace it with a shared cross-platform test helper. That does not weaken the demonstrated runtime path on supported test platforms.

### Integrator prototype

Branch: [`fix/code-mode-live-session-summary`](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-summary)

The prototype:

- scopes nested tool call IDs to the originating `CellId`;
- queries `UnifiedExecProcessManager::list_processes()` at the outer runtime-response boundary;
- filters currently live processes created by that cell;
- adds their session IDs to the untruncated status header.

Example output:

```text
Script completed
Background sessions still running: 6306, 11236
Wall time 0.3 seconds
Output:
...
```

This preserves the existing JavaScript result schema and intended cross-turn process persistence.

### Agent 3

I do not see an Agent 3 ownership/API report in the repository or the known scratch branches yet. Its read-only assignment may exist only in another conversation. The current test and prototype already provide enough evidence to revise the issue strategy.

## Relevant upstream history

### Persistence is deliberate

- PR #8052 originally closed unified-exec sessions at turn completion.
- PR #10799 deliberately reversed that policy and preserved background terminals across ordinary turns.
- Later cleanup semantics moved toward explicit user control such as `/stop`, plus runtime shutdown.

Therefore this bug should not be described as “a process survived turn completion.” The defect is that code mode can hide the live process handle while reporting a terminal-looking outer status.

### The direct exec interface already exposes liveness

`ExecCommandToolOutput::response_text` tells the model when a process remains running and includes its session ID. `ExecCommandToolOutput::code_mode_result` likewise returns a typed `session_id` to JavaScript.

Code mode loses that protection when user JavaScript omits the field from emitted output.

### The cell identity already exists

Nested dispatch already carries `ToolCallSource::CodeMode { cell_id, runtime_tool_call_id }`. A fix can associate live processes with their originating cell without parsing JavaScript output.

## Related public issues and exact distinctions

These are useful prior art and cross-links, not reasons to suppress this issue.

### #34866 — `Script completed` while a nested shell session remains live

Closest visible symptom. It focuses on the confusing two-level lifecycle for one logical foreground command: outer `cell_id` completion versus inner `session_id` liveness.

This project adds a distinct failure mode:

- multiple nested calls;
- handles deliberately discarded by ordinary JavaScript projection;
- no surviving model-visible ID;
- a regression test proving the live sessions remain registered;
- a concrete per-cell visibility patch.

### #32411 — un-emitted nested tool results and artifact handles are discarded

This identifies the general result-loss mechanism. Its motivating harm is lost output and artifact metadata.

This project focuses on a live resource handle. Losing `session_id` leaves an operating-system process alive and removes the normal control path.

### #33816 — model abandons yielded direct exec sessions

This describes model behaviour after receiving a live session: false completion inference and duplicate commands.

This project demonstrates a runtime/API path where the outer code-mode result itself can erase the session handle before the model can preserve it.

### #14731 — turn completes with background processes still running

This proposes guarding turn completion while processes remain live.

This project preserves the intentional persistence policy and changes visibility at the code-cell boundary only.

### #15723 — background work does not wake the parent

Useful follow-up for event-driven completion and hidden-subagent ownership. It is separate from the initial handle-loss bug.

## Publication recommendation

Prepare a standalone upstream issue once the test and prototype are consolidated into a clean comparison branch or draft PR.

The issue should:

- lead with the six-step executive summary;
- include the compact network-independent reproduction;
- link the regression test commit and prototype diff;
- cite #34866, #32411, #33816, #14731, and #15723 under “Related” with one-sentence distinctions;
- keep macOS crash recovery and hidden-subagent policy as follow-up work;
- avoid uploading private rollout logs, environment dumps, or process records.

A good issue can serve as the design record for the prospective PR. The test demonstrates the bug, the patch demonstrates feasibility, and the history explains why the fix preserves process persistence.

---

# Unpublished upstream issue draft

**Title:** Code mode can report completion after discarding live nested exec session handles

## Executive summary

A code-mode JavaScript cell can finish with `Script completed` while nested `exec_command` processes remain alive and their session handles have disappeared from the model-visible result.

The reproducible sequence is:

1. Start two nested `tools.exec_command()` calls with `Promise.all`.
2. Both commands reach `yield_time_ms` and return live `session_id` values.
3. JavaScript reads only `.output` and discards both IDs.
4. The JavaScript cell returns successfully.
5. The outer tool result says `Script completed`.
6. Both background terminals remain registered and running, but the agent no longer knows their IDs.

Cross-turn background-terminal persistence is intentional. The bug is the loss of visibility and control.

## Minimal reproduction

```js
const outputs = (await Promise.all([
  tools.exec_command({
    cmd: "printf orphan-a; sleep 60",
    yield_time_ms: 250,
  }),
  tools.exec_command({
    cmd: "printf orphan-b; sleep 60",
    yield_time_ms: 250,
  }),
])).map(({ output }) => output);

text(outputs.join("|"));
```

The shell commands above are only compact examples. The regression test performs bounded cleanup and can later use a shared cross-platform long-running helper.

## Actual behaviour

The outer result begins with:

```text
Script completed
Wall time ...
Output:
orphan-a|orphan-b
```

At that point, `list_background_terminals()` returns two distinct live sessions. Their IDs appear nowhere in the outer result because the JavaScript projection discarded them.

## Expected behaviour

The outer status should disclose any nested unified-exec sessions from that cell that remain live:

```text
Script completed
Background sessions still running: 6306, 11236
Wall time ...
Output:
orphan-a|orphan-b
```

The processes may continue running. The agent retains the information needed to poll, inspect, or terminate them.

## Regression test

A focused test exists on [`research/code-mode-live-session-test`](https://github.com/teamleaderleo/codex/tree/research/code-mode-live-session-test):

`code_mode_completion_does_not_surface_discarded_live_exec_sessions`

It proves that:

- two nested commands yield;
- JavaScript discards both session IDs;
- the outer cell reports completion without session information;
- both sessions remain live;
- teardown terminates every session even after an assertion panic.

## Root cause

High confidence:

- `ExecCommandToolOutput::code_mode_result` returns `session_id` when unified exec remains live.
- `call_nested_tool` passes that typed JSON to JavaScript.
- JavaScript may emit only selected fields.
- `handle_runtime_response` derives `Script completed` from successful `RuntimeResponse::Result`.
- No outer-cell summary currently checks whether nested unified-exec processes from that cell remain alive.

The nested dispatch path already carries the originating `CellId`, and the unified-exec manager already exposes live process metadata.

## Proposed narrow fix

A prototype exists on [`fix/code-mode-live-session-summary`](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-summary).

It:

1. scopes nested tool-call IDs to the originating cell;
2. queries the existing live-process list at the outer response boundary;
3. filters processes created by that cell;
4. places surviving session IDs in the status header.

The header is inserted after output truncation, so large command output cannot remove the warning.

This patch does not:

- terminate background terminals;
- change persistence across turns;
- change the JavaScript-visible nested result schema;
- solve hidden-subagent ownership;
- solve macOS process recovery after abrupt runtime death.

## Related issues

- #34866 covers the outer-completed/inner-running lifecycle contradiction for a nested shell session.
- #32411 covers silent loss of un-emitted nested tool results and artifact handles.
- #33816 covers model-side abandonment of yielded direct exec sessions.
- #14731 covers turn completion while background processes remain live.
- #15723 covers parent wake-up after background process or subagent completion.

This report adds a deterministic discarded-handle reproduction, an integration test with teardown, and a small visibility-only implementation path.

## Maintainer question

Does associating nested unified-exec calls with their originating code-mode cell and surfacing currently live session IDs in the outer status header fit the intended code-mode contract?
