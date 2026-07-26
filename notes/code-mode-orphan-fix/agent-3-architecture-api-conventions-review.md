# Agent 3 architecture and API-conventions review

Date: 2026-07-26

Reviewer lane: Agent 3 — ownership boundary, architecture, and independent net-diff review

## Scope

Upstream base:

`61a44880a85d2fd0d8770908dea5733495e571c8`

Clean candidate:

`3778e1fae6e7e3d885252282a7c5ce67e06730ff`

This review asks whether the already validated Patch 1 behaviour is expressed through appropriate Codex interfaces and abstraction layers. It does not reopen lifecycle policy or the accepted visibility-only contract.

## Verdict

**Pass with non-blocking notes.**

No code change is requested. The clean candidate uses the correct ownership boundary, process-liveness authority, and output-construction layer. No awkward public API, protocol change, or lifecycle expansion is introduced.

## Ownership and provenance boundary

The provenance handoff occurs at the correct existing boundary:

1. The code-mode runtime supplies a typed `CellId` with each nested tool invocation.
2. `ToolCallSource::CodeMode` is attached while routing that nested call.
3. `ExecCommandHandler` is the first layer that knows the invocation source will create a unified-exec process.
4. It converts the source cell identity into the typed `CellId` carried by `UnifiedExecContext`.
5. The manager stores that identity beside the manager-owned `ProcessEntry`.

This avoids deriving ownership from JavaScript output, nested call-ID text, command text, or timing. The creator identity follows the actual process-creation path.

## Liveness and manager query

`UnifiedExecProcessManager` is the correct source of truth because it owns the process store and process handles.

`live_process_ids_created_by_cell`:

- acquires the existing process-store mutex;
- compares exact typed `CellId` equality;
- calls the existing synchronous `has_exited()` state query;
- excludes exited processes even when stale bookkeeping remains;
- returns logical manager process IDs;
- sorts IDs deterministically;
- performs no mutation or lifecycle operation.

The mutex is not held across an `.await` inside the iteration. The liveness result is necessarily a point-in-time snapshot; a process may exit immediately afterward, but that race is inherent to any live-status display and does not justify lifecycle intervention.

## Field placement and API shape

### `UnifiedExecContext`

`creator_cell_id: Option<CellId>` is appropriate transient creation metadata. The default remains `None`, so direct and non-code-mode callers preserve existing behaviour. The builder-style setter avoids widening every constructor call.

### `ProcessEntry`

The durable attribution belongs beside `call_id`, `process_id`, and the process handle because the manager entry is the lifetime record used for later queries. Storing the identity anywhere in the callback task or JavaScript result would lose it when the cell finishes or the caller discards the copied handle.

### Manager query visibility

The query is `pub(crate)`, returns only the minimum `Vec<i32>` required by the caller, and does not expose `ProcessEntry` or process handles. This is appropriately narrow.

### Status construction

The user-facing line remains in code mode rather than unified exec. Unified exec supplies process facts; code mode decides how terminal cell status is rendered. This avoids teaching the general process manager about model-facing code-mode prose.

The query runs only for terminal `Result` and `Terminated` outcomes. `Yielded` remains neutral. The status is prepended only after emitted content has been truncated, preserving the control information.

## Naming, visibility, mutability, and locking

- `creator_cell_id` accurately distinguishes creator provenance from current caller or polling ownership.
- `live_process_ids_created_by_cell` is precise about liveness, returned identifier type, and matching rule.
- Numeric `i32` sorting matches the manager's logical process-ID representation.
- The added state is immutable after process insertion.
- No new lock, shared mutable collection, public protocol type, or serialization field is introduced.
- Both local and exec-server-backed stored process paths copy the same attribution from `UnifiedExecContext`.

## Non-blocking notes

### 1. Existing string seam in `ToolCallSource`

`CodeModeNestedToolCall` carries a typed `CellId`, but the pre-existing `ToolCallSource::CodeMode` representation stores `cell_id: String`; the exec handler reconstructs `CellId` before persisting it.

A future general cleanup could make `ToolCallSource` itself carry `CellId`, but doing so would broaden the router/context API beyond this fix. The current patch restores typed identity at the first process-specific boundary and is the safer narrow change.

### 2. Defensive duplicate sorting

The manager query sorts the returned process IDs, and `format_script_status` sorts its input again. This is redundant but harmless. It keeps the formatter deterministic when unit-tested independently and costs effectively nothing for the bounded process set. It does not warrant churn before submission.

### 3. Method file placement

The simple read-only query is implemented beside the manager/store definitions in `unified_exec/mod.rs`, while most operational manager methods live in `process_manager.rs`. Moving it would be a stylistic alternative, not an architectural improvement. Its current placement keeps the small store inspection close to the private entry definition.

## Maintainer-facing concerns

No likely blocking maintainer concern was found.

A maintainer might ask about the string-to-`CellId` conversion or duplicate sorting, but both have clear narrow-scope rationales. Neither changes observable behaviour or creates debt that must be resolved in this pull request.

The one-commit structure is appropriate: the production change and its focused tests form one coherent behavioural unit, and the clean branch excludes all investigation ancestry.

## Deferred work

The following remain separate and must not be inferred from this patch:

- generic process-origin/provenance modelling beyond code mode;
- ownership or cleanup policy for hidden or subagent work;
- process termination or persistence changes;
- cross-turn dispatch behaviour;
- shutdown-race handling;
- remote termination confirmation;
- stale-bookkeeping cleanup policy;
- macOS or runtime-loss orphan recovery.

Patch 2 and Patch 3 remain planning labels for those broader families, not approved implementation contracts.

## Final conclusion

The clean candidate uses existing Codex layers appropriately:

- routing source for creator provenance;
- unified-exec context for creation metadata;
- manager-owned process entries for durable attribution;
- manager state for liveness;
- code mode for terminal model-facing status.

**Final conventions verdict: pass with non-blocking notes. No clean-candidate modification requested.**
