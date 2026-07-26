# Report live nested session IDs in code mode

Unpublished pull-request text. Replace `#ISSUE_NUMBER` after the issue is opened.

Fixes #ISSUE_NUMBER.

## Why

A code-mode cell can start nested `exec_command` calls, keep only their `.output`, and discard the returned session IDs. The cell can then finish while those terminal sessions remain live. The existing unified-exec process manager still owns the processes, but the terminal code-mode result has no exact way to recover and report the missing session IDs.

The change restores that control information without changing when background processes are allowed to remain running.

## What changed

1. [`ExecCommandHandler`](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L132-L138) carries the existing code-mode cell ID into unified exec.
2. [`UnifiedExecContext` and `ProcessEntry`](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L76-L99) retain that attribution with stored live process entries.
3. [`live_process_ids_created_by_cell`](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L168-L180) returns the exact cell's still-live session IDs in numeric order.
4. [Terminal code-mode response handling](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/code_mode/mod.rs#L199-L300) adds those IDs to `Result` and `Terminated` status output.

The existing process manager remains the only liveness authority. The change does not infer ownership from JavaScript output, command text, or call-ID strings, and it does not add a second process registry.

Example output, using illustrative session IDs:

```text
Script completed
Background sessions still running: 6306, 11236
Wall time ...
Output:
...
```

## Boundaries

- Ordinary yielded code-cell responses are unchanged.
- Exited sessions are not reported.
- One cell cannot report another cell's sessions.
- Direct or unattributed process entries are excluded.
- Nested tool-call IDs remain opaque.
- The JavaScript-visible nested result schema is unchanged.
- Process lifetime, automatic termination, pruning, shutdown, interrupt, recovery, wake-up, and public-protocol behaviour do not change.

Code-mode emitted output is truncated before the status header is added, so the live-session line is outside that truncation step. The complete tool result remains subject to later global conversation-history limits.

<details>
<summary>Alternatives considered</summary>

- Reading session IDs from JavaScript output cannot work when JavaScript discards the result object.
- Appending IDs to command output would mix control data with program output and would still depend on JavaScript preserving it.
- Encoding ownership in call-ID strings would turn opaque formatting into an ownership API.
- A second per-cell registry would duplicate the existing manager's liveness and lifecycle handling.
- Automatically waiting for or terminating sessions would change background-process policy.
- A new JavaScript or app-server field would not solve JavaScript discarding the returned object and would broaden compatibility work.

</details>

## Testing

The repository uses a [single aggregate integration-test binary](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/all.rs#L1-L9). The five acceptance cases are in the existing code-mode suite at [`tests/suite/code_mode/orphan_sessions.rs`](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs).

They cover:

1. multiple discarded live session IDs and numeric ordering;
2. exited-session exclusion;
3. exact completing-cell isolation;
4. warning placement outside code-mode emitted-output truncation; and
5. yielded-response neutrality.

A direct [manager-query unit test](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod_tests.rs#L332-L395) covers exact-cell inclusion, another-cell exclusion, unattributed entries, exited entries, and numeric ordering without network or shell timing.

Repository-native focused validation on Linux aarch64:

- `just fmt`: passed;
- `just fix -p codex-core`: passed;
- four focused unit tests: `4 passed; 0 failed`;
- five aggregate acceptance cases: `5 passed; 0 failed`;
- two compatibility tests on the final candidate: `20/20 passed`;
- the same tests on exact upstream base `61a44880a85d2fd0d8770908dea5733495e571c8`: `20/20 passed`;
- clean worktree and `git diff --check`: passed.

The [final comparison](https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...760216784efaee1ba6a3b1250349f31d5f91c7ca) contains the complete code and test diff.

A matched broad `just test -p codex-core` run was red on both candidate and exact base. Focused comparison found no persistent candidate-only failure. The broad project suite is not claimed green, and the complete workspace suite was not run.

## Related issue

[#34866](https://github.com/openai/codex/issues/34866) covers a related symptom involving `Script completed` and a still-live nested shell. The standalone issue for this change defines the narrower case where JavaScript discards live session IDs and terminal rendering reports the exact-cell live sessions.
