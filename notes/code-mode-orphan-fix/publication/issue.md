# Codex app bug report

## Title

Code-mode completion can omit IDs for still-live nested exec sessions

## What version of the Codex App are you using?

ChatGPT Powered by Codex & OWL Version 26.721.41059  
Released Jul 25, 2026

## What subscription do you have?

ChatGPT Plus

## What platform is your computer?

MacBook Air (15-inch), macOS  
`uname -mprs`: `<paste command output>`

## What issue are you seeing?

Code-mode JavaScript can discard the `session_id` values returned by nested `exec_command` calls while the unified-exec manager continues to own the live processes.

The cell can then report `Script completed` without showing the session IDs needed to inspect, continue, or terminate those commands.

This is the narrower lost-handle case within the broader wrapper/process mismatch reported in [#34866](https://github.com/openai/codex/issues/34866).

## What steps can reproduce the bug?

Run a code-mode JavaScript cell that starts nested commands, then keeps only each command's `.output` and discards the returned `session_id`:

```js
const outputs = (await Promise.all([
  tools.exec_command({ cmd: "printf orphan-a; sleep 60", yield_time_ms: 250 }),
  tools.exec_command({ cmd: "printf orphan-b; sleep 60", yield_time_ms: 250 }),
])).map(({ output }) => output);

text(outputs.join("|"));
```

The cell returns output similar to:

```text
Script completed
Wall time ...
Output:
orphan-a|orphan-b
```

Both nested commands can still be live and listed by the unified-exec manager, but their logical session IDs are absent from the model-visible response because the JavaScript code discarded the original result objects.

An [executable negative reproduction](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5) preserves this before-state as a test.

I can provide an affected app session ID or additional logs if they would help with tracing.

## What is the expected behavior?

When a code-mode cell reaches a terminal response, its existing status text should include the logical IDs of any still-live nested commands created by that exact cell.

For example:

```text
Script completed
Background sessions still running: 6306, 11236
Wall time ...
Output:
orphan-a|orphan-b
```

The exact wording and display bound are implementation choices. The required property is that the completing cell preserves model-visible access to manager-owned nested commands whose JavaScript result objects were discarded.

## Additional information

Nested tool dispatch already carries the originating code-mode cell ID, and the terminal response still identifies that cell. Yielded commands remain owned by the session-level unified-exec manager, but manager-owned process entries don't retain the corresponding creator-cell provenance, so the completion path can't map the cell back to its live logical session IDs.

At the [verified upstream snapshot](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/codex-rs/core/src/tools/code_mode/mod.rs#L201-L275), `handle_runtime_response` still formats terminal cell output without an equivalent manager lookup.

### Possible implementation direction

Conceptually, with names and surrounding fields omitted:

```rust
struct ProcessEntry {
    creator_cell_id: Option<CellId>,
    // existing fields...
}

// When formatting a terminal response:
let live_session_ids =
    process_manager.live_process_ids_created_by_cell(&cell_id);
```

The lookup would be read-only. It wouldn't wait for, terminate, prune, or otherwise mutate any process.

The proposed fix would leave these unchanged:

- process ownership and lifetime;
- cleanup, pruning, polling, and wake-up policy;
- JavaScript result fields;
- public protocol schemas and event types;
- call-ID generation.

It would report only sessions created by the exact cell whose terminal response is being formatted, so one cell couldn't claim another cell's live work.

Local process handles can expose process exit directly, while exec-server-backed entries rely on exit state already reflected in the manager. A recently exited remote process could therefore appear until the manager's cached state advances.

The exploratory prototype currently reports IDs for successful and failed `Result` responses and for `Terminated`, while leaving `Yielded` unchanged. The remaining scope questions are:

- Should live session IDs be shown only when a cell completes successfully, or also when it fails or is terminated?
- Is manager-observed liveness acceptable for exec-server-backed processes, given that exit reflection can briefly lag the underlying process?

I did a deeper technical review of the prototype, including the data flow, exploratory implementation, validation history, limitations, source references, and design tradeoffs: [technical deep dive](https://github.com/teamleaderleo/codex/blob/review/code-mode-issue-ready/notes/code-mode-orphan-fix/publication/deep-dive.md).

The exploratory implementation and tests are together on [`fix/code-mode-live-session-ids`](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-ids).