# When `Script completed` leaves live terminal sessions behind

Status: public-facing draft; unpublished.

This document explains a code-mode failure in which Codex can still own live nested terminal sessions after the model-visible result has lost the session IDs needed to control them. It also explains why the proposed fix restores visibility rather than changing process-lifecycle policy.

For the concise maintainer-facing versions, see the companion [issue draft](standalone-issue-layered.md) and [pull-request draft](pull-request-layered.md). A separate [works-cited index](works-cited.md) classifies primary code, executable evidence, historical context, and secondary investigation records.

## The problem in plain English

A code-mode JavaScript cell can launch nested `tools.exec_command()` calls, receive session IDs for processes that remain alive, and then keep only each command's `.output`. The JavaScript cell can finish successfully and the outer result can say `Script completed`, even though those terminal sessions are still running.

Codex has not forgotten the processes internally. The session-level unified-exec process manager still owns and tracks them. What disappears is the model-visible control information: the numeric session IDs used to poll, send input to, or terminate those live terminals.[^negative-proof]

That distinction matters. Background terminal persistence is intentional in Codex; servers, watchers, and interactive commands may legitimately outlive a cell or turn. The defect is not simply that a process remains alive. The defect is that a terminal code-mode result can stop exposing the handles needed to manage work that remains alive.

## Why this matters

A live process without an obvious model-visible control path may continue consuming CPU, memory, file descriptors, sockets, locks, subprocesses, network activity, or filesystem state until it exits naturally or is found and terminated by another route.

The original incident involved long-lived browser and Node-related work after a task appeared complete. That incident context is secondary and partly private; raw rollout logs, machine paths, process listings, and user data are not published here. The public defect claim rests on an executable repository reproduction rather than on private evidence alone.

This should not be described as proof of a literal Rust memory leak. The manager still owns reachable process objects. A more accurate description is **lost session-handle visibility with operational resource-retention risk**.

## Minimal reproduction

Each command below prints a marker and then remains alive long enough to yield a background session ID. The JavaScript deliberately projects the returned objects down to `.output`, discarding those IDs:

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

Before the fix, the model-visible result can be:

```text
Script completed
Wall time ...
Output:
orphan-a|orphan-b
```

At that point, the unified-exec manager still lists two live terminal sessions, but the outer result contains neither session ID.[^negative-proof]

The proposed result is:

```text
Script completed
Background sessions still running: 6306, 11236
Wall time ...
Output:
orphan-a|orphan-b
```

The numbers are illustrative. The processes may continue running. The difference is that the model retains the information needed to manage them.

## What the system was doing

The failure crosses three ownership boundaries:

1. **Code mode owns the JavaScript cell.** A cell can call nested tools and decide which parts of their returned values to retain or emit.
2. **Unified exec owns the process.** Once a yielded process is stored, the existing process manager owns the live process independently of the JavaScript object that contained a copied numeric ID.
3. **Terminal rendering owns the final model-visible status.** Before the patch, the outer status was derived only from the code-cell runtime response. It did not consult the process manager for surviving sessions.

The baseline already carried code-mode cell identity at nested tool dispatch, but that identity was not retained on the stored process entry. Once JavaScript discarded its copied `session_id`, terminal rendering had no exact, typed way to recover the live sessions created by the completing cell.[^baseline-path]

## The selected fix

The patch reconnects existing state rather than creating a new lifecycle system.

### 1. Capture existing typed cell identity

At nested `exec_command` dispatch, `ToolCallSource` already distinguishes direct tool calls from code-mode calls and already carries the code-mode cell ID. The patch converts that existing value into optional typed creator metadata.[^dispatch]

```rust
let creator_cell_id = match source {
    ToolCallSource::Direct => None,
    ToolCallSource::CodeMode { cell_id, .. } => Some(CellId::new(cell_id)),
};
```

This is crate-internal metadata. It is not a new JavaScript field, CLI argument, network parameter, app-server protocol item, or user-supplied ownership label.

### 2. Carry and store the attribution

`UnifiedExecContext` carries the optional creator cell to process creation, and the existing `ProcessEntry` stores it beside the manager-owned process and logical session ID.[^context-entry]

JavaScript may then discard its copied return object without erasing the manager's process state or the retained attribution.

### 3. Query the existing liveness authority

The process manager exposes a read-only query for process IDs that:

- match the exact creator `CellId`;
- have not exited;
- exclude direct or unattributed entries; and
- are returned in deterministic numeric order.[^manager-query]

The query acquires the existing process-store mutex, scans the current in-memory entries without awaiting inside the scan, sorts the matching IDs, and releases the lock. It does not wait for child processes, terminate anything, read process output, or change lifecycle state.

### 4. Report only at terminal cell boundaries

Code-mode response handling performs that lookup only for terminal `Result` or `Terminated` responses. Ordinary `Yielded` responses remain unchanged.[^terminal-rendering]

The emitted code-mode output is truncated first; the status header is prepended afterwards. Therefore a large emitted payload cannot displace the live-session warning at that specific truncation boundary. The complete tool result remains subject to later global conversation-history limits.

## Why exact creator-cell attribution matters

A simpler implementation could list every live terminal in the current Codex session. That would reveal the original symptom, but it would be wrong: one completing cell could disclose unrelated sessions created by another cell.

The final contract is therefore not merely “show some live sessions.” It is:

> Report the still-live sessions created by the exact code-mode cell whose terminal result is being rendered.

A two-cell acceptance test exists specifically to reject the global-list shortcut.[^acceptance]

## Why the patch does not kill the processes

Automatically terminating the matching processes would be a different product decision.

Codex intentionally supports long-running terminals across cells and turns. A development server, watcher, REPL, or interactive process may be expected to remain live after the launching JavaScript cell finishes. Blocking completion until every nested terminal exits would turn background work into foreground work and could hang cells indefinitely.

This patch therefore separates two questions:

- **Visibility:** does the model still know which sessions are live?
- **Lifecycle:** when should those sessions stop?

Patch 1 answers only the first question. Cleanup policy, owner-loss recovery, event-driven wake-up, hidden-subagent policy, and automatic termination remain separate design topics. See [rejected and deferred paths](works-cited.md#rejected-and-deferred-implementation-paths).

## Threat-model and information-disclosure review

The new disclosure is intentionally narrow:

- current-session manager state only;
- exact creator-cell matches only;
- still-live logical numeric session IDs only;
- no command text;
- no environment variables;
- no process output;
- no filesystem paths;
- no OS PIDs;
- no unrelated cell's sessions.

The patch exposes only session IDs that the same code-mode cell could already receive from nested `exec_command` results. The failure occurs because JavaScript can project those values away; the patch restores that control information at the terminal boundary.

The evidence does not establish privilege escalation, sandbox escape, cross-user disclosure, or attacker-controlled persistence, so this should not automatically be labelled a security vulnerability. It is a reliability and resource-management defect whose practical impact depends on the processes left running.

## Tests that shaped the design

The final tests are not one large snapshot. They encode separate behavioural invariants.[^acceptance]

1. **Multiple live sessions and numeric ordering.** Two yielded commands discard their JavaScript session IDs; the terminal result must report both real manager-owned IDs exactly once and in numeric order.
2. **Exited-session exclusion.** A deterministic PID/filesystem handshake proves one process has exited before cell completion; only the survivor may be reported.
3. **Truncation placement.** Large emitted output may be truncated, but the separate status item must retain the warning and session ID.
4. **Yielded neutrality.** An ordinary yielded code-cell response must not contain the completion-only warning.
5. **Exact cell isolation.** A completing cell must not disclose another cell's still-live process.

A direct, network-independent manager unit test separately covers exact-cell inclusion, another-cell exclusion, unattributed-entry exclusion, exited-entry exclusion, and numeric ordering.[^manager-test]

### Why the tests moved

The first acceptance implementation created a standalone integration-test binary and duplicated helpers. Review found explicit repository comments establishing one aggregate integration-test binary and an existing code-mode suite. The final cases live under `tests/suite/code_mode/orphan_sessions.rs` and reuse the parent suite's helpers.[^test-convention]

That change was not cosmetic. It reduced duplicate harness logic, avoided another integration binary, and aligned focused nextest filtering with the repository's documented topology.

### Why fixed sleeps were removed

An early survivor test used `sleep 1` and then waited two seconds. That tested elapsed time rather than the state transition that mattered. The final test uses a bounded release-and-poll handshake: the short process writes its PID, waits for a release file, and a foreground command confirms the process has exited before allowing the JavaScript cell to complete.[^test-evolution]

## Validation and limits

Repository-native focused validation recorded on Linux aarch64:[^validation-summary]

- `just fmt`: passed;
- `just fix -p codex-core`: passed;
- four focused unit tests: passed;
- five aggregate acceptance cases: passed;
- two existing compatibility tests: 20/20 executions passed on the final candidate;
- the same compatibility tests: 20/20 passed on the exact upstream base;
- clean worktree and `git diff --check`: passed.

A matched broad `codex-core` run remained red on both candidate and exact base. Exact-base comparison and focused reruns left no persistent candidate-only failure. The broad project suite is not claimed as green.[^validation-summary]

The complete workspace suite was not run. The focused tests compile and exercise the affected `codex-core` paths, but they do not establish every Codex product surface, operating system, remote environment, or private deployment path.

The manager lookup is a point-in-time observation. A process can exit immediately after the query. The status reports what the manager considers live at formatting time; it does not promise future liveness.

## Alternatives considered

<details>
<summary>Why not infer ownership from JavaScript output?</summary>

The confirmed failure exists precisely because JavaScript can discard the returned object or retain only `.output`. An implementation that trusts emitted JavaScript values cannot recover information that was projected away.
</details>

<details>
<summary>Why not append the session ID to nested command output?</summary>

That would mix control metadata with command output and would still depend on JavaScript preserving or emitting the field. It would also alter an established result contract without solving full-result discard.
</details>

<details>
<summary>Why not encode the cell ID in nested call-ID strings?</summary>

A feasibility prototype showed that prefix filtering could work, but it would turn an opaque naming convention into an ownership API, introduce collision and tracing concerns, and couple correctness to string formatting. The final patch retains typed `CellId` provenance instead.[^call-id-prototype]
</details>

<details>
<summary>Why not add a second per-cell process registry?</summary>

The existing process manager already owns process handles and defines liveness. A second registry would need duplicate insertion, exit, pruning, cleanup, and race handling and could disagree with the source of truth.
</details>

<details>
<summary>Why not add a new JavaScript or app-server schema field?</summary>

The nested JavaScript result already contains `session_id`; the problem is that JavaScript can discard the object. A new field has the same retention problem. A new public protocol event would broaden the patch into client compatibility, ordering, and UI design.
</details>

<details>
<summary>Why not add a display cap?</summary>

The purpose of the line is to preserve live control handles. A separate display cap would knowingly omit some handles. The selected implementation reports the complete exact-cell point-in-time list; the full tool result remains subject to later global conversation-history limits. A future cap should first define another way to discover omitted sessions.
</details>

## Historical context

The architecture reflects several earlier upstream changes:

- Unified exec began as a PTY-backed reusable session feature with numeric session IDs, persistence, isolation, timeouts, and bounded output in PR [#3288](https://github.com/openai/codex/pull/3288).[^unified-history]
- Tool execution was centralised under specs, handlers, routing, registry dispatch, and shared invocation context in PR [#4510](https://github.com/openai/codex/pull/4510).[^tool-history]
- Persistent JavaScript execution entered as the feature-gated `js_repl` in PR [#10674](https://github.com/openai/codex/pull/10674).[^js-history]
- Code mode moved from an external Node runner to an in-process Rust/V8 runtime in PR [#15276](https://github.com/openai/codex/pull/15276).[^v8-history]
- Per-cell lifecycle state moved into a single-owner actor in PR [#28599](https://github.com/openai/codex/pull/28599).[^actor-history]

That history explains the patch boundary: the code-mode cell actor owns cell lifecycle, the unified-exec manager owns process liveness, and the nested tool handler is where typed provenance enters unified exec.

## Methodology and provenance

One human coordinated four separate ChatGPT chats with bounded lanes for implementation, executable testing, architecture review, and publication research. Code, tests, analysis, and prose were treated as proposals until checked against primary source, executable tests, exact comparisons, independent review, or explicit human judgement.

This provenance is optional and is not evidence of correctness by itself. Raw private chats, rollout logs, machine-specific paths, and user data remain private by default.

## Works cited

The full classified bibliography is in [works-cited.md](works-cited.md). The most important primary sources are the final comparison, the immutable negative reproduction, the production code links, the aggregate acceptance module, the manager unit test, and the repository's aggregate-test convention.

[^negative-proof]: [Immutable negative reproduction, commit `7298dcf4`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5).
[^baseline-path]: [Baseline nested-exec handler](https://github.com/teamleaderleo/codex/blob/20dafe201d91d4405eef05ecd1db0257f13a9ac8/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs) and [baseline terminal response handling](https://github.com/teamleaderleo/codex/blob/20dafe201d91d4405eef05ecd1db0257f13a9ac8/codex-rs/core/src/tools/code_mode/mod.rs).
[^dispatch]: [`ExecCommandHandler` creator-cell capture](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L132-L138).
[^context-entry]: [`UnifiedExecContext` and stored creator field](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L76-L99) and [`ProcessEntry`](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L189-L199).
[^manager-query]: [`live_process_ids_created_by_cell`](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L168-L180).
[^terminal-rendering]: [Terminal-only lookup and response handling](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/code_mode/mod.rs#L199-L255) and [status formatting](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/code_mode/mod.rs#L268-L300).
[^acceptance]: [Final aggregate acceptance module](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs).
[^manager-test]: [Direct manager-query unit test](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod_tests.rs#L332-L395).
[^test-convention]: [Single aggregate integration-test binary](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/all.rs#L1-L9) and [existing code-mode suite](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode.rs#L59-L77).
[^test-evolution]: [Aggregate-suite test-polish commit `cc01596`](https://github.com/teamleaderleo/codex/commit/cc01596b75abb38335ecdfe07688f155b0dd15a9) and [supplemental test commit `7602167`](https://github.com/teamleaderleo/codex/commit/760216784efaee1ba6a3b1250349f31d5f91c7ca).
[^validation-summary]: [Works-cited validation summary and disclosure boundary](works-cited.md#executable-validation-summary).
[^call-id-prototype]: [Rejected call-ID-prefix feasibility prototype, commit `cffcd8dc`](https://github.com/teamleaderleo/codex/commit/cffcd8dca93ab5c2ff8fa1af262ae7676f5b97a9).
[^unified-history]: [Unified execution, commit `c09ed74a`](https://github.com/openai/codex/commit/c09ed74a163ecea69c32d61ab2bfa1c8490eb611).
[^tool-history]: [Tool-system refactor, commit `33d3ecbc`](https://github.com/openai/codex/commit/33d3ecbccca4b92cfb2a77002387de30302f337f).
[^js-history]: [Feature-gated JavaScript REPL, commit `42e22f3b`](https://github.com/openai/codex/commit/42e22f3bde6c851422eb4f7b502457fe86ba91db).
[^v8-history]: [Code mode on V8, commit `e4eedd61`](https://github.com/openai/codex/commit/e4eedd6170580d5b06fb539635a78f261a6b7369).
[^actor-history]: [Code-mode cell actor, commit `e2f074e1`](https://github.com/openai/codex/commit/e2f074e16c522bfa55d9bcd344a5ea0ba5a4580f).