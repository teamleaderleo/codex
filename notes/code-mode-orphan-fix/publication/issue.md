# `Script completed` can omit session IDs for live nested commands

<!-- Unpublished issue draft. -->

## Summary

A code-mode JavaScript cell can start nested terminal commands, keep only their `.output`, and discard the returned session IDs. The cell can then report `Script completed` while those commands are still running. Codex still tracks the processes internally, but the final result no longer contains the session IDs needed to inspect, continue, or terminate them.

Background terminal persistence is intentional. The defect is that a completing-cell result can hide the control handles for work that remains live.

## Impact

A result that appears complete can leave nested commands running without an obvious model-visible control path. Depending on the command, those processes may continue using CPU, memory, file descriptors, sockets, locks, subprocesses, network activity, or filesystem state until they exit or are found through another route.

This is not evidence of a literal Rust memory leak, and this report does not assign a security severity. It is a control-visibility defect with operational resource-retention risk.

## Minimal reproduction

`yield_time_ms` lets each nested command return a session ID while its process remains live. This example deliberately keeps only `.output`:

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

An [executable negative reproduction](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5) demonstrates the contradiction: the manager still lists two live nested sessions while the model-visible result omits both IDs.

## Actual behaviour

```text
Script completed
Wall time ...
Output:
orphan-a|orphan-b
```

Both nested commands are still live, but their session IDs are absent from the final result.

## Expected behaviour

For a small matching set, the completing-cell result should report every still-live session created by that exact cell:

```text
Script completed
Background sessions still running: 6306, 11236
Wall time ...
Output:
orphan-a|orphan-b
```

`6306` and `11236` are illustrative IDs. The processes may continue running; the result restores the information needed to manage them.

The output is bounded. IDs are sorted numerically and at most 64 are displayed inline. If 71 processes match, an abridged rendering of the line is:

```text
Background sessions still running: 1, 2, ... 64 (+7 more)
```

The literal output contains all 64 visible IDs. Lists containing 64 or fewer matching IDs remain complete. During overflow, the omitted processes remain live and manager-owned, but not every handle is displayed in the completion line. The `64`-ID display limit is an [independent model-visible bound](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L57-L59), not an alias of the manager's [soft process-store capacity](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L70-L76).

## Behavioural boundary

The session-level unified-exec process manager remains the liveness authority. The lookup selects processes by exact creator-cell identity, includes entries whose process is considered live by manager state at that point, and returns IDs in numeric order. A process can exit immediately after the lookup. A process whose exit is already reflected in manager state before the lookup is excluded. The [manager query](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L168-L180) and its [direct filtering/ordering test](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod_tests.rs#L333-L395) define this contract.

Ordinary `Yielded` cell responses do not receive the completion warning. The warning is added after code-mode emitted-output truncation, while later global conversation-history limits still apply. The [final response path and formatter](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L201-L305) implement those boundaries.

The patch does not change process lifetime, automatic termination, persistence, pruning policy, shutdown handling, recovery, wake-up behaviour, JavaScript result schema, process ownership, public protocol schemas, event types, event-emission policy, or call-ID format. Existing response-item notifications can carry the intentionally changed completion text.

## Evidence and validation

- [Current code and test comparison](https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...77e7e3149df366236db2426596c23ebbe1d6bb48)
- [Five aggregate acceptance cases](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs)
- [Eight focused status tests](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L444-L612)
- [Direct manager query test](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod_tests.rs#L333-L395)
- [Focused Actions run on capped head `eb530466...`](https://github.com/teamleaderleo/codex/actions/runs/30220464228)
- [Local and Docker acceptance Actions run](https://github.com/teamleaderleo/codex/actions/runs/30217686056)

The validation record distinguishes the exact refs. The behaviourally equivalent pre-decoupling capped workspace passed the two compatibility tests once; exact current head `77e7e314...` has not been rerun for compatibility. Four Docker cases were selected and passed. The survivor case was excluded by the workflow filter for its documented host-path dependency and passed locally. The current guard-only head adds `skip_if_target_windows!` to four POSIX-command cases and awaits a public Wine-exec validation run. See the [commit-pinned validation record](https://github.com/teamleaderleo/codex/blob/173be554a9e61e80ea682e304d7b2925af5cac64/notes/code-mode-orphan-fix/publication/validation.md).

## Related issue

[#34866](https://github.com/openai/codex/issues/34866) reports that `Script completed` describes the JavaScript wrapper rather than the nested command and identifies discarded `session_id` or `exit_code` values as one possible consequence. It asks for a unified continuation lifecycle or explicit wrapper/process states. This report isolates that consequence as an independently reproducible exact-cell visibility defect with a bounded, visibility-only fix; it does not propose the broader lifecycle redesign requested in #34866.

This patch does not solve every broader lifecycle, cleanup, wake-up, process-group, or owner-loss problem.
