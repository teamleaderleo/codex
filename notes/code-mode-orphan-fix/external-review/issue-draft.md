# Review-only upstream issue draft

> This is a review snapshot, not the final publication source. The final implementation link and validation wording will be refreshed after the test-only packaging revision.

## Proposed title

Code mode can report completion after discarding live nested exec session handles

## Summary

A code-mode JavaScript cell can finish with `Script completed` while nested `exec_command` processes remain alive and their session IDs have disappeared from the model-visible result.

The reproducible sequence is:

1. Start two nested `tools.exec_command()` calls with `Promise.all`.
2. Both commands cross `yield_time_ms`; unified exec stores the live processes and returns copied `session_id` values.
3. JavaScript reads only `.output`, discarding both IDs.
4. The JavaScript cell returns successfully.
5. The outer result says `Script completed`.
6. Both terminals remain live in the conversation-level process manager, but the model receives no ID with which to poll or terminate them.

Background-terminal persistence is intentional. The defect is loss of model-visible control information while the outer cell reports terminal completion.

## Minimal reproduction

```js
const outputs = (await Promise.all([
  tools.exec_command({
    cmd: "printf orphan-a; sleep 60",
    yield_time_ms: 250,
  }),
  tools.exec_command({
    cmd: "printf orphan-b; sleep 60",
    yield_time_ms: 250,
  }),
])).map(({ output }) => output);

text(outputs.join("|"));
```

## Actual behaviour

```text
Script completed
Wall time ...
Output:
orphan-a|orphan-b
```

The process manager still contains two distinct live sessions, but their IDs are absent because JavaScript projected them away.

## Expected behaviour

A terminal code-cell status should disclose the still-live nested sessions created by that cell:

```text
Script completed
Background sessions still running: 6306, 11236
Wall time ...
Output:
orphan-a|orphan-b
```

The sessions may continue running. The model retains the information needed to poll, inspect, or terminate them.

## Ownership and root cause

- Yielded nested processes are intentionally owned by the conversation-level unified-exec process manager.
- JavaScript receives copied logical handles and may discard them without affecting process lifetime.
- Creator-cell attribution is available at nested dispatch time but was not retained on stored process entries.
- Terminal code-cell rendering therefore could not recover the exact-cell live IDs after JavaScript discarded the copied handles.

## Tested narrow fix

Current clean production implementation:

- commit: `3778e1fae6e7e3d885252282a7c5ce67e06730ff`
- comparison: `61a44880a85d2fd0d8770908dea5733495e571c8...3778e1fae6e7e3d885252282a7c5ce67e06730ff`

The patch:

1. carries typed creator-cell attribution from nested code-mode routing through unified exec;
2. stores it on already-persisted live process entries;
3. queries exact-cell, still-live process IDs on terminal `Result` and `Terminated` responses;
4. excludes exited processes and sorts logical IDs deterministically;
5. prepends the IDs to the status header after emitted-output truncation;
6. keeps ordinary `Yielded` responses completion-neutral; and
7. preserves opaque nested call IDs, the JavaScript-visible result schema, and existing lifecycle policy.

## Validation

- Repository-native formatting and scoped fix passed on the clean candidate.
- Three focused code-mode unit tests passed.
- Three focused unified-exec tests passed.
- Five acceptance cases passed.
- Exact-file and architecture/API-conventions reviews passed for the production implementation.
- A matched broad `just test -p codex-core` run was red on both the candidate and exact upstream base because of baseline/environment failures.
- No persistent candidate-only failure remained after repeated focused differential runs.
- The broad project suite and complete workspace suite are not claimed green.
- A test-only revision is in progress to move the five acceptance cases into the existing aggregate integration-test structure and improve cleanup and determinism; it does not alter the production design.

## Non-goals

This patch does not:

- terminate background terminals;
- change persistence across turns or interrupts;
- change the JavaScript-visible nested result schema;
- block turn completion while a process remains live;
- wake an idle parent when a process or subagent completes;
- auto-surface arbitrary completed nested outputs or artifact handles; or
- change hidden-subagent, dispatch, shutdown, remote-termination, or recovery policy.

## Related issues

- #34866 is the closest symptom, but it already exposes an inner `session_id` and asks for clearer wrapper/process lifecycle semantics. This report covers deliberate handle loss, multiple live sessions, manager-state verification, and typed creator attribution.
- #32411 covers arbitrary awaited-but-unemitted nested results and artifact handles. This patch is limited to still-live manager-owned session IDs.
- #33816 covers model-side abandonment after a session ID was exposed. This case hides the IDs before the model receives the terminal result.
- #14731 proposes guarding turn completion while background work remains live. This patch preserves turn and process lifecycle policy.
- #15723 and #32188 cover event-driven wake-up after background completion. This patch reports live IDs at an existing terminal code-cell boundary and adds no wake-up mechanism.

## Maintainer question

Does retaining typed creator-cell attribution on unified-exec process entries and surfacing exact-cell surviving IDs in terminal code-mode headers fit the intended ownership and reporting contract?
