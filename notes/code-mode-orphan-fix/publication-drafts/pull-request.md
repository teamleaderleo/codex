# Unpublished pull-request draft

Status: unpublished

## Proposed title

code-mode: surface live nested exec session IDs on terminal completion

## Proposed body

### Summary

- preserve typed code-mode creator-cell attribution on stored live process entries;
- use the session-level unified-exec process manager as the sole liveness source;
- report exact-cell, still-live nested session IDs in terminal code-mode status headers;
- exclude exited processes and sort session IDs deterministically;
- keep yielded responses, opaque nested tool-call IDs, the JavaScript result schema, and all process lifecycle policy unchanged;
- add focused manager coverage and five aggregate code-mode acceptance cases.

### Problem

A code-mode script can launch nested `exec_command` calls, receive live `session_id` values, and then project those values away by emitting only `.output`. The JavaScript cell can complete successfully while the processes remain alive in the session-level unified-exec process manager. The outer model-visible result then says `Script completed` but provides no session IDs for polling or termination.

The process manager already owns the live processes and already defines liveness. The missing information is typed creator-cell attribution that lets a terminal code-cell response identify the matching stored live process entries without relying on JavaScript output or parsing nested call-ID text.

### Design

- `ExecCommandHandler` translates `ToolCallSource::CodeMode { cell_id, .. }` into optional typed `CellId` creator metadata.
- `UnifiedExecContext` carries that metadata to process creation.
- Stored live process entries retain the optional creator cell.
- `UnifiedExecProcessManager::live_process_ids_created_by_cell` performs a read-only lookup that:
  - uses exact `CellId` equality;
  - excludes entries whose process has exited;
  - excludes direct or unattributed entries;
  - returns logical session IDs in numeric order.
- Code-mode response handling calls that lookup only for terminal `Result` and `Terminated` responses.
- The matching session IDs are appended to the existing terminal status header.

The existing process manager remains the sole liveness authority. This avoids a second registry and avoids inferring ownership from JavaScript values, command text, or nested call IDs.

### Behavioural boundaries

This PR is visibility-only.

- Successful `Result`, failed `Result`, and explicit `Terminated` responses may disclose matching still-live session IDs.
- Ordinary `Yielded` responses remain completion-neutral and unchanged.
- Exited processes are not reported.
- One cell cannot disclose another cell's process.
- Nested tool-call IDs remain opaque.
- The JavaScript-visible nested result schema is unchanged.
- No lifecycle, termination, pruning, persistence, shutdown, interrupt, dispatch, recovery, public-protocol, or JavaScript-schema policy is changed.

Code-mode emitted output is converted and truncated before the status header is prepended, so the live-session warning is outside that specific truncation boundary. The complete tool result remains subject to later global conversation-history limits.

Example output, using illustrative session IDs:

```text
Script completed
Background sessions still running: 6306, 11236
Wall time ...
Output:
...
```

### Validation

Repository-native focused validation on Linux aarch64:

- `just fmt`: passed;
- `just fix -p codex-core`: passed;
- four focused unit tests: `4 passed; 0 failed`;
- five aggregate acceptance cases in the existing code-mode integration suite: `5 passed; 0 failed`;
- two existing compatibility tests, repeated ten times each on the final candidate: `20/20 passed`;
- the same two tests, repeated ten times each on exact upstream base `61a44880a85d2fd0d8770908dea5733495e571c8`: `20/20 passed`;
- clean worktree and `git diff --check`: passed.

The four focused unit tests verify:

1. exact-cell, live-only filtering, including exclusion of another cell, unattributed entries, and exited entries, with numeric ordering;
2. terminal-cell selection excludes `Yielded` responses;
3. terminal status formatting reports sorted live session IDs; and
4. yielded status formatting does not disclose completion-only session information.

The five aggregate acceptance cases verify:

1. multiple discarded live session IDs are reported in numeric order;
2. only the surviving session is reported after another exits;
3. one cell cannot disclose another cell's process;
4. a large emitted payload cannot displace the status warning at the code-mode truncation boundary; and
5. yielded responses remain completion-neutral.

The aggregate harness uses cleanup protection that runs after success, returned errors, and panics while preserving an original panic.

A matched broad `just test -p codex-core` differential was red on both the production-equivalent candidate and the exact upstream base. Persistent failures were attributable to environment dependencies, unavailable helper binaries, sandbox or runner limitations, or assertions reproduced on the exact base. The two differing broad-run test names both passed repeated focused executions on both refs, leaving no persistent candidate-only failure. The broad project suite is not claimed as green.

The complete workspace suite was not run.

### Related work

Related prior symptom coverage: openai/codex#34866. That report overlaps with `Script completed` appearing while a nested shell remains live; this PR implements the narrower exact-cell visibility contract described by the standalone issue opened immediately before this PR.

## Publication note

After opening the standalone issue, add a `Fixes` line with its assigned issue number to the public PR body. Open the PR immediately afterward from `teamleaderleo:fix/code-mode-live-session-summary-clean`, then add the PR URL to the issue and verify both reciprocal links.
