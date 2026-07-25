# Decision and provenance log

Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`

This document records why each proposed change exists, which existing behavior or pattern it relies on, and which upstream authors/PRs introduced the relevant semantics. It is research material, not part of the eventual production patch.

## Existing intended behavior

### Background terminals persist across turns

- Upstream PR: openai/codex#10799, **“feat: do not close unified exec processes across turns”**
- Author: `jif-oai`
- Merge commit: `6cf61725d0c6a11ab887c0a7fd532d2b137f1708`
- Recorded intent: unified-exec background terminals remain alive after a turn unless explicitly cleaned or otherwise shut down.
- Consequence for this work: Patch 1 should not silently change the global persistence policy.

### Interrupt preserves background terminals; explicit cleanup uses `/stop`

- Upstream PR: openai/codex#14602, **“Preserve background terminals on interrupt and rename cleanup command to /stop”**
- Author: `friel-openai`
- Merge commit: `ba463a9dc78180d9cd61b28ef6562e03342a14be`
- Recorded intent: interrupting a turn should not terminate background servers/watchers; termination is explicit.
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
- Symbol: `UnifiedExecProcessManager::list_processes`
- Existing pattern: returns only entries whose process has not exited, including `item_id`, logical process ID, command, and working directory.
- Relevance: Patch 1 can query current live state instead of introducing a second registry.

### Nested code-mode calls already carry a cell ID

- Files:
  - `codex-rs/core/src/tools/context.rs`
  - `codex-rs/core/src/tools/code_mode/mod.rs`
  - `codex-rs/core/src/tools/code_mode/delegate.rs`
- Symbols:
  - `ToolCallSource::CodeMode`
  - `CodeModeNestedToolCall`
  - `call_nested_tool`
- Existing pattern: each nested tool call knows the originating runtime cell.
- Relevance: live sessions can be associated with the outer cell without parsing JavaScript output.

## Patch 1 decision under test

### Decision

Surface still-live unified-exec sessions in the outer code-mode status when a cell returns.

### Current prototype

Branch: `fix/code-mode-live-session-summary`

Prototype commit: `cffcd8dca93ab5c2ff8fa1af262ae7676f5b97a9`

Approach:

1. Include the originating cell ID in nested tool call IDs.
2. At the outer runtime response boundary, call `list_processes()`.
3. Filter live processes to those created by that cell.
4. Append their logical session IDs to the untruncated script-status header.

Example:

```text
Script completed
Background sessions still running: 6306, 11236
```

### Why this direction

- Preserves intentional background-terminal persistence.
- Does not modify the nested JavaScript result contract.
- Does not depend on whether user JavaScript reads `session_id`.
- Reuses the existing process manager as the source of truth.
- Limits reporting to processes created by the specific code-mode cell.
- Places the warning in the status header, reducing the chance that output truncation hides it.

### Alternatives considered

1. Add the running-session message directly to nested result `.output`.
   - Small change, but mutates an existing raw-output field and still relies on JavaScript printing it.
2. Add a second per-cell live-session registry.
   - More explicit, but duplicates process-manager state and creates cleanup/race obligations.
3. Automatically terminate sessions when the cell or subagent completes.
   - Addresses cleanup, but conflicts with existing persistence policy and requires a broader product decision.
4. Require explicit persistence opt-in.
   - Potentially cleaner long term, but backwards-incompatible and outside Patch 1 scope.

## Evidence provenance

Private incident evidence should not be uploaded. The eventual public issue should include only anonymised facts:

- two nested one-shot exec calls reached `yield_time_ms` and returned live logical session IDs;
- JavaScript printed only `.output`;
- the outer cell reported completion;
- replacement commands succeeded later;
- the original macOS process groups survived under PID 1;
- local Codex metadata associated those groups with the same conversation and commands.

## Rules for future entries

For every meaningful design decision, record:

- exact file and symbol examined;
- upstream PR/commit and author when history informs the choice;
- confirmed behavior versus inference;
- alternatives rejected and why;
- test that protects the decision;
- whether the choice belongs in Patch 1, Patch 2, or Patch 3.
