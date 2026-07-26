# Follow-up audit: delayed code-mode dispatch across turn boundaries

Status: high-confidence static crossover path; executable reproduction not yet run.

Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`

This is separate from Patch 1. It must not change or delay the live-session visibility fix.

## Executive finding

A yielded code-mode cell is session-owned and can remain alive after the turn that started it has ended. Its callback cancellation token remains live and its dispatch gate remains open. Meanwhile, `CodeModeDispatchBroker` owns one session-lived queue whose receiver is cloned by each turn worker.

The current dispatch message contains the originating `CellId`, but no originating turn ID or worker generation. Therefore, a nested callback emitted by an old yielded cell after Turn A's worker has stopped can be consumed by Turn B's worker and executed through Turn B's `ToolCallRuntime`.

That conclusion follows strongly from the current ownership and routing code. It remains a candidate bug until an executable test observes the crossover.

## Confirmed lifecycle and routing facts

### Session-lived broker, turn-scoped consumers

Relevant files:

- `codex-rs/core/src/tools/code_mode/mod.rs`
- `codex-rs/core/src/tools/code_mode/delegate.rs`

Confirmed behaviour:

- `CodeModeService` owns one `CodeModeDispatchBroker` for the session.
- The broker owns one unbounded `dispatch_tx` and one cloneable `dispatch_rx`.
- Every turn creates a `CodeModeDispatchWorker` that clones the same receiver.
- Each worker binds that receiver to a `CoreTurnHost` containing that turn's `ExecContext` and `ToolCallRuntime`.
- Cloned async-channel receivers are competing consumers. A message is handled by whichever live worker receives it.
- `DispatchMessage` carries a cell ID and cancellation token, but no originating turn ID or worker generation.
- Dropping a worker asks that consumer loop to stop. It does not close or drain the session queue.
- After a worker accepts an invocation, it starts a detached task that retains that worker's turn-specific host.

### Yielded cells remain live across the turn boundary

Relevant files:

- `codex-rs/core/src/tools/code_mode/execute_handler.rs`
- `codex-rs/core/src/tools/code_mode/wait_handler.rs`
- `codex-rs/code-mode/src/cell_actor/mod.rs`
- `codex-rs/code-mode/src/cell_actor/types.rs`
- `codex-rs/code-mode/src/session_runtime/mod.rs`

Confirmed behaviour:

- The execute handler marks the cell ready for dispatch before waiting for its first response.
- A `Yielded` response does not call `finish_cell_dispatch`; the gate remains open.
- The wait handler closes the dispatch gate only when a later wait observes a terminal response.
- The session runtime keeps yielded cells in its session-level cell registry.
- A cell's cancellation token is a child of the session token. Callback tokens are children of the cell token.
- Delivering `CellEvent::Yielded` does not cancel the cell or callback tokens.
- A live yielded cell can therefore emit another nested tool request after the initiating turn has ended.
- The cell is removed and `cell_closed` closes the gate only during terminal cell cleanup.

These facts rule out cancellation and gate closure as general protections for the yielded-cell crossover sequence. They may still prevent narrower variants involving explicit termination, session shutdown, or a terminal result.

## High-confidence crossover sequence

1. Turn A starts Cell A and creates Worker A.
2. Cell A yields while still running.
3. Turn A completes; Worker A is dropped.
4. Cell A remains registered, its callback token remains live, and its dispatch gate remains open.
5. Cell A emits a nested tool invocation after Worker A has stopped.
6. The invocation is queued on the session-lived broker.
7. Turn B starts and creates Worker B, which clones the shared receiver and binds it to Turn B's runtime.
8. Worker B receives the older Cell A invocation.
9. The nested tool executes through Turn B's `ToolCallRuntime`, despite originating from Cell A before Turn B.

Possible effects:

- wrong turn ID in tool lifecycle events;
- wrong turn-scoped extension state;
- wrong approval, environment, sandbox, or hook context;
- output or notification injection into the wrong active turn;
- an old callback becoming dependent on an unrelated successor turn.

## Upstream provenance

- PR: openai/codex#14437, `Dispatch tools when code mode is not awaited directly`
- Author: `pakrym-oai`
- Merge commit: `2f03b1a3220378426ba1c0894f1551829f4c60e5`
- Recorded design: start one code-mode worker per turn and pump nested tool calls through a dedicated queue.
- The PR body states that testing had not been run at publication time.

Initial issue searches for `code mode nested tool wrong turn` and `code mode turn worker nested tool` did not surface an obvious direct duplicate. This is not a final duplicate check.

## Preferred executable regression

Use the existing extension test surface rather than adding production-only probes.

### Test-owned tools

Register native test tools through `ExtensionRegistryBuilder::tool_contributor`:

1. `dispatch_arm`
   - invoked from Cell A while Turn A is unquestionably active;
   - records `ToolCall.turn_id` as the originating turn;
   - returns immediately.

2. `dispatch_probe`
   - invoked later by the same Cell A;
   - records its received `ToolCall.turn_id`;
   - signals a test-owned notification and returns JSON.

3. `turn_b_hold`
   - invoked directly by the model in Turn B;
   - waits until `dispatch_probe` has executed;
   - keeps Turn B and Worker B alive long enough to consume the queued callback.

The public extension `ToolCall` already exposes `turn_id`, so the test can observe the executing turn without changing core APIs.

### Turn A script

Use a script equivalent to:

```js
await tools.dispatch_arm({});
yield_control();
await new Promise((resolve) => setTimeout(resolve, 1000));
await tools.dispatch_probe({});
text("done");
```

Required sequencing:

1. `dispatch_arm` confirms Cell A executed through Turn A's runtime.
2. `yield_control()` lets the outer code-mode call return while Cell A remains live.
3. Turn A completes and Worker A drops.
4. The timer later resumes Cell A and emits `dispatch_probe` while no Worker A exists.
5. Turn B starts and directly invokes `turn_b_hold`.
6. Worker B consumes the queued probe, which releases the hold.

### Baseline observation

The suspected baseline behaviour is:

```text
dispatch_arm.turn_id != dispatch_probe.turn_id
```

Both nested calls came from Cell A, but the second executed through Turn B.

Also assert:

- the lifecycle source for both nested calls is `CodeMode` with the same cell ID;
- the probe is not left pending after Turn B begins;
- teardown terminates Cell A and releases every test barrier;
- the test has a bounded timeout and cannot hang the suite.

### Desired contract test

After a fix, require one of these explicit outcomes:

- the delayed callback executes only through its bound originating worker generation; or
- the callback receives a bounded `originating turn ended` or equivalent ownership error.

It must never silently execute through an unrelated successor turn.

## Determinism improvements if the timer version flakes

The timer is adequate for a first executable probe, but the preferred hardened test should remove timing as the ordering mechanism.

Two options:

1. Add a test-only gated model response so the harness can prove Turn A stopped before releasing Cell A's second callback.
2. Add a small broker test seam that exposes worker generation and queue admission, then deterministically enqueue an A-owned message between Worker A shutdown and Worker B startup.

Do not broaden production APIs merely to support the test.

## Secondary no-successor regression

Cover the simpler case separately:

1. Turn A yields Cell A and ends.
2. Cell A later emits a nested callback.
3. No successor turn starts.
4. The callback must receive a bounded failure or cancellation.

An indefinite wait for some future turn to create a worker is not an acceptable implicit contract.

## Candidate fixes after reproduction

Do not select a production change until the test establishes current behaviour. Plausible policies are:

1. Add an originating turn or worker-generation ID to each dispatch message and reject it after that generation ends.
2. Retain a session-level router but give each turn a private queue, routing only messages explicitly bound to that turn.
3. Permit explicit handoff of a live cell to a later turn, but represent the transfer in typed metadata and lifecycle events.

The current rule—whichever cloned receiver consumes the message—should not serve as the ownership contract.

## Relationship to Patch 1

Patch 1 only surfaces live unified-exec session IDs at terminal code-mode outcomes. It preserves process persistence and uses typed creator-cell attribution.

This follow-up concerns which turn runtime is authorised to execute a delayed nested callback. Keep its test, policy discussion, fix, and eventual issue separate from the Patch 1 implementation and public issue.
