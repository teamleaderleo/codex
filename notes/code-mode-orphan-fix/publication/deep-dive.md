# How code-mode completion can lose live session handles

This is the full technical record behind the [standalone issue](issue.md), the [#34866 cross-link comment](related-34866-comment.md), and the [implementation draft](pull-request.md).

I used an exploratory implementation to trace the data flow, test the narrow fix, document its limitations, and separate the decisions that belong to maintainers from the parts already established by the current code.

## Executive summary

Nested `exec_command` calls can remain live after code-mode JavaScript discards their returned `session_id` values. The unified-exec manager still owns those processes, but the terminal response doesn't retain creator-cell provenance it can use to recover their logical IDs.

The proposed approach would carry the existing `CellId` through `UnifiedExecContext` into `ProcessEntry`, query still-live entries for that exact cell when its terminal response is formatted, and add their IDs to the existing status text. It wouldn't change process ownership, cleanup, polling, wake-up behaviour, JavaScript result fields, or public protocol shapes.

```text
CodeMode CellId
  → UnifiedExecContext
  → ProcessEntry
  → exact-cell live-process lookup
  → terminal completion status
```

## Failure

A code-mode JavaScript cell can start nested commands and retain only each result's `.output`:

```js
const outputs = (await Promise.all([
  tools.exec_command({ cmd: "printf orphan-a; sleep 60", yield_time_ms: 250 }),
  tools.exec_command({ cmd: "printf orphan-b; sleep 60", yield_time_ms: 250 }),
])).map(({ output }) => output);

text(outputs.join("|"));
```

Those copied JavaScript values don't own the processes. The session-level unified-exec manager keeps the yielded processes alive, but the final code-mode result has no cell-scoped path to identify and recover the discarded session IDs.

The [negative reproduction](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5) preserves that before-state as an executable test.

## Relationship to #34866

[#34866](https://github.com/openai/codex/issues/34866) covers the broader mismatch between wrapper completion and nested-process state and proposes richer lifecycle representation.

This issue isolates a smaller invariant: a completing cell should retain access to its manager-owned nested commands after JavaScript discards their result objects. The proposed approach wouldn't add a protocol field or choose a new continuation, cleanup, polling, or wake-up policy.

## Exploratory implementation

The implementation and tests are together on one branch:

- [exploratory implementation and tests](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-ids)
- [base-to-head comparison](https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...77e7e3149df366236db2426596c23ebbe1d6bb48)
- [prototype head `77e7e314`](https://github.com/teamleaderleo/codex/commit/77e7e3149df366236db2426596c23ebbe1d6bb48)

There isn't a separate test branch. The other commits and workflow runs below are checkpoints from the same exploratory line of work, not parallel implementations.

## Production data flow

### 1. Preserve the existing creator identity

Nested dispatch already carries `ToolCallSource::CodeMode { cell_id, ... }`. An implementation can copy the protocol value with `cell_id.as_str().to_string()` and reconstruct the typed `CellId` at the unified-exec boundary.

Using `as_str()` makes the matching contract explicit and avoids coupling ownership to a `Display` implementation meant for presentation.

### 2. Store provenance with the manager-owned process

`UnifiedExecContext` carries the creator identity. `ProcessEntry` stores it beside the logical session ID and manager-owned process, and `store_process` copies it into the entry.

That provenance stays crate-internal. Public tool results, protocol events, and call-ID formats wouldn't change.

### 3. Query the existing liveness authority

A read-only manager query can select entries whose creator matches the exact `CellId`, filter them through existing `has_exited()` state, and return their logical session IDs.

Numeric ordering belongs in the formatter because it's a display contract. The exploratory prototype sorts in both the manager and formatter; the smaller implementation only needs the formatter sort.

### 4. Choose the terminal outcomes in scope

Ordinary `RuntimeResponse::Yielded` responses describe a cell that remains active and resumable, so they should keep their existing status.

The remaining scope choice is whether live IDs appear on:

- successful `Result` only;
- successful and failed `Result`; or
- every terminal response, including `Terminated`.

### 5. Keep the status outside emitted-output truncation

Code-mode emitted payload is truncated before the status header is prepended. A large emitted value therefore can't remove the live-session line at that boundary. Later whole-conversation limits still apply to the complete tool result.

## Liveness semantics

The query would describe manager-observed state at one instant. A selected process could exit immediately after lookup.

`UnifiedExecProcess::has_exited()` also has a backend asymmetry:

- local processes consult cached state and the live local handle;
- exec-server-backed processes consult cached manager state.

A recently exited remote process could therefore appear until its exit is reflected in manager state. Four Docker acceptance cases exercised exec-server live-process reporting, but the exit-then-exclude survivor case ran locally only. The issue leaves the first-version backend scope open rather than hiding that limitation.

## Exact-cell contract

Reporting every live process in the session would let one completing cell claim another cell's unrelated work.

The narrow contract is:

> Report only manager-owned processes attributed to the exact cell whose terminal result is being formatted.

## Display contract

The prototype formats IDs in numeric order and applies a model-visible bound. The issue intentionally leaves the exact wording and bound open.

Manager capacity and model-visible output policy serve different purposes, so they should remain independent if a bound is retained.

## Upstream status

The selected prototype base [`61a44880`](https://github.com/openai/codex/commit/61a44880a85d2fd0d8770908dea5733495e571c8) is a direct ancestor of the verified upstream snapshot [`95637f70`](https://github.com/openai/codex/commit/95637f7056835fea66bdd0044414af480fc0fd74), five commits behind it.

Those five commits change none of the four production files touched by the prototype. At that snapshot, upstream still carries the code-mode cell ID through `ToolCallSource::CodeMode` and still formats terminal responses without a unified-exec manager lookup.

## Review size

The exploratory comparison contains 903 changed lines, dominated by a 527-line acceptance module. The core change can be reviewed with a much smaller set:

- the production provenance and lookup change;
- focused manager and formatter tests;
- one primary end-to-end discarded-handle regression.

## Validation

These checks establish prototype feasibility. They span closely related refs and workspaces rather than one final SHA.

### Relevant refs

| Role | Ref |
|---|---|
| Selected prototype base | [`61a44880`](https://github.com/openai/codex/commit/61a44880a85d2fd0d8770908dea5733495e571c8) |
| Display-bound milestone | [`eb530466`](https://github.com/teamleaderleo/codex/commit/eb530466cafac0a5aee86342cd2b5ada9047d448) |
| Exploratory branch head | [`77e7e314`](https://github.com/teamleaderleo/codex/commit/77e7e3149df366236db2426596c23ebbe1d6bb48) |
| Verified upstream snapshot | [`95637f70`](https://github.com/openai/codex/commit/95637f7056835fea66bdd0044414af480fc0fd74) |

### Result matrix

| Coverage | Ref or workspace | Result |
|---|---|---|
| Focused formatter and manager tests | `eb530466...` | 9 passed |
| Formatting, scoped fixes, diff, and worktree checks | `eb530466...` | passed |
| Local acceptance | pre-decoupling capped workspace with final remote harness | 5 passed |
| Docker/Linux remote acceptance | same workspace; four remote-safe cases | 4 passed |
| Existing compatibility tests | same workspace | 2 passed |

### Focused validation

- [GitHub Actions run 30220464228](https://github.com/teamleaderleo/codex/actions/runs/30220464228)
- GitHub-hosted Ubuntu 24.04
- validated head: `eb530466cafac0a5aee86342cd2b5ada9047d448`

Commands:

```sh
just fmt
just fix -p codex-core

UNIT_FILTER='test(/(live_process_ids_created_by_cell_filters_exited_and_sorts|terminal_cell_id_excludes_yielded_responses|terminal_script_status_surfaces_sorted_live_background_sessions|terminal_script_status_preserves_sessions_at_display_limit|terminal_script_status_caps_sessions_above_display_limit|terminal_script_status_sorts_before_truncation|terminal_script_status_formats_exact_omitted_count|terminal_script_status_omits_warning_for_empty_sessions|yielded_script_status_does_not_surface_background_sessions)$/)'

just test -p codex-core --lib -E "$UNIT_FILTER" --no-capture --no-tests=fail
git diff --check
git status --porcelain=v1 --untracked-files=all
```

Results:

- formatting and scoped fixes passed;
- nine focused tests passed;
- diff checks passed;
- the worktree was empty of changes.

The direct manager test covers exact-cell filtering, exited-entry exclusion, and logical ID ordering in the prototype.

### Acceptance validation

- [GitHub Actions run 30217686056](https://github.com/teamleaderleo/codex/actions/runs/30217686056)
- GitHub-hosted Ubuntu 24.04
- Docker remote executor: `ubuntu:24.04`

Results:

- five local acceptance cases passed;
- four remote-safe Docker cases exercised the exec-server path and passed;
- the exited-process/survivor case passed locally and was excluded from the Docker filter, so stale remote-exit exclusion remains untested;
- two existing code-mode compatibility tests passed;
- `git diff --check` passed.

## Code and test references

### Upstream code

- [Code-mode terminal response formatting](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/codex-rs/core/src/tools/code_mode/mod.rs#L201-L275)
- [`ToolInvocation` carries `ToolCallSource`](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/codex-rs/core/src/tools/context.rs#L47-L71)
- [`ExecCommandHandler` constructs unified-exec context without creator-cell provenance](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L108-L133)
- [Existing unified-exec context and process entries](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/codex-rs/core/src/unified_exec/mod.rs#L77-L181)

### Exploratory code

- [`ExecCommandHandler` captures the source cell](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L132-L138)
- [`UnifiedExecContext` carries creator metadata](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L76-L99)
- [`ProcessEntry` retains creator-cell attribution](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L189-L200)
- [`store_process` copies creator metadata into the entry](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/process_manager.rs#L944-L976)
- [`live_process_ids_created_by_cell`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L168-L180)
- [Terminal-response lookup and `Yielded` exclusion](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L201-L269)
- [Bounded status formatting](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L270-L305)
- [`has_exited()` backend asymmetry](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/process.rs#L194-L205)

### Prototype tests

- [Focused formatter tests](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L444-L612)
- [Direct manager lookup test](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod_tests.rs#L333-L395)
- [Acceptance module](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs)

## Related reports

| Issue | Relationship |
|---|---|
| [#34866](https://github.com/openai/codex/issues/34866) | Broader wrapper/process completion contradiction and lifecycle representation. |
| [#33816](https://github.com/openai/codex/issues/33816) | Model-side loss of a yielded session can produce false completion and duplicate commands. |
| [#14731](https://github.com/openai/codex/issues/14731) | Proposes keeping a turn active while unified-exec work remains live. |
| [#15723](https://github.com/openai/codex/issues/15723) and [#32188](https://github.com/openai/codex/issues/32188) | Background completion wake-up proposals. |
| [#13733](https://github.com/openai/codex/issues/13733) | Cost of repeated model-driven polling. |

The standalone issue is limited to discarded handle visibility.

## Alternatives considered

- Recover IDs from JavaScript output: unavailable after JavaScript discards the object.
- Append IDs to command output: mixes control metadata with program output and remains discardable.
- Encode creator identity in call IDs: turns an opaque identifier into an ownership API.
- Add another per-cell registry: duplicates existing manager bookkeeping.
- Report every session process: violates exact-cell attribution.
- Wait for or terminate matching processes: changes lifecycle policy.
- Add a JavaScript field or protocol event: expands compatibility scope and can still be discarded.
