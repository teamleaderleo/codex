# How code-mode completion can lose live session handles

This document records the implementation reasoning and validation boundaries behind the concise [issue](issue.md) and [pull-request draft](pull-request.md).

## The failure

A code-mode JavaScript cell can start nested commands and then keep only each result's `.output`:

```js
const outputs = (await Promise.all([
  tools.exec_command({ cmd: "printf orphan-a; sleep 60", yield_time_ms: 250 }),
  tools.exec_command({ cmd: "printf orphan-b; sleep 60", yield_time_ms: 250 }),
])).map(({ output }) => output);

text(outputs.join("|"));
```

The copied JavaScript values do not own the processes. The session-level unified-exec manager still retains the live processes, but the final code-mode result previously had no path to recover their discarded session IDs. It could therefore say `Script completed` without showing the handles needed to manage the still-running commands.

The [negative reproduction](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5) preserves this before-state as an executable test.

## Why this is an operational problem

A live command without an obvious model-visible control path may continue using CPU, memory, sockets, file descriptors, locks, descendants, network activity, or filesystem state until it exits or is found through another route.

This is not evidence of a literal Rust memory leak. The narrower description is **lost session-handle visibility with operational resource-retention risk**.

## Production data flow

### 1. Preserve existing creator-cell identity

Nested tool dispatch already knows whether an invocation came from a code-mode cell. [`ExecCommandHandler`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L132-L138) attaches the existing typed `CellId` to `UnifiedExecContext`.

This is crate-internal provenance, not a new user field, JavaScript result field, protocol event, or call-ID format.

### 2. Store provenance with the manager-owned process

[`UnifiedExecContext`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L76-L99) carries the optional creator. [`ProcessEntry`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L189-L200) stores it beside the logical session ID and manager-owned process, and [`store_process`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/process_manager.rs#L944-L976) copies it into the entry.

### 3. Query the existing liveness authority

[`live_process_ids_created_by_cell`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L168-L180) reads the existing process store, selects entries whose creator matches the exact `CellId`, excludes processes whose exit is already reflected in manager state, extracts logical session IDs, and sorts them numerically.

The query is read-only. It does not wait, terminate, prune, or mutate lifecycle state.

### 4. Report only on final cell outcomes

[Response handling](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L201-L269) performs the lookup for `RuntimeResponse::Result` and `RuntimeResponse::Terminated`. Ordinary `RuntimeResponse::Yielded` responses remain warning-free because the cell itself is still active and resumable.

### 5. Keep the warning outside emitted-output truncation

The code-mode emitted payload is truncated before the status header is prepended. A large emitted value therefore cannot remove the warning at that boundary. Later global conversation-history limits still apply to the complete tool result.

## Output contract

### Exact cell

Reporting every live session process would allow one completing cell to claim another cell's unrelated work. The contract is:

> Report only processes created by the exact cell whose final result is being formatted.

### Point-in-time liveness

The manager query describes one moment. A selected process may exit immediately after lookup. A process whose exit is already reflected before lookup is excluded.

### Independent 64-ID bound

Model-visible output has its own hard limit:

```rust
const MAX_INLINE_BACKGROUND_SESSION_IDS: usize = 64;
```

The manager separately has a soft process-store capacity that currently also equals 64. The values are intentionally not aliases: internal storage policy and model-visible output policy should be able to change independently.

The formatter sorts the complete matching list before taking the first 64 IDs and calculating the exact remainder:

- no matches: no warning;
- 1–64 matches: every matching ID is shown;
- 65 matches: 64 IDs plus `(+1 more)`;
- 71 matches: 64 IDs plus `(+7 more)`.

## What does not change

The patch does not change process ownership, process lifetime, automatic termination, persistence, pruning, shutdown handling, recovery, wake-up behaviour, JavaScript result fields, public protocol schemas, event types, event-emission policy, or call-ID format.

Existing response-item notifications can carry the changed completion text through the existing path.

## Tests

### Focused tests

The capped head has eight formatter/status tests and one direct manager-query test. Together they cover:

- final-result selection and yielded neutrality;
- exact-cell inclusion and unrelated-cell exclusion;
- deterministic exited-entry filtering;
- numeric ordering;
- empty, at-limit, and overflow formatting;
- sort-before-take and exact omitted counts.

The manager test is the deterministic proof of exited-entry filtering; it does not depend on shell or scheduler timing.

### Acceptance cases

The five aggregate cases cover:

1. discarded live session IDs are restored;
2. an exited nested session is excluded while a survivor remains;
3. large emitted output does not remove the warning;
4. ordinary yielded cell responses stay warning-free;
5. only sessions created by the completing cell are reported.

The survivor case uses a bounded OS-exit handshake. Its direct manager counterpart remains the authoritative deterministic test for liveness filtering.

## Local, Docker, and Wine routing

All five cases ran locally. Four remote-safe cases ran through the Docker/Linux executor. The survivor case embeds host `TempDir` paths, so it was excluded from the Docker filter and retains `skip_if_remote!`.

The current code head adds `skip_if_target_windows!` to the four cases whose command strings require POSIX shell syntax. Wine-exec runs the Rust test binary on Linux while sending commands to a Windows exec server, so `cfg(windows)` alone does not protect those command strings.

A targeted Wine-exec run was attempted on current code head `77e7e314...`. It reached the correct x86-64 Linux runner and Bazel target, but Bazel analysis stopped before Rust test discovery because `windows-sandbox-rs/BUILD.bazel` supplied `binary_test_target_compatible_with` to a `codex_rust_crate` macro version that did not accept it. No Patch 1 test executed, so the result is a blocked validation path rather than a behavioural failure.

## Current upstream drift

Current upstream snapshot [`95637f70...`](https://github.com/openai/codex/commit/95637f7056835fea66bdd0044414af480fc0fd74) still has the defect: [`handle_runtime_response`](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/codex-rs/core/src/tools/code_mode/mod.rs#L201-L275) formats status directly from `RuntimeResponse` and performs no manager lookup.

The surrounding implementation has moved since the selected base, so the branch will need a rebase rather than a mechanical cherry-pick. The design still maps directly:

- [`ToolInvocation`](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/codex-rs/core/src/tools/context.rs#L47-L71) still carries `source: ToolCallSource`.
- `ToolCallSource::CodeMode` still contains the runtime `cell_id`.
- The current [`ExecCommandHandler`](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L108-L133) currently ignores that source when constructing `UnifiedExecContext`.
- Current [`UnifiedExecContext` and `ProcessEntry`](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/codex-rs/core/src/unified_exec/mod.rs#L77-L181) still have no creator-cell field.

That means the bug remains relevant and the provenance approach remains suitable, but final upstream-ready code should be adapted and rerun on the then-current base.

## Validation boundaries

- Focused run `30220464228` validated the independent-cap head `eb530466...`: nine focused tests, formatting, scoped fixes, diff checks, and a clean worktree passed.
- Run `30217686056` validated the capped behaviour and final remote-test harness before the display constant was decoupled: five local acceptance cases, four selected Docker cases, and two compatibility tests passed.
- Current code head `77e7e314...` differs from `eb530466...` only by target-Windows test-routing guards.
- No complete workspace run or final-head broad differential is claimed.

See [validation.md](validation.md) for exact refs and commands.

## Related issue landscape

These reports concern adjacent parts of background-process behaviour, but they are not interchangeable:

- [#34866](https://github.com/openai/codex/issues/34866): wrapper completion can contradict nested-process state; explicitly discusses discarded `session_id` or `exit_code` values.
- [#33816](https://github.com/openai/codex/issues/33816): model-side loss of a yielded session can lead to false completion claims and duplicate command attempts.
- [#14731](https://github.com/openai/codex/issues/14731): proposes keeping a turn active while unified-exec work remains live.
- [#15723](https://github.com/openai/codex/issues/15723) and [#32188](https://github.com/openai/codex/issues/32188): request event-driven wake-up when background work completes.
- [#13733](https://github.com/openai/codex/issues/13733): documents the cost of repeated model-driven polling.

Patch 1 addresses only the lost-handle visibility case. It does not choose a continuation, polling, detachment, or wake-up policy.

## Review size

The current base-to-head diff is 903 changed lines, above the repository's 800-line guidance. The 527-line acceptance module dominates the total; production code is comparatively small.

If maintainers request a split, the smallest coherent first stage is the production change, nine focused tests, and the primary discarded-handle acceptance reproduction. The remaining acceptance cases can follow separately.

## Alternatives rejected

- Recover IDs from JavaScript output: impossible after JavaScript discards the object.
- Append IDs to command output: mixes control metadata with program output and remains discardable.
- Encode creator identity in call IDs: turns an opaque identifier into an ownership API.
- Add another per-cell registry: duplicates the existing manager's liveness and cleanup bookkeeping.
- Report every session process: violates exact-cell attribution.
- Wait for or terminate matching processes: changes lifecycle policy.
- Add a new JavaScript field or protocol event: JavaScript can still discard it and compatibility scope expands.
- Reuse the manager's soft capacity as the display limit: silently couples internal storage policy to model-visible output.