# Agent 4 report: upstream history and issue draft

## Status

- Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
- Research date: 2026-07-26
- Publication status: private draft. No upstream issue, comment, or pull request has been published.
- Publication gate: a clean regression-test commit and implementation commit that have both run successfully.

## Conclusion

This work supports a strong standalone issue once the publication gate is met.

Several public reports touch adjacent symptoms, but none currently combines the same concise failure sequence, executable reproduction, ownership analysis, intended-persistence history, and narrow implementation contract.

The bug is:

1. A code-mode JavaScript cell launches nested `tools.exec_command()` calls.
2. The commands cross `yield_time_ms`; unified exec stores each live process in the conversation-level process manager and returns a copied `session_id` handle to JavaScript.
3. JavaScript consumes only `.output`, projecting away both copied handles.
4. The JavaScript cell returns successfully.
5. The outer result says `Script completed` while the manager-owned processes remain alive.
6. The model-visible result contains no session IDs with which to poll, inspect, or terminate those processes.

Background-terminal persistence is intentional. The defect is loss of model-visible control information at a terminal outer-cell boundary.

## Confirmed ownership boundary

The ownership audit resolves an important ambiguity:

- **Code mode owns the nested callback task.** The cell actor tracks the callback while the nested tool call is being dispatched and awaited.
- **Unified exec transfers live-process ownership to the conversation-level process manager.** Once `UnifiedExecProcessManager::store_process` retains the process, ordinary cell or turn completion does not release it.
- **JavaScript receives only a copied logical session handle.** The returned object does not own the process.
- **Dropping or projecting away that handle has no lifecycle effect.** The process manager continues to own the live process.
- **The interface defect occurs at reporting time.** The outer cell reports terminal completion without restoring the control information that JavaScript omitted.

This is why Patch 1 should change visibility rather than termination or persistence.

## Current team evidence

### Agent 2 regression test

Scratch branch: [`research/code-mode-live-session-test`](https://github.com/teamleaderleo/codex/tree/research/code-mode-live-session-test)

Test: `code_mode_completion_does_not_surface_discarded_live_exec_sessions`

The current test:

- starts two nested long-running commands through `Promise.all`;
- sets `yield_time_ms: 250`;
- destructures only `{ output }`, deliberately discarding both session IDs;
- confirms that two distinct background terminals remain alive after cell completion;
- confirms the outer header says `Script completed` and contains no session information;
- terminates every background terminal during teardown, including after a panic.

This is direct executable evidence of the interface failure. Before publication, it should be consolidated onto the implementation branch, changed to assert the corrected terminal header, and run in the local Rust environment. A shared cross-platform long-running helper is preferable if practical; panic-safe teardown remains required.

### Agent 1 feasibility prototype

Prototype branch: [`fix/code-mode-live-session-summary`](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-summary)

Prototype commit: [`cffcd8dca93ab5c2ff8fa1af262ae7676f5b97a9`](https://github.com/teamleaderleo/codex/commit/cffcd8dca93ab5c2ff8fa1af262ae7676f5b97a9)

The prototype proves that the outer runtime-response boundary can:

1. query the existing conversation-level live-process manager;
2. retain only processes that are still alive;
3. sort their logical session IDs deterministically;
4. place those IDs in the untruncated status header;
5. preserve intended process persistence; and
6. preserve the JavaScript-visible nested result schema.

Example:

```text
Script completed
Background sessions still running: 6306, 11236
Wall time 0.3 seconds
Output:
...
```

Its call-ID-prefix mechanism is **feasibility evidence, not the recommended ownership API**. Encoding `CellId` into call IDs and recovering ownership with `starts_with` can collide, leaks unrestricted cell strings into identifiers and tracing, and makes a representation convention responsible for resource attribution.

### Recommended implementation contract

Patch 1 should preserve existing typed source metadata through unified exec:

1. Preserve `ToolCallSource::CodeMode { cell_id, runtime_tool_call_id }` through `ExecCommandHandler` into unified-exec context.
2. Store optional typed creator-cell attribution on the live process entry.
3. Query the process manager for currently live processes whose creator cell matches the terminal outer cell.
4. Sort and report surviving logical session IDs in the outer status/header after output truncation.
5. Apply the summary to terminal outcomes: successful result, failed result, and explicit termination.
6. Keep ordinary `Yielded` responses completion-neutral because the outer cell is still active.
7. Preserve the JavaScript `session_id` schema and existing process persistence policy.
8. Do not create a second liveness registry or infer ownership from emitted JavaScript values.

The prototype's manager-query and header-formatting scaffolding may be reusable. Typed creator attribution should replace prefix matching before the work is presented as the implementation.

## Intended persistence history

### Persistence across ordinary turns is deliberate

- PR #8052 originally closed unified-exec sessions at turn completion.
- PR #10799 deliberately reversed that policy and preserved background terminals across ordinary turns.
- PR #14602 preserved background terminals on interrupt, moved cleanup toward explicit `/stop`, and stored a live process before the initial yield wait so interruption could not drop the last process reference.

Therefore the issue should not claim that survival after cell or turn completion is itself erroneous. The bug is that the surviving manager-owned process becomes invisible to the model after its copied handle is discarded.

### Direct exec already treats the live handle as essential state

`ExecCommandToolOutput::response_text` tells the model when a direct exec process remains running and includes its session ID. `ExecCommandToolOutput::code_mode_result` likewise gives JavaScript a typed `session_id`.

Code mode loses that protection when JavaScript emits or retains only selected fields. The outer terminal status is the last reliable place to restore control information for still-live sessions created by that cell.

## Related public issues and distinctions

These are useful prior art and cross-links, not reasons to suppress a tested standalone report.

- **#34866:** closest visible outer-completed/inner-running symptom for a nested shell session. This work adds deliberate handle projection, multiple live sessions, manager-state verification, a contract test, and a typed per-cell implementation design.
- **#32411:** covers un-emitted nested results and artifact handles generally. Here the discarded value controls a process that remains alive independently in the conversation-level manager.
- **#33816:** covers model-side abandonment after a direct exec session was exposed. Here the runtime/API path removes the handle before the model receives the outer result.
- **#14731:** proposes guarding turn completion while background processes remain live. This work preserves intended persistence and changes terminal code-cell visibility only.
- **#15723:** covers waking a parent after background work completes. It is relevant to broader ownership and eventing, not this initial handle-loss fix.

Separate audit findings involving delayed dispatch, shutdown races, remote bulk termination, stale bookkeeping, hidden-subagent policy, and macOS crash recovery should receive their own tests and issue decisions.

## Publication recommendation

Keep the issue private until both of these exist and have run:

- **Regression commit:** `<tested-regression-commit>`
- **Implementation commit:** `<tested-implementation-commit>`

At publication time, replace scratch-branch links with those stable commits or a clean comparison/PR link. The issue can then serve as a concise design record for the prospective PR:

**observed incident → six-step reproduction → failing contract test → ownership boundary → tested visibility patch**

Do not upload private rollout logs, prompts, environment dumps, machine-specific paths, image data, tokens, or unrelated conversation content.

---

# Unpublished upstream issue draft

**Title:** Code mode can report completion after discarding live nested exec session handles

## Executive summary

A code-mode JavaScript cell can finish with `Script completed` while nested `exec_command` processes remain alive and their session handles have disappeared from the model-visible result.

The reproducible sequence is:

1. Start two nested `tools.exec_command()` calls with `Promise.all`.
2. Both commands reach `yield_time_ms`; unified exec stores the live processes and returns copied `session_id` handles.
3. JavaScript reads only `.output`, discarding both copied IDs.
4. The JavaScript cell returns successfully.
5. The outer tool result says `Script completed`.
6. Both background terminals remain registered and running, but their IDs are absent from the model-visible result.

Cross-turn background-terminal persistence is intentional. The bug is loss of visibility and control while the outer cell reports terminal completion.

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

The shell commands are compact examples. The regression test uses bounded, panic-safe cleanup; its final published form should use the cleanest available deterministic long-running helper.

## Actual behaviour

The outer result begins with:

```text
Script completed
Wall time ...
Output:
orphan-a|orphan-b
```

At that point, the conversation-level process manager still contains two distinct live sessions. Their IDs appear nowhere in the outer result because JavaScript projected them away.

## Expected behaviour

A terminal outer-cell status should disclose currently live nested unified-exec sessions created by that cell:

```text
Script completed
Background sessions still running: 6306, 11236
Wall time ...
Output:
orphan-a|orphan-b
```

The processes may continue running. The agent retains the information needed to poll, inspect, or terminate them.

## Ownership and root cause

High confidence:

- Code mode owns each nested callback task while dispatching the nested tool call.
- After unified exec stores a yielded process, the conversation-level process manager owns it.
- JavaScript receives only a copied logical session handle; dropping the returned object does not affect the process.
- `ExecCommandToolOutput::code_mode_result` supplies the copied `session_id` to JavaScript.
- JavaScript may retain or emit only selected fields.
- `handle_runtime_response` reports `Script completed` from a successful terminal `RuntimeResponse::Result` without summarising still-live processes created by that cell.

The dispatch path already carries typed `ToolCallSource::CodeMode { cell_id, ... }` metadata, but baseline unified exec does not retain the creator cell on the live process entry.

## Regression and implementation evidence

- Tested regression commit: `<tested-regression-commit>`
- Tested implementation commit or PR: `<tested-implementation-commit-or-pr>`

The current regression proves that two IDs can be discarded while both sessions remain alive and absent from the outer header.

A feasibility prototype proves that the outer response can query the existing live-process manager, sort surviving IDs, and place them in the untruncated status header without changing persistence or the JavaScript result schema. Its call-ID-prefix matching is prototype-only and is not the proposed ownership API.

## Proposed narrow fix

1. Preserve typed `ToolCallSource::CodeMode` creator-cell metadata through unified exec.
2. Store optional creator-cell attribution on each live process entry.
3. On terminal cell outcomes, query for still-live processes created by that cell.
4. Sort and append their logical session IDs to the untruncated outer status header.

### Non-goals

This change does not:

- terminate background terminals;
- change persistence across turns or interrupts;
- change the JavaScript-visible nested result schema;
- report a completion warning on an ordinary yielded outer cell;
- define hidden-subagent ownership or completion policy;
- fix delayed dispatch, shutdown races, remote termination, or stale bookkeeping;
- solve macOS recovery after abrupt runtime death.

## Related issues

- #34866: similar outer-completed/inner-running symptom; this report adds deliberate handle loss, multiple sessions, a contract test, and typed creator attribution.
- #32411: general loss of un-emitted nested results; this case loses control of a separately manager-owned live process.
- #33816: abandonment after a direct session was exposed; this case hides the handle before the model receives the outer result.
- #14731: proposes blocking turn completion; this proposal preserves persistence and changes visibility only.
- #15723: parent wake-up after background completion; separate eventing and ownership concern.

## Maintainer question

Does preserving typed creator-cell attribution on unified-exec process entries and surfacing surviving session IDs in terminal code-mode headers fit the intended ownership contract?

---

## Compact handoff

```text
Agent: 4 — history and upstream issue editor
Branch/ref: research/code-mode-orphan-handoffs
Baseline: 20dafe201d91d4405eef05ecd1db0257f13a9ac8
Changed files: notes/code-mode-orphan-fix/agent-4-history-issue-report.md
Tests run and results: none; documentation-only revision
Confirmed findings: Agent 1 proves manager-query/header feasibility; recommended implementation uses typed ToolCallSource::CodeMode creator attribution on ProcessEntry; process ownership transfers to the conversation-level manager before JavaScript can discard its copied handle
Open risks: final process-entry field shape and query API; terminal-failure/termination semantics; cross-platform regression helper; race coverage for one process exiting before summary generation
Publication questions: publish issue before or alongside the prospective PR; exact tested commit/PR links; whether maintainers prefer the header wording or another model-facing representation
Recommended next action: consolidate and run the positive regression with the typed-attribution implementation, then replace placeholders and perform one final issue-editing pass
```