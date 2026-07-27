# Report live nested exec session IDs on code-mode completion

> Open only after a Codex maintainer invites the contribution and the issue agrees the terminal-response boundary.

Implements the behaviour agreed in #<issue-number>.

## What

- Retain the originating code-mode `CellId` on manager-owned unified-exec process entries.
- Add a read-only lookup for live processes created by an exact cell.
- Include the matching logical session IDs in the agreed terminal code-mode responses.
- Keep ordinary `Yielded` responses unchanged.
- Add focused manager and formatter tests plus one end-to-end discarded-handle regression.

## Why

A code-mode cell can start nested `exec_command` calls, retain only their output, and discard the returned `session_id` values.

Those commands can remain live after the cell finishes. The unified-exec manager still owns them, but the final code-mode result previously had no path to recover their model-visible handles.

## How

Nested tool dispatch already identifies calls originating from code mode. This change carries that existing typed cell identity into the unified-exec process entry.

When the cell reaches an agreed terminal outcome, response handling asks the existing manager for processes that:

- were created by that exact cell; and
- remain live according to manager state at lookup time.

The formatter presents the resulting IDs deterministically in the existing status header. The lookup does not wait for, terminate, prune, or mutate any process.

## Example

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

## Testing

Run and record every check on the same final rebased SHA:

- `just fmt`
- `just fix -p codex-core`
- focused manager and formatter tests
- the primary discarded-handle end-to-end regression
- relevant existing code-mode compatibility tests
- `git diff --check`

Final head: `<final-sha>`

Issue: #<issue-number>