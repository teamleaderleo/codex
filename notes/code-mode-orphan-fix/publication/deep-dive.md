# How code-mode completion can lose live session handles

This document records the technical reasoning behind the concise [issue](issue.md).

## Failure

A code-mode JavaScript cell can start nested commands and retain only each result's `.output`:

```js
const outputs = (await Promise.all([
  tools.exec_command({ cmd: "printf orphan-a; sleep 60", yield_time_ms: 250 }),
  tools.exec_command({ cmd: "printf orphan-b; sleep 60", yield_time_ms: 250 }),
])).map(({ output }) => output);

text(outputs.join("|"));
```

The copied JavaScript values carry no process ownership. The session-level unified-exec manager retains the yielded processes, while the final code-mode result has no cell-scoped path to identify and recover the discarded session IDs.

The [negative reproduction](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5) preserves that before-state as an executable test.

## Why a separate issue

[#34866](https://github.com/openai/codex/issues/34866) covers the broader mismatch between wrapper completion and nested-process state and proposes richer lifecycle representation.

This issue targets a smaller invariant: a completing cell should retain access to its manager-owned nested commands after JavaScript discards their result objects. The focused approach adds no protocol field and chooses no new continuation or cleanup policy.

## Production data flow

### 1. Preserve existing creator identity

Nested dispatch already carries `ToolCallSource::CodeMode { cell_id, ... }`. A clean implementation can copy the source string explicitly with `cell_id.as_str().to_string()` and reconstruct the typed `CellId` at the unified-exec boundary.

Using `as_str()` documents that matching depends on the protocol value and avoids coupling ownership to a `Display` implementation intended for presentation.

### 2. Store provenance with the manager-owned process

`UnifiedExecContext` carries the creator identity. `ProcessEntry` stores it beside the logical session ID and the manager-owned process. `store_process` copies the value into the entry.

This remains crate-internal provenance. Public tool results, protocol events, and call-ID formats stay unchanged.

### 3. Query the existing liveness authority

A read-only manager query selects entries whose creator matches the exact `CellId`, filters through existing `has_exited()` state, and returns logical session IDs.

Ordering belongs to the formatter because numeric order is a display contract. The prototype currently sorts in both the manager and formatter; a cleaned implementation can remove the manager sort.

### 4. Report only on selected terminal outcomes

Ordinary `RuntimeResponse::Yielded` responses describe a cell that remains active and resumable, so they retain their existing status.

The unresolved boundary is whether live IDs appear on:

- successful `Result` only;
- successful and failed `Result`; or
- every terminal response, including `Terminated`.

### 5. Keep status outside emitted-output truncation

Code-mode emitted payload is truncated before the status header is prepended. A large emitted value therefore cannot remove the live-session line at that boundary. Later whole-conversation limits continue to apply to the complete tool result.

## Liveness semantics

The query describes manager-observed state at one instant. A selected process can exit immediately after lookup.

`UnifiedExecProcess::has_exited()` has an important backend asymmetry:

- local processes consult cached state and the live local handle;
- exec-server-backed processes consult cached manager state.

A recently exited remote process may therefore appear until its exit is reflected in manager state. The public issue names this boundary so it can be weighed against the broader lifecycle representation in #34866.

## Exact-cell contract

Reporting every live process in the session would let one completing cell claim another cell's unrelated work.

The contract is:

> Report only manager-owned processes attributed to the exact cell whose terminal result is being formatted.

## Display contract

The prototype formats IDs in numeric order and applies a model-visible bound. The issue intentionally leaves the exact wording and bound open.

Internal manager capacity and model-visible output policy serve different purposes and should remain independent values if a bound is retained.

## Verified upstream status

The selected prototype base [`61a44880...`](https://github.com/openai/codex/commit/61a44880a85d2fd0d8770908dea5733495e571c8) is a direct ancestor of verified upstream snapshot [`95637f70...`](https://github.com/openai/codex/commit/95637f7056835fea66bdd0044414af480fc0fd74), five commits behind it.

Those five commits change none of the four production files touched by this fix. Upstream still carries the code-mode cell ID through `ToolCallSource::CodeMode` and still formats terminal responses without a unified-exec manager lookup.

The design therefore rebases cleanly onto that snapshot without adaptation.

## Review size

The prototype comparison contains 903 changed lines, dominated by a 527-line acceptance module. A reviewable implementation can be limited to:

- the small production change;
- focused manager and formatter tests;
- one primary end-to-end discarded-handle regression.

## Prototype validation boundary

Historical focused tests and acceptance cases passed on the refs recorded in [validation.md](validation.md). Those runs establish prototype feasibility.

Because they span closely related refs and workspaces, they are prototype evidence rather than a single-SHA validation claim.

## Alternatives considered

- Recover IDs from JavaScript output: unavailable after JavaScript discards the object.
- Append IDs to command output: mixes control metadata with program output and remains discardable.
- Encode creator identity in call IDs: turns an opaque identifier into an ownership API.
- Add another per-cell registry: duplicates existing manager bookkeeping.
- Report every session process: violates exact-cell attribution.
- Wait for or terminate matching processes: changes lifecycle policy.
- Add a JavaScript field or protocol event: expands compatibility scope and can still be discarded.