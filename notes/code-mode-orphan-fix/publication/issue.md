# Code-mode completion can omit IDs for still-live nested exec sessions

Related: [#34866](https://github.com/openai/codex/issues/34866) reports the broader mismatch between wrapper completion and nested-process state, including JavaScript forwarding only `output`. This report isolates one independently fixable case: the final cell response loses model-visible control handles even though the unified-exec manager still owns the live processes.

The proposed direction restores those handles from existing manager state. It does not redesign lifecycle semantics or add protocol fields.

## Reproduction

```js
const outputs = (await Promise.all([
  tools.exec_command({ cmd: "printf orphan-a; sleep 60", yield_time_ms: 250 }),
  tools.exec_command({ cmd: "printf orphan-b; sleep 60", yield_time_ms: 250 }),
])).map(({ output }) => output);

text(outputs.join("|"));
```

The cell deliberately keeps only each command's `.output` and discards the returned `session_id`.

An [executable negative reproduction](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5) confirms both nested sessions remain listed by the unified-exec manager after the cell finishes, while the model-visible completion result omits their IDs.

## Observed behaviour

```text
Script completed
Wall time ...
Output:
orphan-a|orphan-b
```

The nested commands remain live, but the response no longer contains the handles needed to inspect, continue, or terminate them.

## Proposed behaviour

A terminal cell response could include the matching live handles in its existing status text:

```text
Script completed
Background sessions still running: 6306, 11236
Wall time ...
Output:
orphan-a|orphan-b
```

The exact wording and display bound are implementation choices. The required property is that a completing cell preserves access to manager-owned nested commands whose JavaScript result objects were discarded.

## Root cause

Nested tool dispatch already carries the originating code-mode cell ID. Yielded commands remain owned by the session-level unified-exec manager, but the final code-mode response is formatted from `RuntimeResponse` alone.

Once JavaScript discards a nested result object, the completion path has no cell-scoped path to identify and recover its `session_id`, even though the manager still has both the process and its logical ID.

[Current upstream `handle_runtime_response`](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/codex-rs/core/src/tools/code_mode/mod.rs#L201-L275) still formats terminal cell output without an equivalent manager lookup.

## Proposed direction

1. Retain the originating typed `CellId` on manager-owned process entries created through code mode.
2. For a terminal cell response, query the existing manager for processes created by that exact cell whose manager-observed state remains live.
3. Include their logical session IDs in deterministic order in the model-visible status.

The query is read-only. It does not wait for, terminate, prune, or otherwise mutate any process.

## Liveness boundary

This would report manager-observed liveness at lookup time. Local process handles can expose exit directly; exec-server-backed entries rely on exit state already reflected in the manager. A recently exited remote process could therefore appear until that cached state advances.

That asymmetry already exists in `UnifiedExecProcess::has_exited()` and should be considered when maintainers choose whether this narrow status fix is desirable or whether broader lifecycle reporting from #34866 should land first.

## Scope

The focused fix leaves these unchanged:

- process ownership and lifetime;
- cleanup, pruning, polling, and wake-up policy;
- JavaScript result fields;
- public protocol schemas and event types;
- call-ID generation.

It reports only sessions created by the exact cell whose terminal response is being formatted, so one cell cannot claim another cell's live work.

## Design questions

- Should the warning appear only for successful `Result` responses, or for every terminal outcome, including failed `Result` and `Terminated`?
- Is manager-observed liveness acceptable for exec-server-backed processes, given that exit reflection may lag the underlying process?

## Technical notes

A focused prototype covers manager, formatter, and end-to-end regression cases. Additional implementation detail, validation history, and known limitations are documented in the [technical deep dive](https://github.com/teamleaderleo/codex/blob/review/code-mode-issue-ready/notes/code-mode-orphan-fix/publication/deep-dive.md).