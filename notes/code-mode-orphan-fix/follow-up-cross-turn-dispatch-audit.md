# Follow-up audit: delayed code-mode dispatch across turn boundaries

Status: read-only hypothesis and regression plan; not yet reproduced.

Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`

This is separate from Patch 1. It should not change or delay the live-session visibility fix.

## Why this deserves a focused test

`CodeModeDispatchBroker` owns one session-lived unbounded dispatch channel. Every turn-scoped worker clones the same receiver and pairs it with that turn's `CoreTurnHost` and `ToolCallRuntime`.

Relevant code:

- `codex-rs/core/src/tools/code_mode/mod.rs`
  - `CodeModeService` owns one `CodeModeDispatchBroker` for the session.
  - `start_turn_worker` constructs an `ExecContext` from the current turn and asks the broker to start a worker.
- `codex-rs/core/src/tools/code_mode/delegate.rs`
  - `CodeModeDispatchBroker` owns one `dispatch_tx` and one cloneable `dispatch_rx`.
  - `start_turn_worker` clones `dispatch_rx` and creates a `CoreTurnHost` containing the current turn's runtime.
  - dispatch messages carry a cell ID and cancellation token, but no originating turn ID or worker identity.
  - dispatch readiness gates are keyed only by `CellId`.
  - dropping a turn worker stops that consumer but does not close or drain the broker's session-lived channel.

Upstream provenance:

- PR: openai/codex#14437, `Dispatch tools when code mode is not awaited directly`
- Author: `pakrym-oai`
- Merge commit: `2f03b1a3220378426ba1c0894f1551829f4c60e5`
- Recorded design: start one code-mode worker per turn and pump nested tool calls through a dedicated queue.
- The PR body states that testing had not been run at publication time.

## Candidate failure sequence

The following sequence is plausible from the current ownership model but remains unproven until a deterministic test reproduces it:

1. Turn A starts or resumes a code-mode cell.
2. The cell remains alive long enough to issue a nested tool call near or after Turn A completion.
3. Turn A's `CodeModeDispatchWorker` is dropped.
4. The invocation is queued on the broker's session-lived channel while no Turn A worker can consume it, or loses a receive race with worker shutdown.
5. Turn B starts and creates a new worker with Turn B's `ExecContext` and `ToolCallRuntime`.
6. Turn B's cloned receiver consumes the older invocation.
7. The nested tool executes using Turn B's runtime even though its `CellId` originated before Turn B.

Possible effects include wrong turn attribution, wrong approval or sandbox context, output injected into the wrong active turn, or a tool call surviving longer than its visible owner.

Cancellation and cell-gate closure may prevent some variants. The test must therefore control token lifetime and gate state rather than infer the bug from static code alone.

## Regression plan

Add a deterministic integration test with two turns and a controllable nested tool:

1. Turn A launches a code-mode cell whose JavaScript waits on a deterministic barrier before invoking a nested tool.
2. Allow Turn A to complete or its worker to drop while the cell remains capable of issuing the call.
3. Release the barrier so the old cell submits its nested invocation when no Turn A worker is available.
4. Start Turn B and ensure a Turn B code-mode worker is active.
5. Record which turn context handles the nested invocation.
6. Assert that an invocation originating from Turn A is not executed through Turn B's `ToolCallRuntime`.

Useful assertions:

- no nested-tool begin event for the old cell is attributed to Turn B;
- no old-cell notification is injected into Turn B;
- the old invocation receives a bounded cancellation or ownership error rather than waiting indefinitely;
- the broker queue and cell gate are cleared at teardown.

A second test should cover the simpler no-successor case: after Turn A ends, an old cell submits a nested call and receives a bounded failure without requiring another turn to start.

## Contract decision required after reproduction

Do not select a fix before the test establishes current behaviour. Viable policies include:

1. Bind each queued message to an originating turn/worker generation and reject it after that worker ends.
2. Give each turn a private dispatch queue while retaining a session-level delegate router.
3. Permit explicit handoff of a live cell to a later turn, but represent that transfer in typed metadata and events.

The current implicit behaviour—whichever cloned receiver consumes the message—should not serve as the ownership contract.

## Relationship to Patch 1

Patch 1 only surfaces live unified-exec session IDs at terminal code-mode outcomes. It should preserve existing process persistence and use typed creator-cell attribution.

This follow-up concerns which turn runtime is allowed to execute a delayed nested callback. Keep its test, policy discussion, and eventual issue separate from the Patch 1 implementation and public issue.
