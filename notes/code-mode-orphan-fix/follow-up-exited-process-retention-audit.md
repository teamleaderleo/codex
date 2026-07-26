# Follow-up audit: exited unified-exec entry retention

Status: confirmed hidden post-exit retention; whether it is a bug depends on the intended late-polling contract.

Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`

This is separate from Patch 1. It is not a live-process orphan finding.

## Executive finding

When a stored unified-exec process exits naturally, the background exit watcher emits the terminal event but does not remove the corresponding `ProcessEntry` from the manager.

`list_processes()` filters exited entries, so the process disappears from the public background-terminal listing. Internally, however, the manager can continue retaining:

- the exited `UnifiedExecProcess` handle;
- the logical process ID reservation;
- command, cwd, call ID, and timestamps;
- optional deferred network-approval state;
- weak session attribution and other entry metadata.

The entry is removed only when another path explicitly refreshes or releases it, when pruning selects it after store pressure, during explicit termination, or at session shutdown.

This may be intended to support a late final poll, but the current retention period is implicit and potentially lasts for the rest of the session. The product contract should choose bounded tombstone retention or prompt cleanup rather than relying on unrelated future activity.

## Confirmed code path

### Exit watcher emits but does not remove

File: `codex-rs/core/src/unified_exec/async_watcher.rs`

`spawn_exit_watcher`:

1. waits for the process cancellation/exit token;
2. waits for output draining and any network-denial monitor;
3. acquires the process interaction lock;
4. emits a success or failure terminal event;
5. returns.

The watcher does not hold a manager reference and does not call `release_process_id` or otherwise remove the entry.

### Public listing hides the retained entry

File: `codex-rs/core/src/unified_exec/process_manager.rs`

`list_processes()` filters entries with `!entry.process.has_exited()`. Therefore an exited retained entry is absent from the public list even while still present in `process_store`.

### Removal is incidental

Confirmed removal paths include:

- `refresh_process_state`, reached by later polling or interaction;
- `release_process_id`;
- `terminate_process`;
- `prune_processes_if_needed` when the manager approaches its soft cap;
- `terminate_all_processes` during explicit cleanup or session shutdown.

A naturally exited process that receives no later interaction can remain stored indefinitely within the session.

### Process-ID reservation remains occupied

`ProcessStore::remove` releases both the entry and its reserved process ID. Because the watcher does not call it, the reservation remains occupied with the stale entry.

In deterministic test mode, new IDs are allocated above the maximum reserved ID. In production, random allocation retries on a reserved collision. This is not immediate exhaustion, but it is evidence that the manager still treats the exited entry as owned state.

## Why this is not automatically a bug

Late polling may be useful:

- a caller holding a session ID may poll after the process exits;
- `refresh_process_state` can then return the exit code and remove the entry;
- final output may still need reconciliation with the terminal event.

However, the current implementation does not define a retention duration, a tombstone representation, or a maximum number of exited entries independent of live-process capacity.

The design question is therefore:

> How long should an exited unified-exec session remain addressable after its terminal event, and which state must be retained to support that window?

## Preferred regression and contract test

### Baseline retention test

1. Start a command that is alive long enough to be stored but exits shortly afterward.
2. Wait for its terminal event and output-drain completion.
3. Assert `list_processes()` no longer exposes it.
4. Inspect the manager store and confirm the entry and process-ID reservation remain.
5. Wait beyond the output grace period without polling or starting another process.
6. Confirm the entry is still retained.
7. Explicitly release it for cleanup.

This test documents current behaviour without declaring it correct.

### Contract alternatives

Choose and test one explicit policy:

1. **Prompt removal after terminal publication**
   - The exit watcher removes the entry after the terminal event is durable.
   - Late polling returns unknown-process because the terminal event is the authoritative completion channel.

2. **Bounded tombstone retention**
   - Replace the heavy live `ProcessEntry` with a small exited record containing process ID, exit code, final output cursor, and expiry.
   - Late polling works for a documented duration.
   - Expiry is actively scheduled, not dependent on unrelated manager operations.

3. **Capacity-bounded exited cache**
   - Maintain separate live and exited collections with independent caps.
   - Never let exited records consume live-process capacity.

The current implicit “retain until something else notices” policy should not be the final contract.

## Additional risks to measure

- Does deferred network-approval registration remain live until incidental removal?
- Can repeated short-lived yielded commands accumulate 64 retained entries before pruning begins?
- Does pruning while the exit watcher holds the interaction lock temporarily exceed the manager cap?
- Can late polling race terminal-event publication and lose either output or the exit code?
- Are remote exited processes more likely to remain stale because exit-state propagation differs from local PTYs?

These should be answered by focused tests before proposing cleanup changes.

## Related upstream report

Open issue #12321 reports a stale Desktop “Running N terminals” display after processes die externally. The current core `list_processes()` filters `has_exited()`, so that UI symptom may involve a different tracker or stale event propagation. It is related prior art, not proof that this manager-retention finding is the same bug.

Re-check that issue and current code after an executable core regression exists.

## Relationship to Patch 1

Patch 1 queries live processes only and correctly excludes exited entries from the completion header.

This follow-up concerns internal retention after natural exit. It does not change which sessions Patch 1 reports and must not expand the visibility patch.
