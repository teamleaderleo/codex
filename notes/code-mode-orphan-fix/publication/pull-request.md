# Surface live nested exec session IDs in code-mode completion

Carries code-mode `CellId` provenance into manager-owned process entries and reports still-live session IDs when that cell reaches an in-scope terminal response. It doesn't change process lifecycle behaviour, JavaScript result fields, or public protocol shapes.

## Implementation synopsis

Conceptually, with names and surrounding fields omitted:

```rust
struct UnifiedExecContext {
    creator_cell_id: Option<CellId>,
    // existing fields...
}

struct ProcessEntry {
    creator_cell_id: Option<CellId>,
    // existing fields...
}

if let Some(cell_id) = terminal_cell_id(&response) {
    let live_session_ids = process_manager
        .live_process_ids_created_by_cell(cell_id)
        .await;

    // Include live_session_ids in the existing terminal status.
}
```

## What changed

- Retain the originating code-mode `CellId` on manager-owned unified-exec process entries.
- Add a read-only lookup for live processes created by an exact cell.
- Include the matching manager process IDs, exposed to the model as `session_id`, in terminal code-mode responses.
- Leave ordinary `Yielded` responses unchanged.
- Add a focused manager test, formatter tests, and one primary end-to-end regression.

## Why

A code-mode cell can start nested `exec_command` calls, keep only their output, and discard the returned `session_id` values.

Those commands can remain live after the cell finishes. The unified-exec manager still owns them, but its process entries don't preserve the creator-cell relationship needed to recover their model-visible handles when the terminal response is formatted.

## How it works

Nested tool dispatch already identifies calls originating from code mode. This change carries that existing typed cell identity into the unified-exec process entry.

When the cell reaches an in-scope terminal response, response handling asks the existing manager for processes that:

- were created by that exact cell; and
- remain live according to manager state at lookup time.

The formatter presents those IDs deterministically in the existing status header. The lookup doesn't wait for, terminate, prune, or mutate any process.

The lookup reports every still-live process attributed to the cell, including processes whose returned IDs the JavaScript retained; response handling can't distinguish retained handles from discarded ones.

The exploratory prototype reports IDs for successful and failed `Result` responses and for `Terminated`, while leaving `Yielded` unchanged. It includes both local and exec-server-backed entries; exec-server exit visibility follows manager-observed state and can briefly lag an underlying remote exit.

```text
Script completed
Background sessions still running: 6306, 11236
Wall time ...
Output:
...
```

## Display bound

The prototype's 64-ID display limit matches the manager's current 64-process capacity, so it cannot omit a reachable manager-owned ID.

The display and manager constants can remain separate, but the display limit must not fall below manager capacity unless another model-visible path can enumerate omitted IDs.

## Scope

This change leaves the following behaviour unchanged:

- process ownership and lifetime;
- cleanup, pruning, polling, and wake-up policy;
- JavaScript result fields;
- public protocol schemas and event types;
- call-ID generation.

Only sessions attributed to the exact completing cell are reported.

## Exploratory validation history

The proposed PR shape needs one primary end-to-end discarded-handle regression. The exploratory prototype contains five acceptance cases because it was also used to probe truncation, cross-cell attribution, yielded responses, and local-versus-remote liveness boundaries.

These checks span related prototype refs and workspaces rather than one final SHA, and a broad project or workspace suite wasn't completed. The deep dive records the exact validation boundaries.

- a focused manager test for exact-cell attribution, exited-entry filtering, and manager process ID handling;
- formatter tests for terminal-response selection, deterministic ordering, empty-session behaviour, and the model-visible display policy;
- five local acceptance cases, including the primary discarded-handle regression;
- four Docker cases exercising exec-server live-process reporting;
- a local-only exited-process/survivor case, leaving stale remote-exit exclusion untested.

The display-cap cases are formatter-level policy tests. The prototype's display bound and manager process cap currently both equal 64, so over-limit formatting isn't an ordinary steady-state manager path.

The [technical deep dive](https://github.com/teamleaderleo/codex/blob/review/code-mode-issue-ready/notes/code-mode-orphan-fix/publication/deep-dive.md) contains the data-flow analysis, exploratory implementation links, validation record, source references, limitations, and alternatives considered.
