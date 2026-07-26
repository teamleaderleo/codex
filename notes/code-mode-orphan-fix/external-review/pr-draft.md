# Review-only upstream pull-request draft

> This is a review snapshot, not the final publication source. The final candidate head, test paths, and validation commands will be refreshed after the test-only packaging revision.

## Proposed title

`code-mode: surface live nested exec session IDs on terminal completion`

## Summary

- preserve typed code-mode creator-cell attribution on stored unified-exec process entries;
- report exact-cell, still-live nested session IDs in terminal code-mode status headers;
- exclude exited processes and sort logical IDs deterministically;
- keep yielded responses, the JavaScript-visible result schema, opaque nested call IDs, and process lifecycle policy unchanged; and
- add focused unit and end-to-end acceptance coverage.

## Problem

A code-mode script can launch nested `exec_command` calls, receive live `session_id` values, and then project those values away by emitting only `.output`. The JavaScript cell can complete successfully while the processes remain alive in the conversation-level process manager. The outer model-visible result then says `Script completed` but provides no IDs for polling or termination.

The process manager already owns the live processes. The missing piece is creator attribution that lets the terminal code-cell response identify the matching live sessions without relying on emitted JavaScript values or call-ID text.

## Design rationale

The existing unified-exec process manager remains the sole source of process liveness. This change does not add a second live-session registry or infer ownership from JavaScript output, command text, timing, or nested call-ID formatting.

Instead, the existing nested-call provenance is retained along the process-creation path:

`ToolCallSource::CodeMode -> ExecCommandHandler -> UnifiedExecContext -> ProcessEntry`

Code mode then asks the manager for a point-in-time, exact-cell, live-only list when rendering a terminal response.

## Implementation

- Convert `ToolCallSource::CodeMode { cell_id, .. }` into optional typed creator-cell metadata in `UnifiedExecContext`.
- Copy that metadata onto each stored live `ProcessEntry`.
- Add a crate-private, read-only manager query that uses exact `CellId` equality, excludes exited processes, and returns sorted logical process IDs.
- Query that method only for terminal `Result` and `Terminated` responses.
- Prepend the live-session summary after emitted output has been converted and truncated.
- Preserve the existing success, failure, and termination status text.
- Preserve ordinary `Yielded` status behaviour.

## Behavioural boundary

This PR is visibility-only. It does not terminate processes, alter persistence, block turn completion, wake idle sessions, change nested call IDs, change the JavaScript-visible result schema, or modify pruning, shutdown, interrupt, dispatch, subagent, remote-exec, or recovery policy.

## Current implementation for review

- Clean implementation commit: `3778e1fae6e7e3d885252282a7c5ce67e06730ff`
- Upstream base: `61a44880a85d2fd0d8770908dea5733495e571c8`
- Comparison: `61a44880a85d2fd0d8770908dea5733495e571c8...3778e1fae6e7e3d885252282a7c5ce67e06730ff`

A test-only follow-up is in progress on `review/code-mode-roundtable-test-polish`. It is expected to move the five acceptance cases into the existing aggregate integration-test structure and improve cleanup and determinism without changing production code.

## Validation

Completed on the clean implementation:

- `just fmt`: passed with no changes;
- `just fix -p codex-core`: passed with no changes;
- three focused code-mode unit tests: passed;
- three focused unified-exec tests: passed;
- five acceptance cases: passed;
- clean repository status and `git diff --check`;
- exact-file equivalence and independent architecture/API-conventions reviews: passed.

Broad project-suite classification:

- `just test -p codex-core` was red on both the candidate and exact upstream base;
- persistent failures were shared missing-helper, sandbox/runner, timeout, or unrelated baseline outcomes;
- the two differing broad-run failures passed repeatedly on both refs;
- no persistent candidate-only failure remained;
- the broad project suite and complete workspace suite are not claimed green.

The final PR will replace this section with the revised aggregate-suite test commands and final candidate head after the test-only revision is accepted.

## Acceptance coverage

The five cases verify that:

- two discarded live IDs are surfaced exactly once and in numeric order;
- only the surviving process is reported when another exits;
- a large emitted payload cannot truncate the status warning;
- yielded cells do not receive completion-only disclosure;
- one cell cannot disclose another cell's process; and
- teardown leaves no registered background terminal.

## Issue

Refs `<issue-link>`.
