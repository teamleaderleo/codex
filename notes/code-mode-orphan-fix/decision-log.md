# Decision and provenance log

Last updated: 2026-07-26

Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`

This document records why each proposed change exists, which existing behaviour or pattern it relies on, and which upstream authors and PRs introduced the relevant semantics. It is research material, not part of the eventual production patch.

## Existing intended behaviour

### Background terminals persist across turns

- Upstream PR: openai/codex#10799, **“feat: do not close unified exec processes across turns”**
- Author: `jif-oai`
- Merge commit: `6cf61725d0c6a11ab887c0a7fd532d2b137f1708`
- Recorded intent: unified-exec background terminals remain alive after a turn unless explicitly cleaned or otherwise shut down.
- Consequence for this work: Patch 1 must not silently change the global persistence policy.

### Interrupt preserves background terminals; explicit cleanup uses `/stop`

- Upstream PR: openai/codex#14602, **“Preserve background terminals on interrupt and rename cleanup command to /stop”**
- Author: `friel-openai`
- Merge commit: `ba463a9dc78180d9cd61b28ef6562e03342a14be`
- Recorded intent: interrupting a turn does not terminate background servers or watchers; termination is explicit.
- Additional lifecycle detail: this PR stores a live unified-exec process before the initial yield wait so turn interruption cannot drop the last process reference.
- Consequence for this work: a visibility fix is lower-risk than automatic termination in Patch 1. Cleanup policy belongs in a separate proposal.

## Existing code patterns reused

### Direct unified-exec output surfaces a live process ID

- File: `codex-rs/core/src/tools/context.rs`
- Symbol: `ExecCommandToolOutput::response_text`
- Existing pattern: when `process_id` is present, direct model-facing output includes `Process running with session ID ...`.
- Relevance: the product already treats a live session ID as important model-facing state.

### Code-mode result preserves `session_id` as typed JSON

- File: `codex-rs/core/src/tools/context.rs`
- Symbol: `ExecCommandToolOutput::code_mode_result`
- Existing pattern: nested code-mode exec results expose `session_id: Option<i32>`.
- Failure demonstrated by the incident: JavaScript can consume only `.output`, discard `session_id`, and still complete normally.

### Process manager already exposes live background terminals

- File: `codex-rs/core/src/unified_exec/process_manager.rs`
- Symbols:
  - `UnifiedExecProcessManager::store_process`
  - `UnifiedExecProcessManager::list_processes`
  - `UnifiedExecProcessManager::terminate_all_processes`
- Existing pattern: a live process is retained in the conversation-level manager and can be listed or explicitly terminated.
- Relevance: Patch 1 should query current manager state rather than introduce a second liveness registry.

### Nested code-mode calls already carry a cell ID

- Files:
  - `codex-rs/core/src/tools/context.rs`
  - `codex-rs/core/src/tools/code_mode/mod.rs`
  - `codex-rs/core/src/tools/code_mode/delegate.rs`
- Symbols:
  - `ToolCallSource::CodeMode`
  - `CodeModeNestedToolCall`
  - `call_nested_tool`
- Existing pattern: each nested tool call already carries the originating runtime cell as typed dispatch metadata.
- Relevance: live sessions can be associated with the outer cell without parsing JavaScript output or encoding ownership into display identifiers.

## Confirmed ownership boundary

### Before a nested exec yields

- The code-mode cell actor owns and tracks the nested callback task.
- Cancellation or cell completion can cancel and drain that callback task.

### After unified exec stores a live process

- Files:
  - `codex-rs/core/src/unified_exec/mod.rs`
  - `codex-rs/core/src/unified_exec/process_manager.rs`
  - `codex-rs/core/src/unified_exec/process.rs`
- Symbols:
  - `ProcessStore`
  - `ProcessEntry`
  - `UnifiedExecProcessManager::store_process`
- Confirmed behaviour: the conversation-level process manager retains an `Arc<UnifiedExecProcess>` in its process store.
- JavaScript receives only a copied logical session ID. Dropping the returned JavaScript object does not release the manager-owned process.
- Ordinary cell completion and ordinary turn completion do not remove that process by design.
- Explicit process termination, pruning/removal, or session shutdown can remove it.

### Current metadata gap

- File: `codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs`
- Symbol: `ExecCommandHandler::handle_call`
- Confirmed behaviour at the baseline: `ToolInvocation` contains `source`, but the handler does not preserve the `ToolCallSource::CodeMode` cell identity in `UnifiedExecContext` or `ProcessEntry`.
- Consequence: the manager knows which tool call created a process, but not the typed creator code-mode cell.

## Patch 1 decision under test

### Selected contract

Surface still-live unified-exec sessions in the outer terminal code-mode status while preserving existing persistence semantics.

The intended implementation contract is:

1. Preserve `ToolCallSource::CodeMode { cell_id, ... }` through `ExecCommandHandler` into unified-exec context.
2. Store optional typed creator-cell attribution on the live `ProcessEntry`.
3. Query the process manager for currently live processes created by that cell.
4. Report surviving logical session IDs in the outer terminal status/header after output truncation.
5. Keep the JavaScript-visible `session_id` result compatible.
6. Do not terminate the sessions or transfer ownership in Patch 1.
7. Prefer terminal outcomes: successful result, failed result, and explicit termination. An ordinary yielded cell is still active and should not receive a completion-oriented warning.

### Feasibility prototype

Branch: `fix/code-mode-live-session-summary`

Prototype commit: `cffcd8dca93ab5c2ff8fa1af262ae7676f5b97a9`

Prototype approach:

1. Include the originating cell ID in nested tool call IDs.
2. At the outer runtime response boundary, call `list_processes()`.
3. Filter live processes by a call-ID prefix derived from that cell.
4. Append their logical session IDs to the untruncated script-status header.

Example:

```text
Script completed
Background sessions still running: 6306, 11236
```

What this prototype proves:

- the process manager can be queried at the correct response boundary;
- surviving IDs can be sorted and placed in the untruncated header;
- no JavaScript result-schema or persistence-policy change is required.

Why its ownership mechanism is not the selected contract:

- `CellId` is an unrestricted string;
- `starts_with` matching can collide, such as cell `1` and cell `1-x`;
- arbitrary cell IDs leak into tool call IDs and tracing;
- representation-level naming should not become the ownership API when typed source metadata already exists.

Retain the formatter and manager-query scaffolding, but replace prefix inference with typed creator-cell attribution.

## Regression-test provenance and obligation

### Existing failing regression

- Branch: `research/code-mode-live-session-test`
- File: `codex-rs/core/tests/code_mode_orphan_sessions.rs`
- Test: `code_mode_completion_does_not_surface_discarded_live_exec_sessions`

The test currently:

- launches two nested long-running `exec_command` calls through `Promise.all`;
- deliberately destructures only `{ output }`, discarding both session IDs;
- proves two distinct background terminals remain alive after the cell completes;
- proves the outer status says `Script completed` without session information;
- performs process cleanup even if the assertion body panics.

### Patch 1 acceptance test

On the implementation branch, revise the test to assert:

1. both nested calls yield and remain live;
2. JavaScript discards both nested `session_id` values;
3. the outer terminal status contains both live IDs in deterministic order;
4. a process that exits before the summary is not reported;
5. large output cannot truncate the status warning;
6. explicit teardown leaves no surviving test process.

Prefer a cross-platform long-running helper or existing fixture if available. Preserve the panic-safe teardown even if the first runnable version remains platform-limited.

## Alternatives considered

1. Add the running-session message directly to nested result `.output`.
   - Small change, but mutates an existing raw-output field and still relies on JavaScript printing it.
2. Add a second per-cell live-session registry.
   - More explicit than string parsing, but duplicates process-manager state and creates cleanup and race obligations.
3. Infer ownership from nested call-ID prefixes.
   - Useful as a prototype, but vulnerable to collisions and turns an identifier convention into an ownership API.
4. Inspect only values retained or emitted by JavaScript.
   - Misses the confirmed failure because JavaScript deliberately discards the handle.
5. Automatically terminate sessions when the cell or subagent completes.
   - Addresses cleanup, but conflicts with existing persistence policy and requires a broader product decision.
6. Require explicit persistence opt-in.
   - Potentially cleaner long term, but backwards-incompatible and outside Patch 1 scope.
7. Change the cross-process code-mode protocol to return live-session metadata with every terminal response.
   - Explicit, but broader than needed and introduces protocol-version compatibility work.

## Separate follow-up findings

The ownership audit also found plausible issues that should not expand Patch 1:

- a delayed old-cell invocation may be consumed by a later turn worker because the dispatch receiver is shared;
- session shutdown can race with an already-dispatched nested exec storing a process after the manager drain;
- one remote exec-server bulk-termination path does not await confirmed remote termination;
- natural process exit may leave manager bookkeeping until a later refresh or removal action.

Each requires its own focused test and issue decision.

## Evidence provenance

Private incident evidence should not be uploaded. The eventual public issue should include only anonymised facts:

- two nested one-shot exec calls reached `yield_time_ms` and returned live logical session IDs;
- JavaScript printed only `.output`;
- the outer cell reported completion;
- replacement commands succeeded later;
- the original macOS process groups survived under PID 1;
- local Codex metadata associated those groups with the same conversation and commands.

Do not publish private rollout logs, prompts, environment dumps, image data, tokens, machine-specific paths, or unrelated conversation content.

## Rules for future entries

For every meaningful design decision, record:

- exact file and symbol examined;
- upstream PR or commit and author when history informs the choice;
- confirmed behaviour versus inference;
- alternatives rejected and why;
- test that protects the decision;
- whether the choice belongs in Patch 1, Patch 2, or Patch 3.
