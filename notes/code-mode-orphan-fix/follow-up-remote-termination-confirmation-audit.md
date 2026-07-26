# Follow-up audit: remote unified-exec termination confirmation

Status: confirmed fire-and-forget bulk-termination path; real remote-process escape not yet reproduced.

Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`

This is separate from Patch 1 and from the shutdown/store admission race.

## Executive finding

Unified exec has two different termination contracts:

- terminating one tracked process uses `terminate_confirmed().await` and waits for a remote exec-server process to acknowledge termination;
- bulk termination drains all tracked entries, calls `process.terminate()`, and returns without waiting for remote acknowledgement.

For an exec-server-backed process, `UnifiedExecProcess::terminate()` launches `process_handle.terminate()` in a detached Tokio task, immediately cancels local output state, and returns. The manager has already removed the entry by then.

Consequently, session shutdown or `/stop`-style bulk cleanup can report completion after discarding the only local tracking entry while the remote termination request is still pending or may later fail.

The source-level contract mismatch is confirmed. A real remote executor surviving shutdown still needs reproduction.

## Confirmed code path

### Individual termination is confirmed

Files:

- `codex-rs/core/src/unified_exec/process_manager.rs`
- `codex-rs/core/src/unified_exec/process.rs`

`UnifiedExecProcessManager::terminate_process`:

1. clones the tracked process;
2. awaits `process.terminate_confirmed()` when it is still alive;
3. re-locks the store and removes the matching entry.

`UnifiedExecProcess::terminate_confirmed` awaits the exec-server backend's `terminate()` future and propagates an error before marking local state complete.

### Bulk termination is not confirmed

`UnifiedExecProcessManager::terminate_all_processes`:

1. drains the full manager store and clears reserved IDs;
2. releases the store lock;
3. unregisters approval state;
4. calls `entry.process.terminate()` for each drained entry;
5. returns `()`.

For local PTY processes, `terminate()` invokes local termination directly. For remote exec-server processes, it instead spawns a detached async task:

```text
tokio::spawn(async move {
    let _ = process_handle.terminate().await;
});
```

The result is ignored. The manager entry has already been discarded, so the caller cannot retry or inspect the remote process by logical process ID.

## Existing deterministic test fixture

File: `codex-rs/core/src/unified_exec/mod_tests.rs`

The existing `BlockingTerminateExecProcess` fixture is sufficient to test this without a real remote environment:

- its `terminate()` method signals `terminate_started`;
- it then waits on a test-controlled `allow_terminate` notification;
- existing tests use it to verify the confirmed single-process path.

No new production probe or remote service is required.

## Preferred regression

Add a focused manager test using `BlockingTerminateExecProcess`:

1. Insert one fake remote process into `process_store` with `initial_exec_command_active = false`.
2. Spawn `terminate_all_processes()`.
3. Wait until the fake backend signals that remote termination started.
4. Keep `allow_terminate` blocked.
5. Observe whether the bulk-termination future has already completed.
6. Release `allow_terminate` for panic-safe cleanup.
7. Await all tasks and assert the manager remains empty.

Expected baseline observation:

```text
terminate_all_processes returned while remote terminate was still blocked
```

Desired contract:

```text
bulk termination does not report completion until every remote termination has either completed or produced an explicit bounded failure result
```

The test should use a hard timeout and always release the barrier after panic or assertion failure.

## Failure-path regression

Add a second fake exec-server process whose `terminate()` returns an error.

The test should establish and protect the chosen policy:

- whether bulk cleanup returns an error/report;
- whether failed entries remain trackable for retry;
- whether session shutdown emits a warning or telemetry record;
- whether a bounded timeout is treated differently from a backend rejection.

Silently dropping both the backend error and the process entry should not be the intended contract.

## Candidate fixes

### Preferred implementation

Make bulk termination confirmed and bounded:

1. drain or mark entries as terminating;
2. terminate processes concurrently with `terminate_confirmed()`;
3. apply a bounded timeout per process or to the collection;
4. collect successes, failures, and timeouts into a shutdown report;
5. preserve or otherwise report enough identity to diagnose and retry failures;
6. return the report to session shutdown and explicit cleanup callers.

Use bounded concurrency or `FuturesUnordered` rather than serially waiting on many remote processes.

### Narrow alternative

Change only session shutdown to await confirmed termination while leaving an intentionally fire-and-forget UI cleanup path.

This is weaker and creates two user-visible cleanup meanings. If retained, the distinction must be explicit in API naming, documentation, and tests.

### Defence in depth

Remote executors should also have owner-loss behaviour, such as a lease, heartbeat, or transport-disconnect cleanup policy. That protects against client crashes where no confirmation request can be sent. It does not remove the need for a confirmed graceful-shutdown contract.

## Relationship to the shutdown/store race

These are independent failure dimensions:

1. **Admission race:** was a process inserted after the manager's one shutdown drain?
2. **Termination confirmation:** for a process included in the drain, did the remote backend actually finish termination before shutdown returned?

A session-level regression can inspect both, but fixes and issue descriptions should keep the invariants distinct.

## Initial duplicate search

An initial upstream search for `remote exec server terminate background terminal shutdown` returned broad MCP and process-leak reports, but no obvious report of the unified-exec bulk path dropping tracking before remote termination acknowledgement. Repeat a wider search after executable reproduction.

## Relationship to Patch 1

Patch 1 preserves background-terminal persistence and only restores model-visible session IDs at terminal code-mode boundaries.

This follow-up concerns graceful cleanup guarantees for remote processes. Keep its tests, API decisions, and eventual issue separate from the Patch 1 implementation and public report.
