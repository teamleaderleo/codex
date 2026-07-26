# Patch 1 final unpublished issue and pull-request drafts

Date: 2026-07-26

## Publication status

- Unpublished. No upstream issue or pull request has been created.
- Upstream base: `61a44880a85d2fd0d8770908dea5733495e571c8`
- Canonical branch: `fix/code-mode-live-session-summary-clean`
- Final clean head: `760216784efaee1ba6a3b1250349f31d5f91c7ca`
- Clean comparison: `61a44880a85d2fd0d8770908dea5733495e571c8...760216784efaee1ba6a3b1250349f31d5f91c7ca`
- Publication strategy: publish the standalone issue first, open the PR immediately afterward, and cross-link both in the same working session.

The drafts below are scrubbed of agent identities, research ancestry, machine-specific paths, raw logs, launcher troubleshooting, and unrelated follow-up planning.

---

# Final proposed standalone issue

## Title

Code mode can report completion without exposing still-live nested exec session IDs

## Body

### Summary

A code-mode JavaScript cell can finish with `Script completed` while nested `exec_command` processes remain alive and their session IDs have disappeared from the model-visible result.

The reproducible sequence is:

1. Start nested `tools.exec_command()` calls that outlive their initial yield window.
2. Unified exec stores the live processes in the session-level unified-exec process manager and returns copied `session_id` values to JavaScript.
3. JavaScript keeps or emits only `.output`, discarding the copied session IDs.
4. The JavaScript cell returns successfully.
5. The outer result reports `Script completed`.
6. The processes remain live, but the model receives no session ID with which to poll, inspect, or terminate them.

Background-process persistence is intentional. The defect is loss of model-visible control information at a terminal code-cell boundary.

### Minimal reproduction

```js
const outputs = (await Promise.all([
  tools.exec_command({
    cmd: "printf orphan-a; sleep 60",
    yield_time_ms: 250,
  }),
  tools.exec_command({
    cmd: "printf orphan-b; sleep 60",
    yield_time_ms: 250,
  }),
])).map(({ output }) => output);

text(outputs.join("|"));
```

### Actual behaviour

```text
Script completed
Wall time ...
Output:
orphan-a|orphan-b
```

The session-level unified-exec process manager still owns two live processes, but their session IDs are absent because JavaScript projected them away.

### Expected behaviour

A terminal code-cell result should disclose the still-live nested sessions created by that cell:

```text
Script completed
Background sessions still running: 6306, 11236
Wall time ...
Output:
orphan-a|orphan-b
```

`6306` and `11236` are illustrative session IDs.

The processes may continue running. The model retains the information needed to poll, inspect, or terminate them.

The session summary is placed outside code-mode emitted-output truncation, so a large emitted payload cannot displace it at that boundary. The complete tool result, including the summary, remains subject to later global conversation-history limits.

### Ownership and narrow fix

- Code mode owns the nested callback while the nested tool call is dispatched and awaited.
- Once a yielded process is stored, the session-level unified-exec process manager is the source of truth for whether it is still live.
- JavaScript receives a copied session ID; discarding that value does not affect the manager-owned process.
- The nested dispatch path already has typed code-mode cell identity, but the baseline does not retain that identity on stored live process entries.
- Terminal rendering therefore cannot recover the matching live session IDs when JavaScript omits them.

The tested fix:

1. carries typed creator-cell attribution from `ToolCallSource::CodeMode` through unified exec;
2. stores it on stored live process entries;
3. performs a read-only, exact-cell lookup in the existing process manager;
4. excludes exited processes and sorts matching session IDs deterministically;
5. reports matching session IDs only for terminal `Result` and `Terminated` responses;
6. keeps ordinary `Yielded` responses completion-neutral; and
7. preserves opaque nested tool-call IDs.

No lifecycle, termination, pruning, recovery, protocol, or JavaScript-schema policy is changed.

### Validation

Repository-native focused validation on Linux aarch64 recorded:

- formatting: passed;
- scoped fix/lint: passed;
- four focused unit tests: `4 passed; 0 failed`;
- five aggregate acceptance cases: `5 passed; 0 failed`;
- two existing compatibility tests repeated on the final candidate: `20/20 passed`;
- the same two compatibility tests repeated on the exact upstream base: `20/20 passed`.

The five aggregate acceptance cases cover:

1. multiple discarded live session IDs in numeric order;
2. exited-session exclusion with only the surviving session reported;
3. exact creator-cell isolation between two cells;
4. warning placement outside code-mode emitted-output truncation; and
5. yielded-response neutrality.

The aggregate test harness also verifies cleanup across success, returned error, and panic paths.

A matched broad `codex-core` run was red on both the production-equivalent candidate and the exact upstream base because of environment dependencies, unavailable helper binaries, sandbox or runner limitations, and unrelated baseline failures. Repeated focused comparison left no persistent candidate-only failure. The broad project suite is not claimed as green.

The complete workspace suite was not run.

A narrow tested implementation is ready and will be submitted as a pull request immediately after this issue is opened.

### Related issues

- openai/codex#34866 provides related prior symptom coverage for `Script completed` appearing while a nested shell remains live. This issue is the standalone problem statement for the narrower, tested failure where JavaScript discards still-live session IDs and terminal rendering does not restore them.
- openai/codex#32411 covers the broader loss of arbitrary awaited-but-unemitted nested results and artifact handles. This issue concerns only session IDs for processes that are still live in the process manager.
- openai/codex#33816 covers model-side abandonment after a live session ID was already exposed. Here, the session IDs never reach the model in the terminal outer result.
- openai/codex#14731, openai/codex#15723, and openai/codex#32188 concern blocking completion or waking an idle parent. This fix changes neither lifecycle policy nor completion eventing.

---

# Final proposed pull request

## Title

code-mode: surface live nested exec session IDs on terminal completion

## Body

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

The aggregate harness verifies cleanup across success, returned error, and panic paths.

A matched broad `just test -p codex-core` differential was red on both the production-equivalent candidate and the exact upstream base. Persistent failures were attributable to environment dependencies, unavailable helper binaries, sandbox or runner limitations, or assertions reproduced on the exact base. The two differing broad-run test names both passed repeated focused executions on both refs, leaving no persistent candidate-only failure. The broad project suite is not claimed as green.

The complete workspace suite was not run.

### Related work

Related prior symptom coverage: openai/codex#34866. That report overlaps with `Script completed` appearing while a nested shell remains live; this PR implements the narrower exact-cell visibility contract described by the standalone issue opened immediately before this PR.

---

## Publication-time cross-link procedure

This section is internal and is not part of either public body.

1. Open the standalone issue using the issue title and body above.
2. Before creating the PR, add a `Fixes` line containing the actual issue number assigned in step 1.
3. Open the PR from `teamleaderleo:fix/code-mode-live-session-summary-clean` against `openai/codex` at the approved base.
4. Add the resulting PR URL to the issue, either by editing the final implementation sentence or by posting one concise comment.
5. Confirm that the issue and PR each render a working reciprocal link.

## Remaining human approval

Technical and validation wording is resolved. Human approval is still required for:

- the final public tone and title choices;
- the exact publication moment;
- the issue-first-then-PR execution; and
- the publication-time insertion of the actual reciprocal links.
