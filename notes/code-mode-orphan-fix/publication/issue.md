# `Script completed` can omit session IDs for live nested commands

## What happened

A code-mode JavaScript cell can start nested terminal commands, keep only their `.output`, and discard the returned session IDs. The cell can then report `Script completed` while those commands are still running.

Codex still tracks the processes internally, but the final result no longer shows the handles needed to inspect, continue, or terminate them.

## Reproduction

```js
const outputs = (await Promise.all([
  tools.exec_command({ cmd: "printf orphan-a; sleep 60", yield_time_ms: 250 }),
  tools.exec_command({ cmd: "printf orphan-b; sleep 60", yield_time_ms: 250 }),
])).map(({ output }) => output);

text(outputs.join("|"));
```

An [executable negative reproduction](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5) confirms that the manager still lists both live sessions while the model-visible completion result omits their IDs.

## Actual behaviour

```text
Script completed
Wall time ...
Output:
orphan-a|orphan-b
```

## Expected behaviour

```text
Script completed
Background sessions still running: 6306, 11236
Wall time ...
Output:
orphan-a|orphan-b
```

The IDs above are illustrative. The processes may continue running; the result should preserve the information needed to manage them.

## Scope

The proposed fix reports only still-live processes created by the exact completing cell. IDs are sorted numerically, and the line is bounded to 64 IDs with an exact omitted-count suffix when necessary.

It does not change process ownership, lifetime, cleanup, polling, wake-up behaviour, JavaScript result fields, or public protocol shapes.

## Evidence

- [Current upstream status path](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/codex-rs/core/src/tools/code_mode/mod.rs#L201-L275), which still formats completion without an equivalent manager lookup
- [Current code and test comparison](https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...77e7e3149df366236db2426596c23ebbe1d6bb48)
- [Focused Actions run](https://github.com/teamleaderleo/codex/actions/runs/30220464228)
- [Local and Docker acceptance run](https://github.com/teamleaderleo/codex/actions/runs/30217686056)
- [Detailed validation record](https://github.com/teamleaderleo/codex/blob/review/code-mode-final-draft/notes/code-mode-orphan-fix/publication/validation.md)

A targeted Wine-exec run was also attempted on the current guarded head, but an unrelated Bazel BUILD/macro mismatch stopped analysis before any Rust test ran.

## Related reports

[#34866](https://github.com/openai/codex/issues/34866) describes the broader contradiction between wrapper completion and nested-process state. Its discussion distinguishes that runtime/interface problem from the model-side duplicate-command behaviour in [#33816](https://github.com/openai/codex/issues/33816).

This report isolates one narrower defect: when the copied JavaScript `session_id` is discarded, the completing-cell result should recover the still-live handles already retained by the process manager.
