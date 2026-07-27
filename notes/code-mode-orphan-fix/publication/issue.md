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

The cell can then report `Script completed` without showing the session IDs needed to inspect or continue those commands.

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

Both nested commands can still be live and listed by the unified-exec manager, but their session IDs are absent from the model-visible response because the JavaScript code discarded the original result objects.

An [executable negative reproduction](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5) preserves this before-state as a test.

I can provide an affected app session ID or additional logs if they would help with tracing.

## What is the expected behavior?

At minimum, when a code-mode cell completes successfully, its existing status text should include the manager process IDs exposed to the model as `session_id` for any still-live nested commands created by that exact cell.

For example:

```text
Script completed
Background sessions still running: 6306, 11236
Wall time ...
Output:
orphan-a|orphan-b
```

This reports every still-live nested command attributed to the cell, including commands whose returned IDs the JavaScript retained; the completion path can't distinguish retained handles from discarded ones.

The exact status wording remains an implementation choice, but the final behavior must not hide any matching live ID. A display bound is only safe if every omitted ID remains available through another model-visible enumeration path.

## Additional information

The terminal status is currently derived from `RuntimeResponse`. Although that response identifies the completing cell and the handler can reach the unified-exec manager through `ExecContext`, existing manager entries don't retain creator-cell provenance, so the handler cannot map that cell to its still-live process IDs.

At the [verified upstream snapshot](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/codex-rs/core/src/tools/code_mode/mod.rs#L199-L275), `handle_runtime_response` still formats terminal cell output without an equivalent manager lookup.

### Possible implementation direction

Conceptually, with names and surrounding fields omitted:

```rust
struct ProcessEntry {
    creator_cell_id: Option<CellId>,
    // existing fields...
}

if let Some(cell_id) = terminal_cell_id(&response) {
    let live_session_ids = process_manager
        .live_process_ids_created_by_cell(cell_id)
        .await;

    // Include live_session_ids in the existing terminal status.
}
```

The lookup is read-only. It doesn't wait for, terminate, prune, or otherwise mutate any process.

The proposed fix leaves process ownership and lifetime, cleanup and polling policy, JavaScript result fields, public protocol shapes, and call-ID generation unchanged.

It reports only sessions created by the exact cell whose in-scope terminal response is being formatted, so one cell can't claim another cell's live work.

Local process handles can expose process exit directly, while exec-server-backed entries rely on exit state already reflected in the manager. A recently exited remote process can therefore appear until the manager's cached state advances.

The exploratory prototype currently reports IDs for successful and failed `Result` responses and for `Terminated`, while leaving `Yielded` unchanged. The remaining scope questions are:

- Should live session IDs be shown only when a cell completes successfully, or also when it fails or is terminated?
- Is manager-observed liveness acceptable for exec-server-backed processes, given that exit reflection can briefly lag the underlying process?

I did a deeper technical review of the prototype, including the data flow, exploratory implementation, validation history, limitations, source references, and design tradeoffs: [technical deep dive](https://github.com/teamleaderleo/codex/blob/review/code-mode-issue-ready/notes/code-mode-orphan-fix/publication/deep-dive.md).

The exploratory implementation and tests are together on [`fix/code-mode-live-session-ids`](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-ids).
