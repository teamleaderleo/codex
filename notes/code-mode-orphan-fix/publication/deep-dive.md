# How code-mode completion can lose live session handles

This is the technical record behind [openai/codex#35613](https://github.com/openai/codex/issues/35613), the tested implementation, and the associated validation history.

## Executive summary

A code-mode JavaScript cell can start nested `exec_command` calls, keep only each result's `.output`, and discard every returned `session_id`. The nested commands may remain live in the session-level unified-exec manager after the JavaScript cell reports `Script completed`.

The resulting defect is not merely missing status text. The manager still owns the work, but the model has lost every control handle exposed by the current tool surface for inspecting, continuing, or terminating it.

The tested implementation preserves the existing code-mode `CellId` through unified exec, stores it on the manager-owned process entry, queries still-live entries for the exact terminal cell, and adds their logical session IDs to the existing status text.

```text
CodeMode CellId
  → UnifiedExecContext
  → ProcessEntry
  → exact-cell live-process lookup
  → terminal response status
```

The implementation does not change process ownership, lifetime, cleanup, polling, wake-up behaviour, JavaScript result fields, public protocol shapes, or call-ID generation.

## Minimal failure

```js
const outputs = (await Promise.all([
  tools.exec_command({ cmd: "printf orphan-a; sleep 60", yield_time_ms: 250 }),
  tools.exec_command({ cmd: "printf orphan-b; sleep 60", yield_time_ms: 250 }),
])).map(({ output }) => output);

text(outputs.join("|"));
```

The JavaScript values copied into `outputs` do not own the nested processes. Unified exec keeps the yielded processes alive, while the copied `session_id` values disappear with the discarded result objects.

Before the fix, the terminal response can therefore look like:

```text
Script completed
Wall time ...
Output:
orphan-a|orphan-b
```

The [negative reproduction](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5) preserves that state as an executable test: two background terminals remain manager-owned while the model-visible completion header contains no handle for either one.

## Observed incident and impact

The isolated reproduction came from a real Codex Desktop session on bundle version `26.715.12143`.

A code-mode cell launched two Playwright screenshot commands and a `curl` command concurrently. Each nested command used a 30-second yield timeout, and the JavaScript forwarded only `.output`. The cell then reported `Script completed` without the logical session IDs for the two yielded Playwright commands.

Codex launched replacement screenshot commands while the original process groups remained alive. The original groups survived for more than four days and had been reparented to PID 1 (`launchd`). macOS process metadata attributed them to Codex Desktop:

```text
CODEX_INTERNAL_ORIGINATOR_OVERRIDE=Codex Desktop
__CFBundleIdentifier=com.openai.codex
responsible path=/Applications/ChatGPT.app/Contents/MacOS/ChatGPT
```

The persisted process registry retained the original commands and logical session IDs, while both records had `"osPid": null`.

At inspection time, Activity Monitor showed the two surviving `node` processes at 3.62 GB each in the Memory column:

<img width="829" height="86" alt="macOS Activity Monitor showing two surviving node processes at 3.62 GB each" src="https://github.com/user-attachments/assets/4f6c1a5a-3620-44ad-ad39-038a9f6e6a51" />

*Activity Monitor at inspection time, showing the two surviving `node` processes at 3.62 GB each—approximately 7.24 GB combined.*

Separate process inspection measured approximately:

- 1.38 GB resident memory;
- 6.4 GB swapped memory.

The processes required manual process-group termination outside Codex.

The visibility gap did not itself create the broader cross-runtime orphaning policy. It removed the model's available opportunity to notice and clean up the work before owner loss occurred.

## Relationship to #34866

[#34866](https://github.com/openai/codex/issues/34866) covers the broader contradiction between wrapper completion and nested-process state, including richer lifecycle representation and which continuation operation should be authoritative.

Issue #35613 isolates a smaller invariant:

> A terminal code-mode cell should preserve model-visible access to still-live manager-owned nested commands attributed to that exact cell, even when JavaScript discards every returned result object.

The proposed implementation does not redefine wrapper completion, process lifetime, cleanup, polling, wake-up behaviour, or recovery policy.

## Tested implementation

The implementation and test coverage are on [`fix/code-mode-live-session-ids`](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-ids).

Relevant refs:

- selected upstream base: [`61a44880`](https://github.com/openai/codex/commit/61a44880a85d2fd0d8770908dea5733495e571c8);
- bounded implementation milestone: [`eb530466`](https://github.com/teamleaderleo/codex/commit/eb530466cafac0a5aee86342cd2b5ada9047d448);
- latest implementation head: [`77e7e314`](https://github.com/teamleaderleo/codex/commit/77e7e3149df366236db2426596c23ebbe1d6bb48);
- base-to-head comparison: [`61a44880...77e7e314`](https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...77e7e3149df366236db2426596c23ebbe1d6bb48).

The implementation branch currently resolves to `77e7e314`. That commit contains the same production implementation as `eb530466`; its additional commit only adds test-side Windows-target skips for POSIX acceptance commands.

### Preserve creator identity

Nested dispatch already carries the public code-mode cell ID through `ToolCallSource::CodeMode`. The implementation carries that identity through `UnifiedExecContext` and stores it on the manager-owned `ProcessEntry`.

Creator provenance remains crate-internal. It adds no JavaScript field, public result property, protocol event, or call-ID encoding.

### Query the existing liveness authority

A read-only manager query selects entries whose creator matches the exact `CellId`, filters them through existing `has_exited()` state, and returns their logical manager process IDs.

The same value is called `process_id` internally and exposed to the model as `session_id`.

The lookup cannot determine whether JavaScript retained, printed, copied, or discarded an individual handle, so it reports the manager-observed exact-cell live set.

### Select terminal responses

Ordinary `RuntimeResponse::Yielded` responses describe a code-mode cell that remains active and resumable. They keep their existing status.

The implementation reports live IDs for terminal responses:

- successful `Result`;
- failed `Result`;
- `Terminated`.

### Keep the warning outside emitted-output truncation

Code-mode emitted payload is truncated before the status header is prepended. A large emitted value therefore cannot remove the background-session warning at that boundary. Later whole-conversation limits still apply to the complete tool result.

## Exact-cell attribution contract

Reporting every live process in the session would let one completing cell claim another cell's unrelated work.

The contract is:

> Report only manager-owned processes attributed to the exact cell whose selected terminal response is being formatted.

Remote public cell IDs are namespaced by host generation. Later generations use `g{N}:<id>`, and stale-generation IDs are rejected when translated back to a remote ID. Typed `CellId` equality therefore remains the attribution key across remote host restarts within one Codex session.

## Model-visible display contract

The final reviewed formatter policy is:

- sort matching logical session IDs numerically;
- display at most 64 IDs;
- select the deterministic sorted prefix;
- append the exact omitted count when overflow occurs, for example `(+7 more)`.

The limit is intentionally independent of the unified-exec manager's soft process-store cap:

```rust
// Bound independently because this fragment enters model-visible context.
const MAX_INLINE_BACKGROUND_SESSION_IDS: usize = 64;
```

A future process-store capacity change should not silently change the model-visible output budget. Under normal manager capacity, all exact-cell live IDs remain visible.

Because the current tool surface has no separate session-enumeration operation, IDs beyond the rare over-limit prefix are not directly recoverable from the suffix. A future model-visible enumeration path would close that remaining edge case without requiring an unbounded terminal fragment.

## Liveness semantics

The lookup describes manager-observed state at one instant. A selected process can exit immediately after lookup.

`UnifiedExecProcess::has_exited()` also has a backend asymmetry:

- local processes consult cached state and the live local handle;
- exec-server-backed processes consult cached manager state.

A recently exited remote process can therefore remain visible until its exit is reflected in manager state. Four Docker acceptance cases exercised exec-server live-process reporting. The exit-then-exclude survivor case ran locally because it embeds host `TempDir` paths not shared with Docker or Wine executors.

## Windows and Wine-exec test boundary

Wine-exec is not a native Windows-host run. The Rust integration-test process runs on an x86-64 Linux host while Bazel cross-builds the Windows exec server and launches that server under Wine. The test environment consequently reports a Windows **execution target** even though the test binary itself is Linux.

That distinction explains the two skip mechanisms visible in `orphan_sessions.rs`:

- `#[cfg_attr(windows, ignore = "no exec_command on Windows")]` applies only when the Rust test binary itself is compiled for Windows. It does not fire in Wine-exec because the test binary is Linux.
- `skip_if_target_windows!` checks the selected remote execution target at runtime. It does fire in Wine-exec.
- `skip_if_remote!` fires for both Docker and Wine when a case depends on local-host filesystem topology.

For Patch 1 specifically:

- `code_mode_completion_surfaces_discarded_live_exec_sessions` skips under Wine because its nested commands use POSIX shell syntax;
- `large_emitted_output_does_not_truncate_live_session_warning` skips under Wine for the same reason;
- `yielded_cell_response_does_not_include_completion_session_warning` skips under Wine for the same reason;
- `code_mode_completion_reports_only_sessions_created_by_current_cell` skips under Wine for the same reason;
- `code_mode_completion_reports_only_surviving_nested_session` skips in every remote environment because its PID/release handshake embeds host `TempDir` paths unavailable to the executor.

Therefore, a successful Wine suite validates the Bazel/Wine harness and the broader shared `codex-core` suite on the latest implementation head. It does **not** mean that the five Patch 1 acceptance scenarios executed their substantive assertions against Windows.

A prior attempt that failed during Bazel or Wine setup would not have printed those runtime skip messages because the Rust test process never started. That is a harness failure, not evidence that the skip conditions were absent or incorrect.

The repository-native command is:

```sh
bazel test //codex-rs/core:core-all-wine-exec-test
```

The temporary latest-head workflow uses the same target with full output and cache disabled:

```sh
bazel test //codex-rs/core:core-all-wine-exec-test \
  --nocache_test_results \
  --test_output=all
```

## Validation

The complete evidence ledger is maintained separately so public CI receipts, repeated local history, harness failures, ref boundaries, and target-specific skips are not collapsed together:

- [validation history](validation-history.md)

Summary:

| Coverage | Ref or tested tree | Result |
|---|---|---|
| Repeated candidate/base local validation | Earlier `76021678` work | 20/20 candidate repetitions and 20/20 base repetitions passed |
| Focused formatter and manager tests | Exact tested tree committed as `eb530466` | 9 passed |
| Formatting, scoped fix, diff and worktree checks | `eb530466` | passed; worktree clean |
| Local acceptance | Value-equivalent bounded implementation workspace | 5 passed |
| Docker/Ubuntu 24.04 remote acceptance | Same workspace | 4 passed; 1 explicit host-`TempDir` skip |
| Existing compatibility tests | Same workspace | 2 passed |
| Full `codex-core` library suite | Latest implementation head `77e7e314` | queued when this revision was published |
| Full shared core suite against Windows exec under Wine | Latest implementation head `77e7e314` | queued when this revision was published |

Public receipts and launchers:

- [focused final-head run 30220464228](https://github.com/teamleaderleo/codex/actions/runs/30220464228);
- [local and Docker acceptance run 30217686056](https://github.com/teamleaderleo/codex/actions/runs/30217686056);
- [latest-head full library workflow](https://github.com/teamleaderleo/codex/actions/workflows/temp-code-mode-full-suite.yml);
- [full-library launcher commit `f980d5a3`](https://github.com/teamleaderleo/codex/commit/f980d5a3e3e2bfe6c9058aaa90dbf1a0aae96954);
- [latest-head Wine workflow](https://github.com/teamleaderleo/codex/actions/workflows/temp-code-mode-wine-suite.yml);
- [Wine launcher commit `d7ebb964`](https://github.com/teamleaderleo/codex/commit/d7ebb96477a384b73c1bf59fb29e7179fc755870).

Two earlier Actions attempts failed in the validation harness before producing product-test results and are recorded separately in the ledger rather than counted as test failures.

## Code and test references

### Upstream baseline

- [Code-mode terminal response formatting](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/codex-rs/core/src/tools/code_mode/mod.rs#L199-L275)
- [`ToolInvocation` carries `ToolCallSource`](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/codex-rs/core/src/tools/context.rs#L46-L71)
- [`ExecCommandHandler` baseline context construction](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L108-L133)
- [Unified-exec tool surface](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/codex-rs/core/src/tools/handlers/unified_exec.rs#L22-L27)

### Tested implementation

- [Nested dispatch preserves source-cell identity](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L362-L374)
- [`ExecCommandHandler` reconstructs the typed source cell](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L132-L138)
- [`UnifiedExecContext` carries creator metadata](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L76-L99)
- [`ProcessEntry` stores creator-cell attribution](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L189-L200)
- [`live_process_ids_created_by_cell`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L168-L180)
- [Terminal-response lookup and `Yielded` exclusion](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L201-L269)
- [Bounded status formatting](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L270-L305)
- [Acceptance module](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs)
- [Test-environment target selection](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/tests/common/test_environment.rs#L42-L66)

## Alternatives considered

- Recover IDs from JavaScript output: impossible after JavaScript discards the object.
- Append IDs to nested command output: mixes control metadata with program output and remains discardable.
- Encode creator identity in call IDs: turns an opaque identifier into an ownership API.
- Add another per-cell registry: duplicates manager bookkeeping.
- Report every session process: violates exact-cell attribution.
- Wait for or terminate matching processes: changes lifecycle policy.
- Add a JavaScript field or protocol event: expands compatibility scope and can still be discarded.

## Scope boundary

The change is intentionally limited to preserving creator-cell provenance, querying existing manager-observed liveness, and restoring model-visible logical session handles in terminal code-mode status.

It does not change:

- process ownership;
- command lifetime or automatic termination;
- pruning or recovery policy;
- JavaScript schemas;
- protocol schemas or events;
- call-ID generation;
- polling, wake-up, or continuation semantics.
