# Agent 3 history and threat-model notes

Status: working notes for the Rust walkthrough and design-decision record. Not public copy.

## Why history matters

The final walkthrough should not describe the touched functions as if they appeared in isolation. Their current boundaries were established by several earlier changes:

1. **Unified exec session ownership**
   - Commit: [`c09ed74a163ecea69c32d61ab2bfa1c8490eb611`](https://github.com/openai/codex/commit/c09ed74a163ecea69c32d61ab2bfa1c8490eb611)
   - PR: [`openai/codex#3288`](https://github.com/openai/codex/pull/3288)
   - Introduced PTY-backed interactive execution, reusable numeric session IDs, bounded output, and manager-owned session persistence.

2. **Centralised tool dispatch**
   - Commit: [`33d3ecbccca4b92cfb2a77002387de30302f337f`](https://github.com/openai/codex/commit/33d3ecbccca4b92cfb2a77002387de30302f337f)
   - PR: [`openai/codex#4510`](https://github.com/openai/codex/pull/4510)
   - Centralised tool specs, handlers, routing, registry dispatch, telemetry, and shared invocation context under `core/src/tools/*`.
   - This history supports capturing creator provenance in `ExecCommandHandler`, where typed call-source information already crosses into unified exec.

3. **Persistent JavaScript execution**
   - Commit: [`42e22f3bde6c851422eb4f7b502457fe86ba91db`](https://github.com/openai/codex/commit/42e22f3bde6c851422eb4f7b502457fe86ba91db)
   - PR: [`openai/codex#10674`](https://github.com/openai/codex/pull/10674)
   - Added the original feature-gated persistent JavaScript REPL and established nested tool calls from JavaScript.

4. **Code mode moved from external Node to in-process V8**
   - Commit: [`e4eedd6170580d5b06fb539635a78f261a6b7369`](https://github.com/openai/codex/commit/e4eedd6170580d5b06fb539635a78f261a6b7369)
   - PR: [`openai/codex#15276`](https://github.com/openai/codex/pull/15276)
   - Preserved the model-facing `exec`/`wait` and `tools.*` surface while replacing the external Node runner with an in-process V8/Rust substrate.
   - The user-observed leftover Node server processes should therefore be described as workloads launched through nested `exec_command`, not automatically as the code-mode runtime itself.

5. **Code-mode cell lifecycle moved into a single-owner actor**
   - Commit: [`e2f074e16c522bfa55d9bcd344a5ea0ba5a4580f`](https://github.com/openai/codex/commit/e2f074e16c522bfa55d9bcd344a5ea0ba5a4580f)
   - PR: [`openai/codex#28599`](https://github.com/openai/codex/pull/28599)
   - Clarified that each code-mode cell actor owns cell execution, observation, callback completion, termination, and cleanup, while session services own session-wide registries and adapters.
   - This history supports leaving cell lifecycle rules untouched in Patch 1 and querying the existing session-level process manager for nested-process liveness.

## How to use blame correctly

Git blame is useful for locating the last commit that touched a line and for finding the surrounding PR discussion. It is not proof that the last editor:

- designed the subsystem;
- currently owns it;
- should be individually tagged;
- or is responsible for the defect.

For each important line, the final walkthrough should combine:

1. a commit-pinned code link;
2. blame/history for the immediate line;
3. the introducing or architecture-defining PR where available;
4. current CODEOWNERS rather than inferred personal ownership.

Current repository ownership at the selected upstream base assigns `/codex-rs/core/` to [`@openai/codex-core-agent-team`](https://github.com/openai/codex/blob/61a44880a85d2fd0d8770908dea5733495e571c8/.github/CODEOWNERS).

Recommendation: do not manually tag individual historical authors in the issue. The PR should naturally route through CODEOWNERS. A team mention should be used only if repository norms permit it and normal triage/review routing fails.

## Patch 1 data-flow and threat-model review

### New data

Patch 1 adds one internal metadata value: `Option<CellId>` representing the code-mode cell that created a unified-exec process.

- `None` means direct or unattributed invocation.
- `Some(cell_id)` means the invocation came from that typed code-mode cell.

This is crate-private invocation/process metadata, not a public API field.

### Source trust

The value is derived from existing typed internal dispatch metadata:

```rust
ToolCallSource::Direct => None,
ToolCallSource::CodeMode { cell_id, .. } => Some(CellId::new(cell_id)),
```

It is not parsed from:

- JavaScript output;
- command text;
- nested call-ID strings;
- model-provided arbitrary ownership labels;
- or process stdout/stderr.

### Storage boundary

The value travels through `UnifiedExecContext` and is copied into the existing manager-owned `ProcessEntry` when a yielded process is stored. The patch does not add a second registry or new lifetime owner.

### Read boundary

The new manager query:

- is `pub(crate)`;
- operates on the existing session-level process store;
- uses exact typed `CellId` equality;
- excludes entries whose process has exited;
- returns only numeric logical session IDs;
- exposes no process handles or command contents;
- and does not mutate, terminate, prune, or resume anything.

The async wait is only for acquiring the existing Tokio mutex. Once acquired, the code performs a bounded synchronous scan of the in-memory process map with no nested `.await`.

### Disclosure boundary

The displayed session IDs are not a new class of secret. A nested `exec_command` result already returns its `session_id` to the same JavaScript cell. Patch 1 restores that same control information to the same model/session when JavaScript projects it away.

The exact-cell filter is important because a session may contain processes from more than one code-mode cell. Cross-cell and unattributed entries are excluded by both implementation and tests.

### JavaScript and protocol surface

Patch 1 does not modify:

- the JavaScript nested result schema;
- V8 helper APIs;
- `tools.exec_command` arguments;
- app-server protocol messages;
- public CLI flags;
- Electron code;
- process termination policy;
- or cell lifecycle rules.

The only model-visible change is an additional terminal status line containing matching live session IDs.

## Resource-impact terminology

The user reports that two leftover Node server processes retained approximately 7–8 GB of RAM until they were terminated. That is a concrete and potentially severe operational impact if preserved evidence supports it.

The report should distinguish three claims:

1. **Observed process resource retention**
   - Two live child/server processes continued consuming substantial memory.
   - This may be described in the human account as a first-person incident, ideally with a scrubbed process snapshot, timestamp, or log citation.

2. **Confirmed Patch 1 defect**
   - The processes remained manager-owned and live, but the model-visible terminal result lost their session IDs after JavaScript discarded them.
   - The model therefore lacked the normal control handles needed to poll or terminate those processes.

3. **What is not proven**
   - The Rust process manager did not necessarily leak unreachable heap memory.
   - Patch 1 does not automatically terminate or deallocate the child processes.
   - The exact 7–8 GB figure should not appear as formal validation unless supporting evidence is preserved.

Preferred language:

- “orphaned live process from the model’s perspective”;
- “lost session-control visibility”;
- “resource-retention risk”;
- “background-process lifecycle hazard”.

Avoid calling the implementation defect itself a literal memory leak unless a separate memory-ownership investigation proves unreachable allocated memory.

## Walkthrough additions

The final Agent 3 walkthrough should include:

1. subsystem history before current code;
2. code-owner and blame interpretation;
3. the exact data-flow through handler, context, process entry, manager query, and terminal renderer;
4. a Rust beginner’s explanation of `Option`, `Arc`, `Weak`, Tokio `Mutex`, and `pub(crate)`;
5. a threat-model table covering source, scope, storage, read access, disclosure, and lifecycle effects;
6. why this is a deliberately small outsider-friendly patch;
7. what would have been overreach: new public schemas, generic origin enums, new lifecycle policy, automatic cleanup, event APIs, or recovery mechanisms;
8. the distinction between compiling/exercising `codex-core` and validating every Codex product surface.
