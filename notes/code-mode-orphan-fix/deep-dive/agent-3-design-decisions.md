# Agent 3 design decisions: why Patch 1 is visibility-only

Status: internal engineering decision record. This document explains the selected contract, the alternatives considered, and the evidence required to reopen deferred paths. It is not part of the clean upstream candidate.

Reviewed refs:

- upstream base: `61a44880a85d2fd0d8770908dea5733495e571c8`
- final clean candidate: `760216784efaee1ba6a3b1250349f31d5f91c7ca`

## Decision summary

Patch 1 preserves existing background-process lifetime and restores model-visible control information at the point where a code-mode cell reaches a terminal result.

The selected design:

1. reads existing typed code-mode cell identity from `ToolCallSource::CodeMode`;
2. carries it through `UnifiedExecContext`;
3. stores it on the existing manager-owned `ProcessEntry`;
4. queries the existing process manager for exact-cell, live-only process IDs;
5. reports those IDs only on terminal `Result` or `Terminated` code-mode responses;
6. leaves ordinary `Yielded` responses unchanged;
7. changes no JavaScript result schema, public protocol, nested call-ID format, process lifetime, pruning, shutdown, recovery, or termination policy.

The patch is deliberately narrower than the original operational symptom. The incident involved long-lived resource-consuming child processes, but source and history review showed that persistence was intentional. The actionable defect for Patch 1 was that the model-visible terminal result could lose the only copied session IDs while the manager continued to own the processes.[^diagnosis]

## Engineering principles used

### Preserve the existing source of truth

The unified-exec process manager already owns the stored process handles and already defines liveness. Patch 1 must query it rather than create a second registry or infer state from JavaScript output.

### Preserve typed provenance

The invocation already carries typed code-mode cell identity. Patch 1 should retain that value rather than encode ownership in strings or reconstruct it later.

### Separate visibility from lifecycle policy

Showing a live session ID is an information-flow correction. Killing a process, blocking cell completion, waking a parent, or sweeping stale processes is a product/lifecycle decision. Those must not be smuggled into the same patch.

### Make the smallest outside-contributor change that is reviewable

The patch should use existing fields, managers, handlers, and response boundaries. It should not establish a new public abstraction merely because a more general design can be imagined.

### Test independent invariants

The behavioural contract is not one snapshot string. It is a set of independent properties: exact ownership, current liveness, deterministic ordering, terminal-only reporting, truncation placement, and schema/lifecycle non-change. Agent 2's test archaeology shows how several over-specific assertions were replaced with those invariants.[^testing]

## Decision 1: store creator-cell attribution on `ProcessEntry`

### Chosen

Capture the existing `ToolCallSource::CodeMode` cell ID in `ExecCommandHandler`, carry it in `UnifiedExecContext`, and copy it into the stored process entry.

### Why

- the handler already receives typed provenance;
- the invocation context already carries metadata to process creation;
- the manager-owned entry is the durable place associated with the live process;
- JavaScript can discard its copied result without affecting manager state;
- exact typed equality avoids representation assumptions.

### Rejected alternative: infer ownership from JavaScript output

JavaScript may deliberately keep only `.output` or discard the full result. The confirmed failure exists precisely because the relevant value is absent from retained output.

### Rejected alternative: append the ID to nested `.output`

Changing `.output` would mix control metadata with command output and still depend on JavaScript preserving or emitting that field. It would also alter an established nested result contract without solving full-result discard.

### Rejected alternative: encode the cell ID into nested call IDs

A feasibility prototype proved that prefix-based filtering could expose the sessions, but it would make a naming convention an ownership API. Risks include collisions, leaking cell identity into logs/tracing, and coupling ownership to opaque identifier formatting. The accepted contract keeps nested call IDs opaque.[^callid]

### Reopen only if

A future design intentionally standardises a typed, public process-origin model across multiple tool sources. That work should define variants, serialization boundaries, migration, privacy, and lifecycle semantics rather than replacing `Option<CellId>` opportunistically.

## Decision 2: keep the process manager as the liveness authority

### Chosen

Add a read-only manager query that filters exact creator-cell matches and excludes exited processes.

### Why

- the manager owns the process handles;
- `has_exited()` is the existing current-liveness check;
- no state duplication is introduced;
- no lifecycle mutation occurs;
- the result can be tested independently.

### Rejected alternative: maintain a second per-cell registry in code mode

A second registry would need its own insertion, exit, pruning, shutdown, recovery, and race handling. It could disagree with the actual manager store. The defect does not justify another liveness system.

### Rejected alternative: list every live session in the current Codex session

That would reveal the symptom but violate ownership isolation. A completing cell must not disclose processes created by another cell. The two-cell acceptance case exists specifically to prevent this shortcut.

### Rejected alternative: trust stale stored attribution without checking liveness

Creator attribution alone would report processes that already exited. The one-survivor acceptance case and direct manager unit test require both creator match and current liveness.

### Reopen only if

The process manager's ownership model changes, or a separate authoritative lifecycle service replaces it. Any replacement must provide exact creator attribution and current liveness without weaker isolation.

## Decision 3: report only at terminal code-cell boundaries

### Chosen

Perform the manager lookup for `RuntimeResponse::Result` and `RuntimeResponse::Terminated`. Return no completion-only session summary for `RuntimeResponse::Yielded`.

### Why

The loss occurs when a cell becomes terminal and its nested copied results no longer have another opportunity to reach the model. `Yielded` means the cell is still active and already has a resumable cell ID. Adding terminal-style language there would blur completion semantics.

### Rejected alternative: always report live nested sessions on every response

That would add noisy repeated state to intermediate yields and could suggest the cell completed or abandoned those sessions when it had not.

### Rejected alternative: wait for all nested sessions before publishing terminal completion

That changes lifecycle policy. Long-running servers, watchers, and interactive terminals are intended to persist. Blocking completion would turn background work into foreground work and could hang code cells indefinitely.

### Rejected alternative: terminate matching sessions automatically

Automatic cleanup would destroy intentional background work and make the selected visibility fix inseparable from a product policy change.

### Reopen only if

Product owners decide that hidden or background work must block completion, be auto-terminated, or trigger a separate lifecycle event. That requires an explicit ownership contract and separate acceptance tests.

## Decision 4: put the summary in the outer status header

### Chosen

Append the live-session line to the existing terminal status, after code-mode emitted output has been truncated and before the header is prepended to the final result.

### Why

- the outer result is the boundary that currently says `Script completed`;
- it is visible even if JavaScript discarded the nested result object;
- placing it after emitted-output truncation prevents a large payload from displacing it at that boundary;
- existing status lines remain unchanged;
- no JavaScript result schema changes.

### Rejected alternative: add a new JavaScript field

The existing nested schema already includes `session_id`. The failure is not lack of a field; it is that JavaScript can discard the returned object. A new field would have the same retention problem and create compatibility work.

### Rejected alternative: create a new protocol event

A new app-server or public protocol event would broaden the patch, require client handling, and introduce ordering and compatibility questions. The model-facing status already has the needed delivery path.

### Rejected alternative: emit a synthetic nested tool result after completion

That would complicate call/result accounting and potentially expose or invent call IDs. The existing terminal status can carry the minimal information without changing tool-call protocol.

### Reopen only if

Maintainers decide live-session state should become a first-class structured protocol item consumed by multiple clients. That should be a separate API design with schema versioning and UI requirements.

## Decision 5: show the complete matching point-in-time list

### Chosen

Render every exact-cell, still-live logical session ID returned by the manager at the time of terminal response formatting.

### Why

The purpose is to preserve control handles. A separate display cap would intentionally hide some handles and weaken the guarantee. Normal manager limits constrain the common case, and the complete result remains subject to later global history limits.

### Considered alternative: cap the displayed IDs and add an omitted count

This would provide a hard output bound but leave some sessions inaccessible from the displayed terminal result. It could be reasonable if the manager store becomes large enough to threaten response safety, but no evidence showed that the normal matching set creates a practical issue.

### Reopen only if

A demonstrated large-cardinality case causes response-size or history-management problems. A future cap should define how omitted handles remain discoverable through another model-visible API.

## Decision 6: keep `Option<CellId>` rather than add a general origin enum

### Chosen

Use `Option<CellId>` in the crate-private unified-exec context and process entry.

### Why

The current required distinction is exact and binary: code-mode creator known versus no code-mode creator. The existing call source already maps naturally to that representation.

### Considered alternative: `ProcessOrigin` or `ToolCallSource` on every process entry

A general enum could support direct calls, code mode, subagents, MCP, remote sources, or future origins. It would also establish a broader internal contract, invite lifecycle policy by origin, and require decisions outside Patch 1.

### Non-blocking caveat

`Option` parameters can be less expressive than explicit methods or variants. The current builder call uses a named variable and remains crate-private, so the ambiguity is limited.

### Reopen only if

At least one additional origin-specific behaviour is accepted and tested, or maintainers request a general origin model during review.

## Decision 7: keep duplicate sorting for now

### Chosen

The manager returns sorted IDs, and the formatter also sorts its input.

### Why

The manager contract is deterministic. The formatter is also deterministic if called from another test or future path with unsorted input. The extra integer sort is negligible at expected cardinalities.

### Alternative

Remove the formatter sort and rely on manager ordering. This is a valid cleanup but not necessary for correctness.

### Reopen only if

Maintainers prefer a single ordering owner or profiling identifies the redundant sort as meaningful.

## Decision 8: preserve existing process persistence

### Chosen

Do not alter cross-turn persistence, interrupt behaviour, `/stop`, pruning, shutdown, or process-group handling.

### Why

Upstream history treats background terminals as intentional reusable resources. The original incident included abrupt owner loss and long-lived macOS processes, but Patch 1's executable reproduction does not require or solve that recovery path.

### Deferred family: hidden/subagent cleanup policy

Questions such as whether a hidden subagent may complete while yielded work remains are product-policy questions. They need an ownership statement and their own reproduction.

### Deferred family: macOS/runtime-loss recovery

Safe reclamation after application or runtime loss requires durable owner identity, OS PID or process-group tracking, reuse protection, crash semantics, and platform-specific termination confirmation. Restoring logical session IDs during a live session is not sufficient.

### Deferred family: event-driven wake-up

Notifying a parent or model when a process exits could improve lifecycle management, but it does not replace the need to preserve handles at terminal completion.

## Decision 9: use the repository's aggregate integration suite

### Chosen

Move the five acceptance cases under `tests/suite/code_mode/orphan_sessions.rs` and register them from the existing `code_mode` module.

### Why

The repository explicitly documents one aggregate integration-test binary. The existing code-mode module already provides relevant response and turn helpers. The final shape reduces duplicate code and avoids another integration binary.

### Rejected alternative: retain a standalone target for easier focused execution

Nextest expression filtering already supports focused child-module runs inside the aggregate binary. The convenience did not justify violating the documented suite shape or duplicating helpers.

### Rejected alternative: place all cases directly into the large parent file

A child module preserves the aggregate convention without adding roughly five hundred lines to an already large file.

## Decision 10: test state transitions, not elapsed time

### Chosen

Replace the one-survivor fixed sleeps with a PID/filesystem release-and-poll handshake.

### Why

The contract is “one process has exited before the cell completes”, not “two seconds elapsed”. The final handshake is causal, bounded, and diagnosable.

### Rejected alternative: increase sleep durations

Longer sleeps reduce but do not remove scheduler races and make successful tests slower.

## Decision 11: avoid over-specific output assertions

### Chosen

Assert the named warning, exact IDs, separation from emitted output, and non-empty remaining output. Do not require exactly two content items or one specific truncation excerpt.

### Why

The product contract concerns information and placement, not one internal serialisation cardinality. Tests should fail on user-visible regressions rather than harmless representational changes.

## Decision 12: use bounded validation claims

### Chosen

Public claims state:

- four focused unit tests passed;
- five aggregate acceptance cases passed;
- two compatibility tests passed 20/20 executions on candidate and 20/20 on exact base;
- the matched broad `codex-core` suite was red on both refs and is not claimed green;
- the complete workspace suite was not run.

### Why

The evidence is strong in the changed area but not universal. The broad differential showed no persistent candidate-only failure, while environment and baseline failures remained. Repetition reduces concern about a frequent race but does not prove impossibility.

## Security and privacy judgement

This patch is not automatically a security fix.

It may reduce operational risk by restoring control handles for live processes that can consume CPU, memory, sockets, file descriptors, locks, descendants, or filesystem state. But the current evidence does not establish privilege escalation, sandbox escape, cross-user disclosure, or attacker-controlled persistence.

Information exposure remains narrow:

- only current-session manager state;
- only exact creator-cell matches;
- only still-live logical numeric IDs;
- no commands, output, environment, paths, OS PIDs, or other-cell IDs.

Raw private logs and chat transcripts are not required to review the production patch. Scrubbed chronology and executable tests replace most of that evidentiary burden.

## External-contributor posture

The selected patch is appropriate for an outside contributor because it avoids claiming ownership of product policy.

It says, in effect:

> The system already knows the creator cell, already owns the live process, and already has a terminal status boundary. Preserve the missing association and disclose the existing control IDs there.

It does not say:

> Redesign process origin, change persistence, invent a protocol, or decide when users' background work should be killed.

That restraint lowers review cost and gives maintainers clear room to accept, adjust, or extend the design.

## What would make this decision record obsolete

Revisit the design if any of these becomes true:

- code mode no longer carries stable typed cell IDs;
- unified exec no longer owns the authoritative process store;
- session IDs cease to be the model-visible control handle;
- terminal result formatting moves to a structured protocol layer;
- a general process-origin model is adopted upstream;
- product policy changes to auto-terminate or block on background work;
- a demonstrated cardinality problem requires capped display plus another discovery API;
- cross-platform recovery becomes part of the same accepted contract.

Until then, the final candidate is the smallest design that directly addresses the reproduced information-loss defect.

## Footnotes and sources

[^diagnosis]: [`agent-1-investigation-reconstruction.md`](agent-1-investigation-reconstruction.md), “The point at which the diagnosis narrowed” and “Evidence that changed the diagnosis”.
[^testing]: [`agent-2-test-validation-archaeology.md`](agent-2-test-validation-archaeology.md), especially sections 6-14.
[^callid]: Rejected feasibility prototype [`cffcd8dca93ab5c2ff8fa1af262ae7676f5b97a9`](https://github.com/teamleaderleo/codex/commit/cffcd8dca93ab5c2ff8fa1af262ae7676f5b97a9); see Agent 1's “Discarded hypotheses”.
