# Surface live nested exec session IDs in code-mode completion

## What changed

- Retain the originating code-mode `CellId` on manager-owned unified-exec process entries.
- Add a read-only lookup for live processes created by an exact cell.
- Include the matching logical session IDs in terminal code-mode responses.
- Leave ordinary `Yielded` responses unchanged.
- Add focused manager and formatter tests plus one end-to-end discarded-handle regression.

## Why

A code-mode cell can start nested `exec_command` calls, keep only their output, and discard the returned `session_id` values.

Those commands can remain live after the cell finishes. The unified-exec manager still owns them, but the final code-mode result has no cell-scoped path to identify and recover their model-visible handles.

## How it works

Nested tool dispatch already identifies calls originating from code mode. This change carries that existing typed cell identity into the unified-exec process entry.

When the cell reaches a terminal outcome, response handling asks the existing manager for processes that:

- were created by that exact cell; and
- remain live according to manager state at lookup time.

The formatter presents those IDs deterministically in the existing status header. The lookup won't wait for, terminate, prune, or mutate any process.

```text
Script completed
Background sessions still running: 6306, 11236
Wall time ...
Output:
...
```

## Liveness semantics

The lookup uses existing manager-observed state. Local handles can expose process exit directly. Exec-server-backed handles rely on exit already reflected in manager state, so reporting can briefly lag an underlying remote exit.

## Scope

This change leaves the following behaviour unchanged:

- process ownership and lifetime;
- cleanup, pruning, polling, and wake-up policy;
- JavaScript result fields;
- public protocol schemas and event types;
- call-ID generation.

Only sessions attributed to the exact completing cell are reported.

## Prototype coverage

- focused manager tests for exact-cell attribution, exited-entry filtering, and logical ID handling;
- formatter tests for terminal-response selection, deterministic ordering, bounded output, and empty-session behaviour;
- one primary end-to-end discarded-handle regression;
- four Docker cases exercising exec-server live-process reporting;
- a local-only exited-process/survivor case, leaving stale remote-exit exclusion untested.
