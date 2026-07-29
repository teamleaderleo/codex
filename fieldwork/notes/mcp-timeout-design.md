# Codex MCP tool timeout: design notes

Status: experiment in `teamleaderleo/codex#22`

Source pin: `openai/codex@5989dcc470695fc3f25a7eb3e90c014ef56d7d2a`
Dependency: `rmcp = 3.0.0`
Fieldwork candidate: `teamleaderleo/fieldwork#134`
Upstream contact: not authorized

## Required invariant

When Codex reports a tool timeout, the caller wait and the underlying MCP request must not silently diverge.

A complete design must answer four separate questions:

1. Did Codex stop waiting?
2. Was cancellation delivered to the server or request stream?
3. Did the server stop before committing an effect?
4. Is the result safe to retry, or is the outcome still ambiguous?

Cancellation delivery alone cannot prove that a side effect did not happen. A server may commit immediately before receiving cancellation.

## Use cases

### Read-only lookup

Examples: search, list, read, inspect.

Desired behavior:

- cancel promptly to free resources;
- a retry may be reasonable after transport recovery;
- late results should be discarded from the timed-out call;
- cache policy must not turn a late response into a successful retry result accidentally.

Risk if cancellation is absent: wasted work and responder retention, usually without external-state ambiguity.

### Potential mutation

Examples: send a message, create a ticket, deploy, charge, delete, upload, or change account state.

Desired behavior:

- attempt cancellation promptly;
- report the operation as outcome-unknown unless the protocol or tool provides a durable receipt;
- never automatically replay an accepted request;
- reconcile with an idempotency key, operation receipt, or follow-up read before retrying.

Risk if cancellation is absent: Codex reports failure, the server commits later, and a retry duplicates the effect.

### Tool call paused for user elicitation

Examples: payment confirmation, deployment approval, account selection, or destructive-action review.

Desired behavior:

- user decision time must not consume the tool execution deadline;
- cancellation must still occur when active tool time expires after the pause;
- cancelling the parent tool must also retire the associated elicitation request;
- a user response arriving after cancellation must not revive the tool.

Risk of a wall-clock SDK timeout: a valid call is cancelled while the user is reading or deciding.

### Concurrent tool calls

Desired behavior:

- cancel only the timed-out request;
- do not close the shared MCP transport unless it is independently known to be unusable;
- preserve unrelated response routing and subscriptions.

Risk of transport-wide shutdown: unrelated calls fail and accepted mutations become ambiguous together.

### Broken or saturated transport

Desired behavior:

- the timeout result itself remains bounded;
- cancellation delivery has a bounded grace period;
- failed or indeterminate cancellation is surfaced as outcome-unknown;
- pending ownership is eventually retired through request cancellation, late response, or transport teardown.

Risk of awaiting cancellation without a bound: a configured 40-second timeout can still hang forever while attempting to send the cancellation message.

### Modern 2026 request lifecycle

Desired behavior:

- distinguish stdio cancellation notification from per-request HTTP stream closure;
- do not equate a resumable stateful HTTP disconnect with cancellation;
- test legacy fallback independently from a successfully negotiated modern session;
- preserve MRTR/input-required rounds and their parent request association.

## Candidate approaches

### A. Keep the current outer Codex timeout

Mechanism: `active_time_timeout` drops the operation future.

Strengths:

- preserves active-time accounting;
- user elicitation pauses the deadline;
- shared implementation across operations.

Weaknesses:

- dropping a legacy `RequestHandle::await_response` future sends no MCP cancellation;
- the server can finish a mutation after Codex reports timeout;
- pending response ownership remains until a late response, explicit cancellation, or transport close.

Decision: insufficient on its own.

### B. Move the timeout into `PeerRequestOptions`

Mechanism: let `rmcp::RequestHandle::await_response` own the timeout.

Strengths:

- small patch;
- uses the SDK's existing cancellation path;
- cancellation send and pending-responder cleanup stay together;
- consistent SDK timeout error.

Weaknesses:

- wall-clock timeout includes user elicitation time;
- legacy fallback from a requested modern mode can accidentally acquire two competing deadlines;
- Codex loses its active-time policy unless the SDK gains an external pause signal.

Decision: useful control and acceptable for calls that cannot elicit; poor default for all tool calls.

### C. Keep the Codex active-time deadline and explicitly cancel the legacy handle

Mechanism: retain `RequestHandle`, await `handle.rx` under `active_time_timeout`, then call `handle.cancel()` on timeout.

Strengths:

- preserves elicitation pause behavior;
- sends request-scoped cancellation;
- avoids killing concurrent calls;
- follows the SDK's own subscription-handle pattern.

Weaknesses:

- adds a tool-specific operation path in Codex;
- awaiting `handle.cancel()` can exceed the configured timeout on a wedged transport;
- cancellation success does not prove a mutation did not commit;
- modern HTTP still needs a separate control.

Decision: strongest legacy candidate, subject to bounded cancellation-delivery tests.

### D. Cancel asynchronously after the active-time deadline

Mechanism: return the timeout promptly and move the owned `RequestHandle` into a bounded background cancellation task.

Strengths:

- caller timeout remains bounded;
- preserves active-time accounting;
- keeps request-scoped cancellation.

Weaknesses:

- cancellation may arrive after the caller sees the error;
- a background task may be lost during runtime shutdown;
- if cancellation delivery times out, the pending responder may remain until late response or transport teardown;
- requires telemetry and an outcome-unknown result state.

Decision: plausible production refinement of C, not yet coded.

### E. Close the whole MCP transport on timeout

Strengths:

- eventually retires all pending responders;
- useful when the transport is independently known to be dead.

Weaknesses:

- cancels unrelated calls;
- loses subscriptions and tool-catalog state;
- can turn several accepted mutations into ambiguous operations;
- forces reconnect or process respawn.

Decision: last-resort recovery action, not normal timeout handling.

### F. Add cancel-on-drop semantics to `rmcp::RequestHandle`

Strengths:

- outer callers become safer automatically;
- could remove Codex-specific request plumbing.

Weaknesses:

- `Drop` cannot await delivery;
- the SDK's internal `try_cancel_request` can fail when its channel is full;
- normal response paths must disarm the guard to avoid spurious cancellation;
- broad SDK behavior change requires upstream design agreement.

Decision: potential SDK campaign, outside the current no-upstream scope.

## Current experiment matrix

| Variant | Request cancellation | Mutation stopped | User elicitation pauses timeout | Caller return bounded on cancel-send stall |
| --- | --- | --- | --- | --- |
| Current Codex | no | no | yes | yes |
| SDK-native timeout | expected yes | expected yes | no | SDK-dependent |
| Pause-aware explicit cancel | expected yes | expected yes | yes | not yet; current patch awaits cancel |

## Recommended direction before production code

1. Keep Codex active-time accounting.
2. Own the request handle explicitly for legacy requests.
3. Give cancellation delivery a short bound and record whether it was confirmed.
4. Treat timed-out potential mutations as outcome-unknown even when cancellation was delivered.
5. Add an idempotency/receipt reconciliation path before automatic retry.
6. Implement modern stdio and modern Streamable HTTP controls separately.
7. Close the transport only when cancellation failure coincides with independent transport-health failure.
