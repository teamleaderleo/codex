# How code-mode completion can lose live session handles

This is the longer technical record behind the concise [issue](issue.md). I used an exploratory prototype to trace the data flow, test the narrow fix, and identify the decisions that still belong in the issue discussion.

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

This issue isolates a smaller invariant: a completing cell should retain access to its manager-owned nested commands after JavaScript discards their result objects. The focused approach wouldn't add a protocol field or choose a new continuation, cleanup, or wake-up policy.

## Exploratory prototype

The implementation and tests are together on one exploratory branch:

- [exploratory implementation and tests](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-ids)
- [base-to-head comparison](https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...77e7e3149df366236db2426596c23ebbe1d6bb48)
- [prototype head `77e7e314`](https://github.com/teamleaderleo/codex/commit/77e7e3149df366236db2426596c23ebbe1d6bb48)

There isn't a separate test branch that needs to be read alongside it. Historical validation commits and workflow runs are linked in [validation.md](validation.md) as evidence for specific checks, not as parallel proposed implementations.

## Production data flow

### 1. Preserve the existing creator identity

Nested dispatch already carries `ToolCallSource::CodeMode { cell_id, ... }`. A clean implementation can copy the protocol value with `cell_id.as_str().to_string()` and reconstruct the typed `CellId` at the unified-exec boundary.

Using `as_str()` makes the matching contract explicit and avoids coupling ownership to a `Display` implementation meant for presentation.

### 2. Store provenance with the manager-owned process

`UnifiedExecContext` carries the creator identity. `ProcessEntry` stores it beside the logical session ID and manager-owned process, and `store_process` copies it into the entry.

That provenance stays crate-internal. Public tool results, protocol events, and call-ID formats wouldn't change.

### 3. Query the existing liveness authority

A read-only manager query can select entries whose creator matches the exact `CellId`, filter them through existing `has_exited()` state, and return their logical session IDs.

Numeric ordering belongs in the formatter because it's a display contract. The exploratory prototype sorts in both the manager and formatter; a cleaned implementation only needs the formatter sort.

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

## Verified upstream status

The selected prototype base [`61a44880...`](https://github.com/openai/codex/commit/61a44880a85d2fd0d8770908dea5733495e571c8) is a direct ancestor of the verified upstream snapshot [`95637f70...`](https://github.com/openai/codex/commit/95637f7056835fea66bdd0044414af480fc0fd74), five commits behind it.

Those five commits change none of the four production files touched by the prototype. Upstream still carries the code-mode cell ID through `ToolCallSource::CodeMode` and still formats terminal responses without a unified-exec manager lookup.

The design therefore rebases cleanly onto that snapshot without adaptation.

## Review size

The exploratory comparison contains 903 changed lines, dominated by a 527-line acceptance module. The core change can be reviewed with a much smaller set:

- the production provenance and lookup change;
- focused manager and formatter tests;
- one primary end-to-end discarded-handle regression.

## Validation boundary

The focused tests and acceptance cases passed on the refs recorded in [validation.md](validation.md). Because those checks span closely related refs and workspaces, I treat them as prototype evidence rather than one final-SHA validation claim.

## Alternatives considered

- Recover IDs from JavaScript output: unavailable after JavaScript discards the object.
- Append IDs to command output: mixes control metadata with program output and remains discardable.
- Encode creator identity in call IDs: turns an opaque identifier into an ownership API.
- Add another per-cell registry: duplicates existing manager bookkeeping.
- Report every session process: violates exact-cell attribution.
- Wait for or terminate matching processes: changes lifecycle policy.
- Add a JavaScript field or protocol event: expands compatibility scope and can still be discarded.
