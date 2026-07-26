# Agent 3 code walkthrough: how Patch 1 restores lost live-session visibility

Status: internal engineering record. This document is written for a reader who can follow code but does not yet read Rust fluently. It is not part of the clean upstream candidate and should not be pasted wholesale into the public issue.

Reviewed refs:

- upstream base: `61a44880a85d2fd0d8770908dea5733495e571c8`
- final clean candidate: `760216784efaee1ba6a3b1250349f31d5f91c7ca`
- final comparison: `61a44880a85d2fd0d8770908dea5733495e571c8...760216784efaee1ba6a3b1250349f31d5f91c7ca`

## The whole patch in one sentence

A code-mode cell can lose the copied session IDs returned by nested `exec_command` calls while the unified-exec process manager still owns the live processes; Patch 1 remembers which cell created each stored process and, when that exact cell finishes, asks the existing manager which of its processes are still live and reports their IDs in the terminal status.

A compact mental model is:

```text
code-mode cell
    -> nested exec tool invocation already carries cell identity
    -> unified-exec invocation context carries that identity
    -> stored process entry retains that identity
    -> existing process manager answers exact-cell + live-only query
    -> terminal code-mode result displays the surviving session IDs
```

The process is not newly created by this patch, newly persisted by this patch, or automatically terminated by this patch. The missing association is restored so that model-visible control information survives even when JavaScript projects the nested result down to `.output`.[^agent1-diagnosis]

## Why this is the right problem statement

The original incident looked like a broad process leak: long-lived browser and Node work remained after a task and consumed substantial resources. Investigation then separated three facts that initially looked like one bug:

1. unified-exec background processes are intentionally allowed to survive a code cell or turn;
2. the manager owns the live process independently of the JavaScript object returned to code mode;
3. the outer terminal code-mode result did not consult manager state, so a copied `session_id` could be discarded and never restored.

That changed the diagnosis from “kill anything left after the cell” to the narrower contract:

> Preserve existing process lifetime, but do not let a terminal code-mode result hide the control IDs for still-live processes created by that completing cell.

Agent 1's reconstruction documents the evidence transitions, including the initially missed wait record, the distinction between copied JavaScript values and manager ownership, and the rejected interpretation that persistence itself was the defect.[^agent1-history]

## Historical architecture: why these boundaries exist

The current code is the result of several earlier architectural changes:

- Unified exec began as a PTY-backed reusable session mechanism with numeric session IDs, persistence, timeouts, bounded output, and multi-session isolation in upstream PR `#3288`.[^unified-exec-origin]
- Tool execution was later centralised under tool specs, handlers, routing, registry dispatch, telemetry, and shared invocation context in PR `#4510`. That history makes the tool handler the natural provenance-entry boundary.[^tool-refactor]
- Persistent JavaScript execution first appeared as feature-gated `js_repl` work in PR `#10674`.[^js-repl]
- Code mode later moved from an external Node runner to an in-process V8 runtime driven by Rust while preserving the model-facing `exec`, `wait`, and `tools.*` surface in PR `#15276`.[^v8]
- Cell lifecycle was then isolated into a dedicated actor with a single writer in PR `#28599`; session-level registries and facilities remained outside the cell actor.[^cell-actor]

The historical through-line matters because it argues against a broad rewrite. The cell actor owns code-cell lifecycle. The unified-exec manager owns process liveness. The handler is where typed tool-call provenance crosses into unified exec. Patch 1 connects those existing responsibilities rather than moving them.

## Before the patch: the exact information-loss path

Consider this code-mode JavaScript:

```js
const outputs = (await Promise.all([
  tools.exec_command({ cmd: "printf orphan-a; sleep 60", yield_time_ms: 250 }),
  tools.exec_command({ cmd: "printf orphan-b; sleep 60", yield_time_ms: 250 }),
])).map(({ output }) => output);

text(outputs.join("|"));
```

Each nested command can yield while remaining alive. The returned object includes a copied numeric `session_id` and the command `output`. JavaScript then deliberately retains only `output`.

Before Patch 1:

1. the manager still owned each live process;
2. the JavaScript copies of the session IDs were discarded;
3. the code cell completed successfully;
4. `handle_runtime_response` produced `Script completed` based only on the cell response;
5. no remaining model-visible path disclosed the still-live session IDs.

The immutable negative reproduction proves that contradiction directly: the manager lists two live background terminals while the outer model-visible result says `Script completed` and contains no session information.[^negative-test]

## File-by-file production walkthrough

### 1. Capture the existing creator-cell identity at nested exec dispatch

File:

[`codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs` lines 132-138](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L132-L138)

The relevant code is conceptually:

```rust
let creator_cell_id = match source {
    ToolCallSource::Direct => None,
    ToolCallSource::CodeMode { cell_id, .. } => Some(CellId::new(cell_id)),
};

let context = UnifiedExecContext::new(session.clone(), turn.clone(), call_id.clone())
    .with_creator_cell_id(creator_cell_id);
```

`ToolCallSource` already tells Codex whether the tool invocation came directly from the model or from a code-mode cell. Patch 1 does not invent a new user input or parse JavaScript. It retains existing typed internal metadata.

`Option<CellId>` means:

- `Some(cell_id)`: this nested process came from a known code-mode cell;
- `None`: it was direct or otherwise not attributed to a code-mode cell.

Why this location is correct:

- it is the first unified-exec-specific boundary that receives the typed invocation source;
- it avoids guessing from command text, output, or call-ID strings;
- direct calls remain unchanged;
- the value is crate-internal rather than a new public protocol field.

Agent 1's investigation found that baseline code already possessed `ToolCallSource::CodeMode` but discarded it before process storage. That observation directly informed this first change.[^agent1-provenance]

### 2. Carry the creator identity through the invocation context

File:

[`codex-rs/core/src/unified_exec/mod.rs` lines 76-99](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L76-L99)

Patch 1 adds:

```rust
pub creator_cell_id: Option<CellId>,
```

and a builder:

```rust
pub fn with_creator_cell_id(mut self, creator_cell_id: Option<CellId>) -> Self {
    self.creator_cell_id = creator_cell_id;
    self
}
```

`UnifiedExecContext` is invocation-scoped metadata. It already carries the session, turn, and call ID into unified exec. Creator-cell identity belongs here because it is known at invocation time and needed if a process becomes durable manager state.

The builder consumes `self`, mutates the field, and returns the updated value. This is a common Rust builder pattern. It does not add a public API surface outside the crate.

A maintainer could reasonably prefer a future general `ProcessOrigin` enum over `Option<CellId>`, but that would establish a broader origin model with more variants and policy. For this patch, the optional field represents exactly the distinction the existing call source provides without introducing a new architectural pattern.

### 3. Store creator identity beside the manager-owned process

Files:

- [`unified_exec/mod.rs` lines 189-199](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L189-L199)
- [`unified_exec/process_manager.rs`, stored-process construction](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/process_manager.rs)

The stored process entry gains:

```rust
creator_cell_id: context.creator_cell_id.clone(),
```

This is the decisive ownership step. JavaScript receives a copied integer. The manager stores an `Arc<UnifiedExecProcess>` and the metadata needed to identify its creator later.

The `clone()` here clones the small `Option<CellId>` value, not the operating-system process. The process itself is already shared through `Arc`.

Relevant Rust concepts:

- `Arc<T>` is an atomically reference-counted shared owner. Multiple async tasks or manager structures can hold references to the same process object safely.
- `Weak<T>` is a non-owning reference used where a strong reference would create a cycle. The process entry keeps a weak link back to the session.
- Cloning an `Arc` increments a reference count; it does not duplicate the process.
- Dropping the JavaScript result object has no effect on this Rust-owned process entry.

This code embodies the investigation's core correction: JavaScript did not own the live process. Therefore the durable creator association must be stored where the process is owned, not where its copied result happens to be rendered.[^agent1-manager-ownership]

### 4. Ask the existing manager for exact-cell, live-only IDs

File:

[`codex-rs/core/src/unified_exec/mod.rs` lines 168-180](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L168-L180)

The new query is:

```rust
pub(crate) async fn live_process_ids_created_by_cell(&self, cell_id: &CellId) -> Vec<i32> {
    let store = self.process_store.lock().await;
    let mut process_ids = store
        .processes
        .values()
        .filter(|entry| {
            entry.creator_cell_id.as_ref() == Some(cell_id) && !entry.process.has_exited()
        })
        .map(|entry| entry.process_id)
        .collect::<Vec<_>>();
    process_ids.sort_unstable();
    process_ids
}
```

Line by line:

1. `lock().await` waits briefly for exclusive access to the process store.
2. `.values()` iterates over stored entries.
3. `entry.creator_cell_id.as_ref() == Some(cell_id)` requires exact typed equality.
4. `!entry.process.has_exited()` excludes completed processes.
5. `.map(...)` extracts only the logical numeric session ID.
6. `sort_unstable()` provides deterministic numeric order.
7. the mutex guard is dropped when the function returns.

What it does not do:

- no process is terminated;
- no process is resumed;
- no output is read;
- no command or environment is exposed;
- no second registry is created;
- no asynchronous operation occurs while iterating under the lock;
- no other cell's IDs are returned.

The query is asynchronous only because it may wait to acquire the existing Tokio mutex. Once acquired, the work is a bounded in-memory scan plus integer sorting.

Agent 2's supplemental direct unit test was important because the integration suite initially covered these semantics only indirectly. The final unit inserts deliberately chosen entries and proves exact-cell inclusion, another-cell exclusion, unattributed-entry exclusion, exited-entry exclusion, and numeric sorting without network or shell timing dependencies.[^agent2-query-test]

### 5. Query only for terminal cell outcomes

File:

[`codex-rs/core/src/tools/code_mode/mod.rs` lines 199-255](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/code_mode/mod.rs#L199-L255)

The response path first derives a terminal cell ID:

```rust
fn terminal_cell_id(response: &RuntimeResponse) -> Option<&CellId> {
    match response {
        RuntimeResponse::Yielded { .. } => None,
        RuntimeResponse::Terminated { cell_id, .. }
        | RuntimeResponse::Result { cell_id, .. } => Some(cell_id),
    }
}
```

Then:

```rust
let background_session_ids = match terminal_cell_id(&response) {
    Some(cell_id) => exec
        .session
        .services
        .unified_exec_manager
        .live_process_ids_created_by_cell(cell_id)
        .await,
    None => Vec::new(),
};
```

`Yielded` means the code cell itself is still running. Showing a completion-only warning there would blur the lifecycle contract and could make ordinary intermediate output look terminal. Therefore yielded responses do not perform the manager lookup.

`Result` and `Terminated` are terminal cell outcomes. They are the point at which copied nested session IDs may otherwise vanish from the model-visible result.

This boundary is informed by both the product diagnosis and the tests. Agent 1 narrowed the defect to terminal outer-status blindness after nested yields. Agent 2's yielded-neutrality test checks the named warning is absent rather than scanning all numbers, because the ordinary yielded header legitimately contains a numeric cell ID.[^agent2-yielded]

### 6. Render the warning without changing existing first-line status

File:

[`code_mode/mod.rs` lines 268-300](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/code_mode/mod.rs#L268-L300)

The formatter preserves the existing status:

- `Script running with cell ID ...`
- `Script terminated`
- `Script completed`
- `Script failed`

For a non-yielded response with matching live IDs, it appends:

```text
Background sessions still running: 1001, 3003
```

It returns only numeric IDs. Commands, outputs, working directories, environment variables, process handles, and other-cell sessions remain undisclosed.

The formatter sorts again even though the manager query already sorts. This is redundant but harmless. Keeping formatter determinism independent of caller order can be defended; removing the duplicate sort can also be defended as a small cleanup. It is not a correctness concern.

### 7. Put the status outside code-mode emitted-output truncation

The response path converts and sanitises emitted content, truncates it, and only then prepends the status header.

Conceptually:

```rust
content_items = truncate_code_mode_result(content_items, max_output_tokens);
prepend_script_status(&mut content_items, &script_status, started_at.elapsed());
```

That means a large `text(...)` payload cannot consume the code-mode output budget and remove the live-session warning at this boundary.

This is not an unlimited-persistence guarantee. The complete tool result remains subject to later global conversation-history limits. Agent 4 correctly recommends keeping the essential truncation claim visible while moving deeper history-limit nuance into a compact scope note or appendix.[^agent4-layering]

Agent 2's large-output test evolved to assert the actual contract rather than one serialisation shape: a separate status item must contain the warning and a separate non-empty output representation must remain. It no longer requires exactly two content items.[^agent2-output-test]

## Why this does not modify JavaScript, Electron, or the nested result schema

Despite the symptom appearing through JavaScript code mode, the production diff is Rust-only.

It does not change:

- JavaScript source;
- V8 APIs;
- Electron IPC;
- the object returned by `tools.exec_command`;
- the `session_id` field type;
- public app-server protocol;
- nested tool-call IDs.

The patch changes internal Rust metadata flow and final model-facing status formatting. The JavaScript object can still be projected to `.output`; the difference is that terminal rendering can now recover the matching live IDs from manager state.

## Threat model and attack-surface review

The new datum is not accepted from arbitrary JavaScript. It comes from existing internal `ToolCallSource::CodeMode` metadata.

The new query is crate-private and session-local. It returns only exact-cell live numeric IDs. It does not expose a global process list or accept a string-prefix ownership convention.

The strongest disclosure risk would have been cross-cell enumeration. That is why exact `CellId` equality and the two-cell acceptance test are central rather than decorative. A global “list all live sessions” warning would make the symptom visible but violate isolation between concurrent or historical cells.

Potential denial-of-service or lock concerns are limited:

- the code acquires an existing manager mutex;
- it performs no nested `.await` while holding it;
- the manager already owns the map;
- the output contains integer IDs only;
- the number of entries is bounded in normal operation by existing manager policy, though that policy is soft under some locked-exit conditions.

The final design keeps the complete point-in-time matching list rather than introducing a separate display cap. A cap would deliberately hide some control handles. Later global history limits are documented separately.

## How the tests shaped the production contract

The test history is not merely cleanup after implementation. Several tests forced sharper engineering decisions:

### Multiple live sessions

The primary acceptance case proves the status is derived from authoritative manager state, not one JavaScript value, and that IDs appear once each in numeric order.

### Exited-session exclusion

The one-survivor case proves creator attribution alone is insufficient. The manager must also check current liveness.

The first version used `sleep 1` and `sleep 2`, which asserted elapsed time rather than process exit. The final PID/filesystem handshake makes cell completion causally downstream of observed process exit and has a bounded failure mode.[^agent2-handshake]

### Exact completing-cell attribution

The two-cell case proves the lookup must not dump all session processes. This is the test that turns “show something useful” into a defensible ownership contract.

### Yielded neutrality

The yielded case proves the warning is tied to terminal outcomes rather than all code-mode responses.

### Truncation placement

The large-output case proves the warning is not part of the truncatable emitted payload.

### Direct manager semantics

The unit test proves exact filtering independently of the code-mode runtime and shell harness.

### Repository test convention

The tests were moved from a standalone integration binary into the existing aggregate `all` suite because the repository explicitly documents a single aggregate integration-test binary. Reusing the existing code-mode parent module also removed duplicated setup and response helpers.[^agent2-aggregate]

These revisions increased confidence without expanding production scope.

## Was the relevant Rust code compiled and executed?

Yes. Repository-native focused `just test` commands invoke Cargo nextest, which compiles the relevant crate and test binaries before executing them.

Final focused evidence includes:

- four unit tests passed;
- five aggregate acceptance cases passed;
- two exposed compatibility tests passed 20/20 executions on the final candidate;
- the same two tests passed 20/20 executions on the exact upstream base;
- formatting, scoped fix/lint, clean worktree, and `git diff --check` passed.

The broader `codex-core` suite was red on both candidate and exact base under the matched hosted environment. It is not claimed green. The complete workspace suite was not run.

This evidence does not establish every product surface, operating system, private deployment component, app-server integration, or UI path.

## Resource impact: precise language

The observed incident reportedly involved two Node/Playwright process groups retaining roughly 7-8 GB of memory until manually terminated. That can be described as an operational resource-retention incident when supported by a preserved process snapshot or clearly labelled first-person recollection.

It should not be described as proof that the Rust implementation leaked 7-8 GB of unreachable heap memory.

The technical chain is:

1. child processes intentionally allocated and retained resources;
2. unified exec continued to own them;
3. their model-visible session IDs disappeared;
4. the ordinary model control path could no longer naturally inspect or stop them;
5. the processes continued consuming their own resources.

Accurate terms include:

- lost session-handle visibility;
- effectively orphaned live process from the model's perspective;
- background-process resource-leak risk;
- process-lifecycle visibility defect.

Patch 1 restores handles. It does not deallocate the child processes automatically.

## Is this good code?

The production patch is good primarily because it is restrained.

Strengths:

- uses existing typed provenance;
- stores metadata beside the manager-owned process;
- preserves the existing manager as liveness authority;
- uses exact typed equality;
- returns a minimal data shape;
- changes no public schema;
- changes no lifecycle policy;
- performs a read-only query;
- places the warning at the correct terminal and truncation boundary;
- has direct unit and end-to-end acceptance coverage.

Non-blocking imperfections:

- `Option<CellId>` is less general than a future origin enum;
- the manager and formatter both sort;
- the small query method lives in `unified_exec/mod.rs` while many process operations live in `process_manager.rs`.

None justifies widening a first outside contribution after the behaviour is validated.

## What this patch does not do

Patch 1 does not:

- terminate background sessions at code-cell completion;
- change persistence across turns;
- change interrupt or `/stop` policy;
- prevent a model from ignoring a visible session ID;
- recover OS processes after abrupt application or runtime loss;
- persist OS PIDs for later reclamation;
- add wake-up events when a process exits;
- add subagent ownership or cleanup policy;
- change JavaScript result fields;
- parse or expose nested call-ID structure;
- add a second process registry;
- solve delayed cross-turn dispatch;
- prove every Codex product surface behaves identically;
- prove a literal Rust memory leak;
- assign a security severity.

Those are separate product, lifecycle, recovery, or architecture questions.

## A terse human-readable description

A defensible short description is:

> Code mode can start background terminal sessions, discard their returned session IDs while keeping only output, and then report `Script completed` even though those sessions are still running. The patch remembers which cell created each stored process and lists that cell's still-live session IDs when the cell finishes, so the model does not lose its control handles.

An even shorter version is:

> The process manager did not forget the processes; the terminal result forgot to tell the model how to reach them. This patch reconnects those two pieces of state.

## Footnotes and sources

[^agent1-diagnosis]: [`agent-1-investigation-reconstruction.md`](agent-1-investigation-reconstruction.md), especially “The point at which the diagnosis narrowed”.
[^agent1-history]: [`agent-1-investigation-reconstruction.md`](agent-1-investigation-reconstruction.md), chronological reconstruction and “Evidence that changed the diagnosis”.
[^unified-exec-origin]: Upstream commit [`c09ed74a`](https://github.com/openai/codex/commit/c09ed74a163ecea69c32d61ab2bfa1c8490eb611), “Unified execution” / PR `#3288`.
[^tool-refactor]: Upstream commit [`33d3ecbc`](https://github.com/openai/codex/commit/33d3ecbccca4b92cfb2a77002387de30302f337f), tool-system refactor / PR `#4510`.
[^js-repl]: Upstream commit [`42e22f3b`](https://github.com/openai/codex/commit/42e22f3bde6c851422eb4f7b502457fe86ba91db), feature-gated `js_repl` / PR `#10674`.
[^v8]: Upstream commit [`e4eedd61`](https://github.com/openai/codex/commit/e4eedd6170580d5b06fb539635a78f261a6b7369), code mode on V8 / PR `#15276`.
[^cell-actor]: Upstream commit [`e2f074e1`](https://github.com/openai/codex/commit/e2f074e16c522bfa55d9bcd344a5ea0ba5a4580f), cell actor / PR `#28599`.
[^negative-test]: Negative reproduction commit [`7298dcf4`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5); see also [`agent-2-test-validation-archaeology.md`](agent-2-test-validation-archaeology.md), section 3.
[^agent1-provenance]: [`agent-1-investigation-reconstruction.md`](agent-1-investigation-reconstruction.md), “Typed creator-cell information existed but was not retained”.
[^agent1-manager-ownership]: [`agent-1-investigation-reconstruction.md`](agent-1-investigation-reconstruction.md), “The manager, not JavaScript, owned the live process”.
[^agent2-query-test]: [`agent-2-test-validation-archaeology.md`](agent-2-test-validation-archaeology.md), section 12; final unit test [`unified_exec/mod_tests.rs` lines 332-395](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod_tests.rs#L332-L395).
[^agent2-yielded]: [`agent-2-test-validation-archaeology.md`](agent-2-test-validation-archaeology.md), section 10.
[^agent4-layering]: [`agent-4-publication-architecture.md`](agent-4-publication-architecture.md), executive verdict and recommended issue/PR structures.
[^agent2-output-test]: [`agent-2-test-validation-archaeology.md`](agent-2-test-validation-archaeology.md), section 11.
[^agent2-handshake]: [`agent-2-test-validation-archaeology.md`](agent-2-test-validation-archaeology.md), sections 8-9.
[^agent2-aggregate]: [`agent-2-test-validation-archaeology.md`](agent-2-test-validation-archaeology.md), section 6; repository convention [`tests/all.rs` lines 1-9](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/all.rs#L1-L9).
