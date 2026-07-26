# How code-mode completion can lose live session handles

This document explains the failure mechanism, selected implementation, bounded output, test design, validation boundaries, and review-size trade-off. The concise publication texts are the [issue](issue.md) and [pull-request draft](pull-request.md). Primary evidence is classified in [sources.md](sources.md), and execution details are in [validation.md](validation.md).

## Problem mechanism

A code-mode JavaScript cell can call nested `tools.exec_command()` operations. If a nested command yields while it remains live, its result contains a numeric session ID and command output. JavaScript can then keep only `.output` and discard the copied session ID:

```js
const outputs = (await Promise.all([
  tools.exec_command({ cmd: "printf orphan-a; sleep 60", yield_time_ms: 250 }),
  tools.exec_command({ cmd: "printf orphan-b; sleep 60", yield_time_ms: 250 }),
])).map(({ output }) => output);

text(outputs.join("|"));
```

The copied JavaScript values do not own the processes. The session-level unified-exec process manager still retains the stored processes. Before this patch, the final code-mode status was derived from the runtime response and did not recover the discarded session IDs from manager state. The result could therefore say `Script completed` while live nested commands remained manager-owned without model-visible handles.

The [negative reproduction](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5) preserves this before-state as an executable test.

## Operational impact

A live command without an obvious model-visible control path may continue using CPU, memory, sockets, file descriptors, locks, descendants, network activity, or filesystem state until it exits naturally or is found through another route.

This is not proof of a literal Rust memory leak. The manager retains reachable process objects. The narrower description is **lost session-handle visibility with operational resource-retention risk**. The evidence does not establish privilege escalation, sandbox escape, cross-user disclosure, or a security severity.

## Ownership boundaries

The failure crosses three responsibilities:

1. **Code mode owns the cell lifecycle.** The cell decides which nested return values it keeps or emits.
2. **Unified exec owns process liveness.** A stored process remains manager-owned independently of the copied JavaScript result.
3. **The final-result formatter owns the model-visible completion status.** It is the last reliable place to restore control information after JavaScript discards it.

The patch connects those existing responsibilities. It does not move process ownership into code mode or create another process registry.

## Production code path

### 1. Preserve existing creator-cell provenance

Nested tool dispatch already knows whether an invocation came directly from the model or from a code-mode cell. [`ExecCommandHandler`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L132-L138) converts the existing code-mode cell value into an optional typed `CellId` and attaches it to `UnifiedExecContext`.

This metadata is crate-internal. It is not user input, a JavaScript field, a protocol event, or a call-ID encoding.

### 2. Store provenance beside the owned process

[`UnifiedExecContext`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L76-L99) carries the optional creator to process creation. [`ProcessEntry`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L189-L200) stores it beside the manager-owned process and logical session ID, and [`store_process`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/process_manager.rs#L944-L976) copies the invocation metadata into that entry.

In Rust terms, the manager retains an `Arc<UnifiedExecProcess>`. JavaScript receives only a copied integer. Dropping or projecting away the JavaScript object does not drop the manager's process entry.

### 3. Query the liveness authority

[`live_process_ids_created_by_cell`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L168-L180) locks the existing process store, selects entries whose typed creator matches the exact `CellId`, excludes entries whose process reports that it exited, extracts logical session IDs, and sorts them numerically.

The query is read-only. It does not terminate a process, wait for output, change pruning, or mutate lifecycle state. The direct [manager unit test](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod_tests.rs#L333-L395) covers exact-cell inclusion, other-cell and unattributed exclusion, deterministic exited-entry filtering, and numeric ordering.

### 4. Report only on final cell outcomes

[Response handling](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L201-L269) performs the manager lookup for `RuntimeResponse::Result` and `RuntimeResponse::Terminated`. `RuntimeResponse::Yielded` receives no completing-cell warning because the cell itself is still active and resumable.

### 5. Add the warning after emitted-output truncation

The code-mode emitted content is truncated before the status header is prepended. The warning therefore sits outside that specific emitted-output truncation step. A large emitted payload cannot remove the warning at that boundary. The complete tool result remains subject to later global conversation-history limits.

## Point-in-time semantics

The manager query describes one moment. A selected process can exit immediately after lookup. A process whose exit is already reflected in manager state before lookup is excluded.

The status means:

> These were the matching processes that the existing manager considered live when the final result was formatted.

It does not promise that every displayed process will remain live by the time the next model action occurs.

## Exact-cell semantics

Listing every live process in the Codex session would violate attribution: one completing cell could report another cell's unrelated process.

The selected contract is:

> Report only the still-live processes created by the exact code-mode cell whose final result is being formatted.

The two-cell acceptance case rejects the global-list shortcut.

## Independent 64-ID display limit

Model-visible output needs a hard bound independent of internal storage policy:

```rust
// Bound independently because this fragment enters model-visible context.
const MAX_INLINE_BACKGROUND_SESSION_IDS: usize = 64;
```

The unified-exec manager separately has a soft process-store capacity that currently also equals 64. The two values are deliberately not aliases:

- manager capacity controls internal process-store policy;
- formatter capacity controls model-visible response size;
- either policy can change without silently changing the other.

The formatter sorts the full matching list first, displays the first 64 IDs, and calculates the exact remainder:

- 0 matches: no warning;
- 1–64 matches: every matching ID is shown;
- 65 matches: 64 IDs plus `(+1 more)`;
- 71 matches: 64 IDs plus `(+7 more)`.

Under the current equal constants, overflow is a defensive bound rather than an expected routine path. That does not make it redundant: model-visible output should remain bounded even if internal storage policy changes or the store temporarily exceeds its soft capacity.

## Unchanged boundaries

The patch does not change process ownership, process lifetime, automatic termination, persistence, pruning policy, shutdown handling, recovery, wake-up behaviour, JavaScript result schema, public protocol schemas, event types, event-emission policy, or call-ID format.

Existing response-item notifications can carry the intentionally changed completion text. That is an observable payload-content change through an existing path, not a new protocol shape or emission rule.

## Test design

### Focused status and manager tests

The capped head has eight formatter/status tests and one direct manager-query test. They cover final-response selection, completed/failed/terminated status, exact limit, overflow cap, sort-before-take, exact omitted count, empty matches, yielded neutrality, exact-cell filtering, exited-entry filtering, and numeric ordering.

The manager test is the deterministic evidence for exited-entry filtering. It avoids shell and scheduler timing.

### Aggregate acceptance cases

The five cases cover:

1. multiple discarded live sessions are reported;
2. an exited nested session is excluded while a survivor remains;
3. large emitted output does not remove the warning;
4. ordinary yielded cell responses remain warning-free;
5. only sessions created by the completing cell are reported.

The survivor case uses a bounded OS-exit handshake. The short process writes its PID, waits for a release file, and a foreground command polls until the OS no longer reports the process before the cell completes. The direct manager test, rather than this shell handshake, is the deterministic proof of manager-side exited filtering.

### Local, Docker, and Wine target behaviour

The acceptance run selected all five cases locally and four cases for the Docker executor. The survivor case was excluded by the Docker workflow filter because its shell commands embed host `TempDir` paths not mounted into the container.

The current head adds `skip_if_target_windows!` to the four remote-capable cases that use POSIX shell commands. Wine-exec uses a native Linux test binary while targeting a Windows exec server, so `cfg(windows)` alone does not guard those command strings. The survivor case already carries `skip_if_remote!`.

The target-Windows guard commit has not yet received a public Wine-exec Actions run. This limitation is recorded rather than converted into an execution claim.

## Validation boundaries

The public execution record has three distinct refs:

1. The local and Docker acceptance run exercised the capped behaviour and final remote-test harness while the display limit was still expressed as an alias of the manager's equal capacity.
2. Capped head `eb530466...` changed the production definition to an independent literal `64` and passed the nine focused tests plus formatting, scoped fix, diff, worktree, and scope checks.
3. Current head `77e7e314...` adds only target-Windows skip guards to four POSIX-command acceptance cases. It has not yet received a new public Actions run.

The behaviourally equivalent pre-decoupling capped workspace passed two compatibility tests once. Those passes must not be attributed to the exact current head.

A previous broad `codex-core` comparison used candidate `3778e1fa...`, which was production-equivalent to the uncapped parent `760216...`, and the selected upstream base. It was red on both refs. No broad differential was run for the capped or guard-only heads, and the complete workspace suite was not run.

## Review size and staging

The current base-to-head diff is 903 changed lines, above the repository's 800-line guidance. The 527-line bespoke acceptance module dominates the total; production code remains comparatively small.

If maintainers request a split, the smallest coherent first stage is production provenance, manager query, bounded formatter, nine focused tests, and the primary discarded-handle acceptance reproduction. The exited-session, large-output, yielded-neutrality, exact-cell, and remote-routing cases can form a supplemental acceptance stage.

This staging option addresses reviewability. It is not required for runtime correctness.

## Alternatives considered

- Recover IDs from JavaScript output: fails when JavaScript discards the object.
- Append IDs to command output: mixes control metadata with program output and remains discardable.
- Encode creator identity in call-ID strings: turns an opaque identifier into an ownership API.
- Add a second per-cell registry: duplicates manager liveness and cleanup bookkeeping.
- Report every session process: violates exact-cell attribution.
- Wait for or terminate matching processes: changes lifecycle policy.
- Add a new JavaScript field or event: JavaScript can still discard it and compatibility scope expands.
- Alias the display cap to manager capacity: silently couples internal storage policy to model-visible output.

## Related issue and non-goals

[#34866](https://github.com/openai/codex/issues/34866) identifies discarded `session_id` or `exit_code` values as one consequence of contradictory wrapper/process completion semantics and proposes broader continuation-state changes. This patch isolates that consequence as a bounded visibility fix.

Patch 1 does not attempt automatic cleanup, process-group recovery, durable PID recovery, crash reclamation, parent wake-up, sandbox inspection, disk quotas or backpressure, or a public API for enumerating omitted overflow handles.
