# Follow-up audit: session shutdown versus late unified-exec store

Status: confirmed teardown-ordering gap and post-drain insertion window; escaped process not yet reproduced end to end.

Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`

This is separate from Patch 1. It must not change or delay the live-session visibility fix.

## Executive finding

Session teardown currently performs these operations in this order:

1. abort the active turn task;
2. drain and terminate all currently stored unified-exec processes;
3. shut down code mode and wait for its cell tasks.

The unified-exec manager has no closing state. `terminate_all_processes()` drains the process map under its mutex, releases that mutex, and then terminates the drained entries. A code-mode nested exec that has already been dispatched can therefore insert a new live `ProcessEntry` after the drain but before code-mode shutdown quiesces the producer.

No second manager drain follows code-mode shutdown. A process stored in that interval can remain manager-owned after session teardown.

The ordering gap is confirmed from source. An actual escaped child process still needs a deterministic regression.

## Confirmed code path

### Teardown order

File: `codex-rs/core/src/session/handlers.rs`

`shutdown_session_runtime` currently:

```text
abort_all_tasks
terminate_all_processes
code_mode_service.shutdown
```

`abort_all_tasks` cancels and aborts the active session task. It does not itself shut down the session-owned code-mode runtime or all yielded cells.

### Manager drain semantics

File: `codex-rs/core/src/unified_exec/process_manager.rs`

`terminate_all_processes()`:

1. locks `process_store`;
2. drains all current entries and clears reserved IDs;
3. releases the lock;
4. unregisters approvals and calls `process.terminate()` for each drained entry.

There is no manager-closing flag and `store_process()` does not reject insertion during or after teardown.

### Code-mode quiescence occurs later

Files:

- `codex-rs/core/src/tools/code_mode/mod.rs`
- `codex-rs/code-mode/src/session_runtime/mod.rs`

`CodeModeService::shutdown()` marks the service as shutting down and calls the session runtime's shutdown method.

The session runtime then:

- cancels its session shutdown token;
- closes the cell task tracker;
- waits for all tracked cell tasks to finish.

That is the operation that quiesces yielded cells and their callback tasks, but it happens only after the unified-exec drain.

### Nested exec stores early

File: `codex-rs/core/src/unified_exec/process_manager.rs`

A newly spawned process that appears alive is stored before the initial yield wait. This intentionally preserves background terminals across interruption, but it means a callback only needs to progress through process startup to create a manager-owned entry.

## High-confidence race sequence

1. A code-mode cell dispatches nested `exec_command`.
2. The callback task begins process startup but has not yet called `store_process()`.
3. Session shutdown starts.
4. The active turn task is cancelled or aborted, but the already-dispatched cell callback remains capable of running until code-mode shutdown cancels and joins the cell runtime.
5. `terminate_all_processes()` drains the manager while the new process is not yet present.
6. Process startup completes.
7. The callback calls `store_process()` and inserts the new live entry after the drain.
8. Code-mode shutdown cancels and joins the cell.
9. Session teardown continues without another manager drain.
10. The late process remains in the manager and may remain alive outside the completed session.

The precise result when the callback future is cancelled at different points still requires testing. The key invariant failure is independent: manager insertion remains permitted after the one teardown drain has completed.

## Preferred regression strategy

Use deterministic barriers rather than shell sleeps.

### Layer 1: manager ordering test

Add a focused unified-exec unit test that proves post-drain insertion is currently possible:

1. Hold the process-store mutex.
2. Start `terminate_all_processes()` so it queues first for the mutex.
3. Start a test insertion representing `store_process()` so it queues second.
4. Release the mutex.
5. Await both operations.
6. Assert that the manager contains the late entry after termination returns.

This establishes the manager-level gap without process-spawn timing. The fixed contract should make the insertion fail or synchronously terminate the inserted process once shutdown begins.

A small test-only barrier or extracted `drain_for_shutdown` helper may be preferable to relying on mutex waiter ordering. Do not add a public production API solely for the test.

### Layer 2: session-level code-mode regression

Build an integration test with a controllable exec backend or spawn barrier:

1. Start a code-mode nested exec and block process startup immediately before the callback can store the process.
2. Confirm that shutdown has entered unified-exec termination and completed its manager drain.
3. Release process startup so the callback attempts to store.
4. Allow code-mode shutdown to finish.
5. Assert that session shutdown returns.
6. Assert that the manager is empty and the executor process has received confirmed termination.

The baseline is expected either to leave a live manager entry or to reveal an unconfirmed child termination. Record the exact observed outcome rather than assuming which transport wins the race.

### Required teardown safeguards

- hard timeout around the full test;
- panic-safe release of every barrier;
- confirmed cleanup of any local or fake remote process;
- final empty manager assertion;
- no reliance on operating-system process reaping alone.

## Candidate fixes after reproduction

### Preferred ownership sequence

A robust shutdown should close admission before draining resources:

1. mark unified exec as closing so new stores are rejected or immediately terminated;
2. shut down code mode and wait for all cell/callback producers to quiesce;
3. drain and terminate unified exec;
4. optionally assert or perform a defensive final drain.

### Narrower options

1. Reorder code-mode shutdown before unified-exec termination.
   - This may be sufficient if code-mode shutdown reliably joins every callback that can store a process.
   - It still leaves other potential unified-exec producers unguarded.

2. Add a manager closing flag checked by process-ID allocation and `store_process()`.
   - Strong admission invariant.
   - Late stores must terminate their process rather than merely return an error and drop bookkeeping.

3. Add a second drain after code-mode shutdown.
   - Useful defence in depth.
   - Alone, it treats the symptom and may still race with other producers.

The final design should state which component owns the shutdown admission barrier.

## Related remote-termination concern

`UnifiedExecProcess::terminate()` awaits local PTY termination synchronously but spawns remote exec-server termination as a detached task. Therefore even entries included in the drain do not receive confirmed remote termination before `terminate_all_processes()` returns.

That transport-confirmation problem deserves its own regression and should not be conflated with the late-store race. A session-level race test using a fake remote backend should record both properties separately:

- was the process included in the drain;
- was termination confirmed before shutdown completed.

## Initial duplicate search

An initial upstream search for `code mode shutdown background terminal race` did not reveal an obvious direct report. The results were broader terminal-cleanup and lifecycle issues. Perform a fresh, wider search only after executable reproduction.

## Relationship to Patch 1

Patch 1 reports still-live nested session IDs at terminal code-mode boundaries. It intentionally preserves background-process persistence.

This follow-up concerns session teardown admitting a new manager-owned process after the teardown drain. Keep its test, shutdown policy, and eventual issue separate from the Patch 1 implementation and publication.
