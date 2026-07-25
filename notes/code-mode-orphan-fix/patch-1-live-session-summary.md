# Patch 1 handoff: surface live nested exec sessions

## Goal

When a code-mode JavaScript cell finishes while nested unified-exec commands are still running, make the outer result explicitly report those live session IDs.

Example target output:

```text
Script completed with 2 background sessions still running
Session IDs: 6306, 11236
Wall time 30.2 seconds
Output:
...
```

The exact wording is open for review. The invariant is that the outer result must not look fully terminal while live nested sessions remain undisclosed.

## Non-goals

- Do not automatically terminate background sessions in this patch.
- Do not change direct `exec_command` persistence behaviour.
- Do not add macOS-specific process recovery.
- Do not redesign code-mode cancellation.
- Do not infer command intent from command text.

## Confirmed behaviour

`ExecCommandToolOutput::code_mode_result` serializes a live unified-exec process as `session_id`. JavaScript can discard that field by reading only `result.output`. The outer runtime then reports `Script completed` when the JavaScript cell returns successfully, even if nested sessions remain live.

The observed incident used `Promise.all` with two Playwright calls and one `curl` call. Both Playwright calls reached their 30-second nested yield boundary, returned live session IDs internally, and continued running. The JavaScript printed only their output strings.

## Relevant code

Start with:

- `codex-rs/core/src/tools/context.rs`
  - `ExecCommandToolOutput`
  - `ToolOutput::code_mode_result`
- `codex-rs/core/src/tools/code_mode/delegate.rs`
  - nested tool dispatch and `cell_id`
- `codex-rs/core/src/tools/code_mode/mod.rs`
  - `handle_runtime_response`
  - runtime status formatting
- `codex-rs/core/src/tools/code_mode/execute_handler.rs`
  - initial code-cell result handling
- `codex-rs/core/src/tools/code_mode/wait_handler.rs`
  - terminal wait handling
- `codex-rs/core/src/unified_exec/process_manager.rs`
  - live process lookup and lifecycle
- `codex-rs/core/tests/suite/code_mode.rs`
  - integration test harness

## Preferred design properties

- Track typed session IDs; do not scrape `output` strings or serialized JSON.
- Associate nested live sessions with their originating code-mode `CellId`.
- Before reporting a warning, confirm that each session is still live in the process manager.
- Make the warning resistant to output truncation, preferably by inserting it in the status/header section.
- Clear per-cell bookkeeping when the cell reaches a terminal state.
- Avoid changing the JavaScript-visible nested result schema unless necessary.

## Candidate implementation routes

### A. Per-cell live-session tracker

Record live session IDs when nested tool results return, keyed by `CellId`. At outer cell completion, query the process manager and append the surviving IDs to the model-facing result.

Pros:

- typed and explicit;
- catches discarded JavaScript fields;
- can verify current liveness;
- keeps nested result compatibility.

Cons:

- adds state and cleanup responsibilities to the code-mode broker/service.

### B. Runtime observes returned JavaScript values

Teach the code-mode runtime to inspect tool results retained by JavaScript and summarize live sessions.

Pros:

- closer to the JavaScript execution layer.

Cons:

- may miss results that JavaScript discards;
- likely crosses crate or process boundaries;
- less suitable for the confirmed failure.

### C. Change nested exec result ergonomics only

Rename fields or require explicit disposal semantics.

Pros:

- potentially cleaner API long term.

Cons:

- does not protect existing code that ignores the handle;
- larger compatibility discussion;
- insufficient as the first fix.

Route A is the current recommendation.

## Regression test

Suggested name:

```rust
code_mode_completion_surfaces_discarded_live_exec_sessions
```

Test scenario:

1. Start two deterministic long-running helper processes from a code-mode cell.
2. Give each nested `exec_command` a very small yield time.
3. Await both with `Promise.all`.
4. Print only `result.output`, deliberately discarding `session_id`.
5. Allow the outer cell to complete.
6. Assert that the model-facing code-mode result reports both still-live session IDs.
7. Terminate both sessions during teardown.
8. Assert the process manager contains no surviving test sessions.

Test requirements:

- cross-platform helper or existing fixture;
- deterministic process IDs if supported by the test harness;
- bounded waits;
- teardown runs even after assertion failure;
- no reliance on network access.

## Edge cases for review

- A session exits between nested result collection and outer result generation.
- One nested command exits and one remains live.
- Repeated waits on the same cell.
- The cell fails after creating a live session.
- The cell is explicitly terminated.
- Output is truncated.
- Multiple nested calls refer to the same session.
- A process ID is released and reused before the summary is generated.

## Deliverables

1. Failing regression test.
2. Minimal implementation.
3. Focused unit/integration tests for bookkeeping cleanup if needed.
4. Before/after example output.
5. Short design note explaining why the patch does not alter persistence policy.

## Stop conditions

Pause and report before broadening scope if:

- the design requires changing public protocol types across several crates;
- reliable liveness checks are unavailable;
- cleanup ownership becomes ambiguous;
- the test cannot safely guarantee process teardown;
- the implementation starts changing subagent completion policy.