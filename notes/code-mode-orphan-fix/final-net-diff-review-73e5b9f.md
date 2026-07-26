# Final net-diff review: published formatted Patch 1 head

Date: 2026-07-26

Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`

Reviewed head: `73e5b9fc28de0815975fad3c3d70a6a0b38399b1`

Branch: `fix/code-mode-live-session-summary`

Status: final Patch 1 net-diff sign-off passed.

## Evidence reviewed

The published branch resolves exactly to `73e5b9fc28de0815975fad3c3d70a6a0b38399b1`.

The head is one commit ahead of integrated merge head `4263facaf3c7d30b26cae33fd1e679278ac02105`. That commit is `style: format code-mode live-session patch` and changes only:

- `codex-rs/core/src/tools/code_mode/mod.rs`;
- `codex-rs/core/src/unified_exec/process_manager.rs`.

Its complete patch consists of Rust formatter line wrapping. It does not alter expressions, branches, data flow, tests, process state, or public output.

The final baseline comparison contains seven changed files:

Production:

- `codex-rs/core/src/tools/code_mode/mod.rs`;
- `codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs`;
- `codex-rs/core/src/unified_exec/mod.rs`;
- `codex-rs/core/src/unified_exec/mod_tests.rs`;
- `codex-rs/core/src/unified_exec/process_manager.rs`;
- `codex-rs/core/src/unified_exec/process_manager_tests.rs`.

Acceptance:

- `codex-rs/core/tests/code_mode_orphan_sessions.rs`.

The final comparison is 664 changed lines, of which 521 are the dedicated acceptance file. No shutdown, interrupt, dispatch-broker, recovery, code-mode runtime, process implementation, session-cleanup, subagent, macOS recovery, or public protocol file changed.

## Contract review

### Typed creator-cell attribution: pass

`ExecCommandHandler` reads the existing typed source:

- direct calls produce no creator cell;
- `ToolCallSource::CodeMode { cell_id, .. }` produces `Some(CellId)`.

That typed value is attached to `UnifiedExecContext` and copied directly into the stored `ProcessEntry` when the live unified-exec process is registered.

No JavaScript output, returned `session_id`, call-ID prefix, command text, or other string convention is used to infer ownership.

### Live-only exact-cell filtering: pass

`UnifiedExecProcessManager::live_process_ids_created_by_cell`:

- compares stored creator `CellId` values exactly;
- excludes entries whose process reports `has_exited()`;
- returns the concrete logical process IDs;
- sorts those IDs deterministically.

The query is read-only. It does not refresh, remove, terminate, prune, transfer, or otherwise change lifecycle state. Existing stale-entry cleanup policy remains unchanged.

The two-cell acceptance test proves that Cell A's live process is absent from Cell B's terminal summary.

### Terminal-only reporting and header placement: pass

Only `RuntimeResponse::Result` and `RuntimeResponse::Terminated` expose a terminal cell ID to the process lookup. `RuntimeResponse::Yielded` does not query or report surviving nested sessions.

For terminal responses, emitted output is converted and truncated before the script-status header is prepended. The session warning is therefore outside emitted-output truncation.

Successful result, failed result, and explicit termination preserve their existing primary status text and append the live-session line only when matching survivors exist.

The JavaScript-visible nested tool result schema is unchanged.

### Opaque nested call IDs: pass

Nested call IDs remain random UUID-based `exec-...` identifiers, matching the baseline path. No cell ID is embedded in the call ID, and no ownership lookup parses call-ID text.

### Lifecycle-policy boundary: pass

No lifecycle-policy expansion was found.

The net production changes only:

- preserve creator metadata at nested tool dispatch;
- carry it through unified exec;
- store it with an already-persisted live process entry;
- read exact-cell live IDs while formatting a terminal response;
- add focused unit coverage.

Existing behaviour remains unchanged for:

- store-before-yield persistence;
- process pruning;
- natural-exit bookkeeping;
- process termination;
- interrupt handling;
- session shutdown;
- dispatch gates and workers;
- cross-turn persistence;
- subagents;
- remote termination;
- macOS recovery.

The formatting-only descendant introduces no semantic delta from the locally validated integrated tree.

## Validation record

Agent 2's canonical validation ran on the Rust-formatted descendant of `4263facaf3c7d30b26cae33fd1e679278ac02105`. The now-published commit contains exactly the two formatting changes recorded during that run.

Reported results:

- `cargo check --manifest-path codex-rs/Cargo.toml -p codex-core --tests`: passed;
- focused code-mode library tests: `3 passed; 0 failed`;
- focused unified-exec library tests: `3 passed; 0 failed`;
- complete `code_mode_orphan_sessions`: `5 passed; 0 failed; 0 ignored`;
- no skips or flakes on the correctly scoped commands;
- panic-safe acceptance cleanup remained active.

One broad fallback command caused unrelated integration-test linkers to be killed by signal 9. That command selected the wrong test scope. It does not change this sign-off because the correctly scoped compile, library, and acceptance commands passed.

A full workspace test suite and the full multi-language repository formatter are not claimed.

## Minor notes, not blockers

1. Process IDs are sorted in both the manager query and formatter. The redundancy is harmless.
2. The branch retains research/prototype ancestry. Prepare a clean candidate comparison only after evidence and publication text are final.
3. The integration tests are Unix-oriented and network-harness-backed; that limitation is documented.

## Final verdict

Final Patch 1 net-diff sign-off: **pass**.

The published tested head satisfies the selected contract for:

- typed creator-cell ownership;
- exact-cell live-only filtering;
- deterministic session ordering;
- terminal-only disclosure;
- yielded-response neutrality;
- status placement outside truncation;
- opaque call IDs;
- unchanged JavaScript schema;
- no lifecycle-policy expansion.

No further Patch 1 code change is requested by this review.

Remaining work is publication preparation rather than implementation validation:

1. Agent 4 fills final SHA, validation, and review evidence;
2. related-issue and maintainer-discussion research is refreshed;
3. a clean candidate commit or draft PR comparison is prepared;
4. issue/PR ordering is chosen;
5. no upstream issue or PR is published until those publication steps are complete.

## Separate follow-up boundary

The delayed cross-turn dispatch investigation is not part of Patch 1 or this sign-off. It remains an unreproduced static finding. It must not be described as a confirmed bug without executable evidence of wrong-turn execution or a bounded no-successor failure/hang condition.
