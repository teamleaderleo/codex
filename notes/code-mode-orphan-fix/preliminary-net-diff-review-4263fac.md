# Preliminary net-diff review: integrated Patch 1 head

Date: 2026-07-26

Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`

Reviewed head: `4263facaf3c7d30b26cae33fd1e679278ac02105`

Branch: `fix/code-mode-live-session-summary`

Status: preliminary static review passed; final sign-off is reserved until the canonical validation run completes.

## Review scope

The net comparison contains seven changed files:

Production code:

- `codex-rs/core/src/tools/code_mode/mod.rs`
- `codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs`
- `codex-rs/core/src/unified_exec/mod.rs`
- `codex-rs/core/src/unified_exec/mod_tests.rs`
- `codex-rs/core/src/unified_exec/process_manager.rs`
- `codex-rs/core/src/unified_exec/process_manager_tests.rs`

Integration coverage:

- `codex-rs/core/tests/code_mode_orphan_sessions.rs`

The net comparison is 663 changed lines. Most of that total is the 521-line acceptance file. No shutdown, dispatch-broker, cell-runtime, process implementation, session cleanup, interrupt handling, recovery, or public protocol file is changed.

## Findings

### 1. Typed creator-cell attribution: pass

`ExecCommandHandler` now preserves the existing typed source path rather than parsing JavaScript output or call-ID text:

- direct calls map to `None`;
- `ToolCallSource::CodeMode { cell_id, .. }` maps to `Some(CellId)`;
- that optional typed value is attached to `UnifiedExecContext`.

`UnifiedExecContext` adds only `creator_cell_id: Option<CellId>` plus a builder. `store_process` copies the value directly into `ProcessEntry` at the existing process-store boundary.

This matches the selected ownership contract. The manager remains the owner and source of truth after the nested exec yields; JavaScript still receives only its existing copied `session_id` result.

### 2. Exact-cell, live-only filtering: pass

`UnifiedExecProcessManager::live_process_ids_created_by_cell`:

- compares `ProcessEntry.creator_cell_id` directly with the requested `CellId`;
- excludes entries whose process reports `has_exited()`;
- returns concrete logical process IDs;
- sorts the IDs numerically before returning.

The query is read-only. It does not remove, terminate, refresh, hand off, or otherwise modify process state. Exited entries that remain in bookkeeping are excluded from the summary without changing existing removal policy.

The integrated two-cell acceptance case verifies that Cell A's live process is absent from Cell B's completion summary.

### 3. Terminal-only header placement: pass

The response path derives a cell ID only for terminal outcomes:

- `RuntimeResponse::Result` returns its cell ID;
- `RuntimeResponse::Terminated` returns its cell ID;
- `RuntimeResponse::Yielded` returns `None`.

The manager query therefore does not run for an ordinary yielded response. Formatting also independently avoids adding the background-session line to a yielded status.

For result, failure, and explicit termination, emitted content is converted and truncated first. The script-status header, including any surviving process IDs, is then prepended as a separate content item. Large emitted output therefore cannot truncate the warning.

The existing success value and JavaScript-facing result schema are unchanged.

### 4. Opaque nested call IDs: pass

The nested call ID remains:

```text
exec-<random UUID>
```

This is identical to the baseline path. The final net diff does not encode the cell ID into the call ID and contains no prefix-based ownership inference.

### 5. No lifecycle-policy expansion: preliminary pass

The production changes are limited to:

- preserving creator metadata at tool dispatch;
- storing that metadata with the existing live process entry;
- reading exact-cell live IDs at terminal response formatting;
- formatting the model-visible status;
- adding focused tests and fixture fields.

The existing store-before-yield behaviour remains in place. Existing pruning, termination, shutdown, interrupt, process watcher, dispatch gate, cross-turn persistence, and removal paths are not altered by the net diff.

In particular, `store_process` still performs the same insertion, pruning cleanup, and exit-watcher launch; the only semantic addition to the entry construction is the copied creator-cell field.

No evidence of an unrelated lifecycle-policy change was found in this preliminary review.

## Minor notes, not blockers

1. Process IDs are sorted in the manager and sorted again by the formatter. This is harmless defensive redundancy and does not justify a pre-validation code change.
2. The branch contains prototype history even though the final net diff is clean. Squashing or preparing a clean candidate comparison should occur only after canonical validation is green.
3. The focused integration tests are Unix-oriented and network-harness-backed. That limitation is already documented and does not undermine the ownership contract, but broader validation claims must remain narrow.

## Preliminary verdict

No code change is requested before the canonical validation run.

The integrated head satisfies the static Patch 1 contract for:

- typed creator-cell attribution;
- exact-cell live-only filtering;
- terminal-only disclosure;
- warning placement outside truncation;
- opaque call IDs;
- unchanged JavaScript schema and process-persistence policy.

Final sign-off remains pending all of the following on the canonical integrated branch:

1. formatting completes and the formatted net diff is inspected;
2. the relevant code-mode and unified-exec unit tests pass;
3. the complete five-test `code_mode_orphan_sessions` file passes from `4263facaf3c7d30b26cae33fd1e679278ac02105` or its formatting-only descendant;
4. the resulting tested head or clean PR comparison is reviewed once more for lifecycle-policy expansion.

## Separate follow-up boundary

The delayed cross-turn dispatch investigation is not part of this review or Patch 1. It remains a high-confidence static crossover path only. It must not be described as reproduced unless an executable test observes wrong-turn execution or a bounded no-successor failure/hang condition.
