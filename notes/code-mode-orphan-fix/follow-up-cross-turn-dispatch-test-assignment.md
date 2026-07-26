# Cross-turn code-mode dispatch regression assignment

Status: ready for a separate follow-up agent after Patch 1 integration is stable.

Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`

Read first:

- `notes/code-mode-orphan-fix/follow-up-cross-turn-dispatch-audit.md`
- `notes/code-mode-orphan-fix/coordination-status.md`
- `codex-rs/core/src/tools/code_mode/delegate.rs`
- `codex-rs/core/src/tools/code_mode/execute_handler.rs`
- `codex-rs/core/src/tools/code_mode/wait_handler.rs`
- `codex-rs/code-mode/src/cell_actor/mod.rs`
- `codex-rs/code-mode/src/cell_actor/callbacks.rs`
- `codex-rs/code-mode/src/runtime/globals.rs`

## Scope

Create executable evidence for or against the suspected cross-turn dispatch crossover. Keep this entirely separate from Patch 1. Do not change background-process persistence, creator-cell attribution, cleanup policy, or the live-session summary.

Do not select a production fix before the tests establish baseline behaviour.

## Confirmed static path

The test should be based on these already-confirmed facts:

1. A yielded cell remains session-owned and is not cancelled.
2. Delivering `CellEvent::Yielded` does not cancel callback tokens.
3. `yield_control`, `setTimeout`, and nested tools are available to the JavaScript runtime.
4. A yielded response does not close the cell's dispatch gate.
5. The original `CodeModeDispatchWorker` is turn-scoped.
6. The broker queue and receiver are session-scoped.
7. Successor turn workers clone the same competing receiver and bind it to their own `ToolCallRuntime`.
8. Dispatch messages carry `CellId` but no originating turn ID or worker generation.

The remaining question is executable behaviour, not whether cancellation or gate closure universally forbids the path.

## Test 1: successor-turn crossover

Build a bounded two-turn regression with three test-owned tools:

- `dispatch_arm`: called by Cell A while Turn A is active; records its observed turn ID and returns immediately.
- `dispatch_probe`: called later by the same Cell A; records its observed turn ID and signals the test.
- `turn_b_hold`: called directly during Turn B; keeps Turn B and Worker B active until the probe executes or the test times out.

Use a Cell A script equivalent to:

```js
await tools.dispatch_arm({});
yield_control();
await new Promise((resolve) => setTimeout(resolve, 1000));
await tools.dispatch_probe({});
text("done");
```

Required ordering:

1. Prove `dispatch_arm` executed through Turn A.
2. Observe the yielded outer response.
3. Let Turn A finish so Worker A drops.
4. Start Turn B and keep it active with `turn_b_hold`.
5. Allow Cell A's delayed probe to run.
6. Compare the turn IDs received by `dispatch_arm` and `dispatch_probe`.

Baseline failure evidence is:

```text
dispatch_arm.turn_id != dispatch_probe.turn_id
```

Also assert that both calls retain the same code-mode `CellId`, teardown terminates Cell A, every barrier is released, and the whole test has a bounded timeout.

## Test 2: no-successor queue wait

Cover the simpler failure mode separately:

1. Turn A yields Cell A and ends.
2. Cell A emits a delayed nested callback after Worker A has dropped.
3. No successor turn starts.
4. Observe whether the callback remains unresolved indefinitely.

The test must use a short outer timeout and always terminate the cell during cleanup. A baseline timeout is evidence that the session queue accepts work without an active owner and provides no bounded failure.

## Preferred hardening

The timer-based integration test is acceptable as the first executable probe when it uses wide timing margins and strict outer timeouts.

If it flakes, add the smallest test-only ordering seam possible. Prefer an internal fake dispatch host or worker-generation barrier over a new public API. Do not duplicate the worker loop in the test, because that could accidentally test a model rather than the production routing path.

## Desired post-fix contract

A delayed callback must do exactly one of the following:

- execute through an explicitly bound originating worker generation; or
- fail within a bounded period with an ownership/turn-ended error.

It must never silently execute through an unrelated successor turn.

## Required handoff

```text
Branch/ref:
Baseline:
Changed files:
Exact tests added:
Exact commands run:
Observed baseline behaviour:
Whether crossover was reproduced:
Whether no-successor waiting was reproduced:
Timing or platform limitations:
Production seam added, if any:
Recommended issue/fix decision:
```
