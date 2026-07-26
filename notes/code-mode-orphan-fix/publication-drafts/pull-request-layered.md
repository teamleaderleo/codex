# Layered pull-request draft

Status: unpublished. Insert the actual standalone issue number before publication.

## Proposed title

code-mode: report live nested session IDs in terminal results

## Proposed body

### Summary

A code-mode cell can launch nested `exec_command` calls, discard their returned session IDs while retaining only `.output`, and then finish while those terminal sessions remain live. The outer result currently has no way to restore the missing handles even though the existing unified-exec process manager still owns the processes.

This PR carries the existing typed creator-cell identity into stored live process entries, queries the existing manager for exact-cell still-live sessions when the cell reaches a terminal result, and reports those session IDs in the status header.

Fixes #ISSUE_NUMBER.

### Design

The data flow is deliberately small:

1. [`ExecCommandHandler`](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L132-L138) translates existing `ToolCallSource::CodeMode { cell_id, .. }` metadata into an optional typed `CellId`.
2. [`UnifiedExecContext`](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L76-L99) carries that attribution to process creation, and the existing [`ProcessEntry`](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L189-L199) retains it beside the manager-owned process.
3. [`live_process_ids_created_by_cell`](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L168-L180) performs a read-only exact-cell, live-only lookup and returns logical session IDs in numeric order.
4. [Code-mode terminal response handling](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/code_mode/mod.rs#L199-L300) performs the lookup only for `Result` and `Terminated`, then adds `Background sessions still running: ...` to the existing status header.

The existing process manager remains the sole liveness authority. The patch does not infer ownership from JavaScript output, command text, or nested call-ID strings and does not create a second registry.

### Behavioural boundaries

This PR is visibility-only.

- Successful results, failed results, and explicit termination results may report matching still-live session IDs.
- Ordinary yielded code-cell responses remain unchanged.
- Exited processes are not reported.
- One cell cannot disclose another cell's processes.
- Direct or unattributed process entries are excluded.
- Nested tool-call IDs remain opaque.
- The JavaScript-visible nested result schema is unchanged.
- No process-lifetime, termination, pruning, shutdown, interrupt, recovery, wake-up, or public-protocol policy changes.

The code-mode emitted output is truncated before the status header is prepended, so the live-session warning is outside that specific truncation boundary. The complete tool result remains subject to later global conversation-history limits.

Example output, using illustrative IDs:

```text
Script completed
Background sessions still running: 6306, 11236
Wall time ...
Output:
...
```

### Why this boundary

Background terminals intentionally support long-running servers, watchers, and interactive work. Automatically killing matching sessions or blocking cell completion would change lifecycle policy and could destroy valid background work.

The failure is narrower: the manager still owns the live processes, but terminal code-mode rendering lacks the creator attribution needed to restore copied session IDs that JavaScript discarded. This PR repairs that information path without deciding when background work should stop.

### Alternatives considered

<details>
<summary>Optional design alternatives</summary>

- **Infer ownership from JavaScript output:** rejected because the confirmed failure occurs when JavaScript discards the result object or keeps only `.output`.
- **Append IDs to command output:** rejected because it mixes control metadata with command output, changes an established result contract, and still depends on JavaScript preserving that output.
- **Encode creator identity in call-ID strings:** a feasibility prototype showed prefix filtering could work, but it would turn opaque identifier formatting into an ownership API and introduce collision and tracing concerns.
- **Add a second per-cell registry:** rejected because the unified-exec manager already owns the process handles and defines liveness; a second registry would duplicate lifecycle and race handling.
- **Terminate or wait for matching sessions:** rejected for this PR because either choice changes product lifecycle policy and can break legitimate long-running background work.
- **Add a JavaScript or app-server schema field:** rejected because the nested result already contains `session_id`, JavaScript can discard any returned field, and a public protocol change would require separate compatibility and ordering design.

</details>

### Tests

The final test shape follows the repository's documented [single aggregate integration-test binary](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/all.rs#L1-L9). The five acceptance cases live in the existing code-mode suite at [`tests/suite/code_mode/orphan_sessions.rs`](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs).

Coverage:

1. multiple discarded live session IDs are reported exactly once in numeric order;
2. an exited session is excluded while a surviving session is reported;
3. one completing cell cannot disclose another cell's live process;
4. large emitted output cannot displace the warning at the code-mode truncation boundary; and
5. ordinary yielded responses do not contain the terminal-only warning.

A direct network-independent [manager-query unit test](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod_tests.rs#L332-L395) covers exact-cell inclusion, another-cell exclusion, unattributed-entry exclusion, exited-entry exclusion, and numeric ordering.

The acceptance harness places every process-creating submission inside cleanup protection. The one-survivor case uses a bounded PID/filesystem handshake rather than fixed elapsed-time sleeps.

### Validation

Repository-native focused validation on Linux aarch64:

- `just fmt`: passed;
- `just fix -p codex-core`: passed;
- four focused unit tests: `4 passed; 0 failed`;
- five aggregate acceptance cases: `5 passed; 0 failed`;
- two existing compatibility tests, repeated ten times each on the final candidate: `20/20 passed`;
- the same tests, repeated ten times each on exact upstream base `61a44880a85d2fd0d8770908dea5733495e571c8`: `20/20 passed`;
- clean worktree and `git diff --check`: passed.

A matched broad `just test -p codex-core` differential was red on both the production-equivalent candidate and the exact upstream base. Environment dependencies, unavailable helper binaries, sandbox or runner limitations, timeouts, and unrelated baseline assertions accounted for the retained failures. The differing broad-run test names passed repeated focused executions on both refs, leaving no persistent candidate-only failure. The broad project suite is not claimed green.

The complete workspace suite was not run.

<details>
<summary>Validation and evidence links</summary>

- [negative reproduction](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5)
- [final comparison](https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...760216784efaee1ba6a3b1250349f31d5f91c7ca)
- [supplemental focused validation receipt](https://github.com/teamleaderleo/codex/blob/728e2e07462aea6505925366158b5f04644ad034/notes/code-mode-orphan-fix/agent-2-test-polish-supplemental-validation-receipt.md)
- [matched broad-suite differential](https://github.com/teamleaderleo/codex/blob/728e2e07462aea6505925366158b5f04644ad034/notes/code-mode-orphan-fix/agent-1-clean-candidate-project-failure-inventory.md)

</details>

### Technical record

The public deep dive explains the runtime path, historical architecture, Rust ownership model, threat model, test evolution, alternatives, and validation limits:

- [public technical deep dive](https://github.com/teamleaderleo/codex/blob/01be2774a304529db9962d827d678576a85f4330/notes/code-mode-orphan-fix/publication-drafts/public-deep-dive.md)
- [works cited](https://github.com/teamleaderleo/codex/blob/01be2774a304529db9962d827d678576a85f4330/notes/code-mode-orphan-fix/publication-drafts/works-cited.md)

### Related work

[#34866](https://github.com/openai/codex/issues/34866) provides related prior symptom coverage involving `Script completed` and a still-live nested shell. The standalone issue for this PR defines the narrower executable contract where JavaScript discards still-live session IDs and terminal rendering reports the exact-cell live session IDs.