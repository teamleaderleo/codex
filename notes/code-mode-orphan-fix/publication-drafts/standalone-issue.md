# Unpublished standalone issue draft

Status: unpublished

## Proposed title

Code mode can report completion without exposing still-live nested exec session IDs

## Proposed body

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

## Publication note

Open this standalone issue first. Do not substitute a comment on openai/codex#34866 for this issue. After GitHub assigns the issue number, add that number to the PR draft before opening the PR.