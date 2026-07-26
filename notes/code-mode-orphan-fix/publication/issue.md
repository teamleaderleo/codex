# `Script completed` can omit session IDs for live nested terminals

Unpublished issue text.

## Summary

A code-mode JavaScript cell can start nested terminal commands, keep only their `.output`, and discard the returned session IDs. The cell can then report `Script completed` while those terminal sessions are still running. Codex still tracks them internally, but the model no longer has the session IDs needed to poll or terminate them.

Background terminal persistence is intentional. The defect is that a terminal code-mode result can lose model-visible control handles for work that remains live.

## Impact

The terminal result can make the script appear finished while nested commands continue running without an obvious control path. Depending on the command, the remaining processes may continue consuming CPU, memory, file descriptors, sockets, locks, subprocesses, network activity, or filesystem state until they exit or are found and terminated by another route.

This is not evidence of a literal Rust memory leak, and this report does not assign a security severity. It is a control-visibility defect with operational resource-retention risk.

## Minimal reproduction

`yield_time_ms` lets each command return a session ID while its process remains live. This example deliberately projects the returned objects down to `.output`:

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

## Actual behaviour

```text
Script completed
Wall time ...
Output:
orphan-a|orphan-b
```

Both nested terminal sessions are still live, but their session IDs are absent from the model-visible result.

## Expected behaviour

A terminal code-cell result should report the still-live nested sessions created by that cell:

```text
Script completed
Background sessions still running: 6306, 11236
Wall time ...
Output:
orphan-a|orphan-b
```

`6306` and `11236` are illustrative session IDs. The processes may continue running; the model retains the information needed to poll or terminate them.

## Boundary

The proposed fix is visibility-only:

- the existing unified-exec process manager remains the source of truth for liveness;
- only still-live sessions created by the exact completing code-mode cell are reported;
- exited sessions and sessions created by other cells are excluded;
- ordinary yielded code-cell responses remain unchanged;
- nested tool-call IDs remain opaque;
- the JavaScript-visible nested result schema is unchanged; and
- process lifetime, termination, pruning, shutdown, interrupt, recovery, wake-up, and protocol behaviour do not change.

The status line is added outside code mode's emitted-output truncation step. The complete tool result remains subject to later global conversation-history limits.

## Evidence

- [Negative reproduction](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5)
- [Final code and test comparison](https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...760216784efaee1ba6a3b1250349f31d5f91c7ca)
- [Aggregate acceptance tests](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs)
- [Creator-cell attribution](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L132-L138)
- [Exact-cell live-session query](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L168-L180)
- [Terminal response rendering](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/code_mode/mod.rs#L199-L300)

## Validation

Repository-native focused validation on Linux aarch64 recorded:

- formatting and scoped fix/lint passed;
- four focused unit tests passed;
- five aggregate acceptance cases passed;
- two existing compatibility tests passed 20/20 executions on the final candidate;
- the same tests passed 20/20 executions on the exact upstream base.

A matched broad `codex-core` run was red on both refs. Exact-base comparison and focused reruns found no persistent candidate-only failure; the broad project suite is not claimed green. The complete workspace suite was not run.

## Related issues

- [#34866](https://github.com/openai/codex/issues/34866) covers a related symptom involving `Script completed` and a still-live nested shell. This report defines the narrower executable case where JavaScript discards still-live session IDs and terminal rendering does not restore them.
- [#32411](https://github.com/openai/codex/issues/32411) covers the broader loss of awaited but unemitted nested results and artifact handles.
- [#33816](https://github.com/openai/codex/issues/33816) covers model-side abandonment after a live session ID was already exposed.

Broader completion-blocking, wake-up, and lifecycle-policy questions are outside this report.
