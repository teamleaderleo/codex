# Agent 4 report: upstream history and issue draft

## Status

- Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
- Research date: 2026-07-26
- Publication status: private draft. No upstream issue, comment, or pull request has been published.
- Verified baseline regression commit: [`7298dcf44f61164ffc25b8bdf5f136281caeb9f5`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5)
- Prepared typed-attribution head: [`cea3f73d97897ca5ede37010cbd96addbabda6a5`](https://github.com/teamleaderleo/codex/commit/cea3f73d97897ca5ede37010cbd96addbabda6a5)
- Prepared acceptance-test commit: [`528171c72c06d8be3471752322b7755a1eac3ac8`](https://github.com/teamleaderleo/codex/commit/528171c72c06d8be3471752322b7755a1eac3ac8)
- Agent 2 handoff note: [`1ae28a191a7885438abf15f61de273ab37551768`](https://github.com/teamleaderleo/codex/commit/1ae28a191a7885438abf15f61de273ab37551768)
- Publication gate: the corrected positive acceptance suite must pass against the integrated typed-attribution implementation, followed by final review and a current related-issue refresh.

## Conclusion

This work supports a strong standalone issue once the publication gate is met.

Several public reports touch adjacent symptoms, but none currently combines the same concise failure sequence, a verified executable reproduction, explicit ownership analysis, intended-persistence history, and a narrow typed-attribution implementation contract.

The bug is:

1. A code-mode JavaScript cell launches nested `tools.exec_command()` calls.
2. The commands cross `yield_time_ms`; unified exec stores each live process in the conversation-level process manager and returns a copied `session_id` handle to JavaScript.
3. JavaScript consumes only `.output`, projecting away both copied handles.
4. The JavaScript cell returns successfully.
5. The outer result says `Script completed` while the manager-owned processes remain alive.
6. The model-visible result contains no session IDs with which to poll, inspect, or terminate those processes.

Background-terminal persistence is intentional. The defect is loss of model-visible control information at a terminal outer-cell boundary.

## Confirmed ownership boundary

The ownership audit resolves an important ambiguity:

- **Code mode owns the nested callback task.** The cell actor tracks the callback while the nested tool call is being dispatched and awaited.
- **Unified exec transfers live-process ownership to the conversation-level process manager.** Once `UnifiedExecProcessManager::store_process` retains the process, ordinary cell or turn completion does not release it.
- **JavaScript receives only a copied logical session handle.** The returned object does not own the process.
- **Dropping or projecting away that handle has no lifecycle effect.** The process manager continues to own the live process.
- **The interface defect occurs at reporting time.** The outer cell reports terminal completion without restoring the control information that JavaScript omitted.

This is why Patch 1 should change visibility rather than termination or persistence.

## Three evidence stages

### 1. Verified baseline reproduction

Resolved commit: [`7298dcf44f61164ffc25b8bdf5f136281caeb9f5`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5)

Test: `code_mode_completion_does_not_surface_discarded_live_exec_sessions`

Environment: Linux aarch64 in a local Lima VM hosted on macOS. Private host usernames, log locations, and unrelated machine details are intentionally omitted.

Verified command:

```sh
RUST_MIN_STACK=8388608 \
CARGO_BUILD_JOBS=4 \
CARGO_INCREMENTAL=1 \
CARGO_PROFILE_TEST_DEBUG=0 \
CARGO_TARGET_DIR=/home/lima/.cache/codex-orphan-target \
RUST_BACKTRACE=1 \
cargo test -p codex-core \
  --test code_mode_orphan_sessions \
  code_mode_completion_does_not_surface_discarded_live_exec_sessions \
  -- --exact --nocapture
```

Verified result:

```text
test code_mode_completion_does_not_surface_discarded_live_exec_sessions ... ok

test result: ok. 1 passed; 0 failed; 0 ignored
```

The negative regression passed and confirms that:

- two nested long-running commands can cross `yield_time_ms` through `Promise.all`;
- JavaScript can destructure only `{ output }`, discarding both copied session IDs;
- the outer result can report `Script completed` without surfacing either ID;
- two distinct background terminals remain alive in the conversation-level process manager; and
- panic-safe teardown can terminate the remaining processes and verify that none remain.

This is verified executable evidence of the baseline interface failure, rather than an unrun test proposal.

### 2. Implementation and acceptance work under development

#### Prepared typed-attribution implementation

Branch: [`fix/code-mode-live-session-summary`](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-summary)

Reviewed head: [`cea3f73d97897ca5ede37010cbd96addbabda6a5`](https://github.com/teamleaderleo/codex/commit/cea3f73d97897ca5ede37010cbd96addbabda6a5)

This head is prepared and has received static review. It has **not** yet been formatted, compiled, or tested.

The prepared implementation:

1. converts `ToolCallSource::CodeMode` into optional typed `CellId` attribution in unified-exec context;
2. stores that attribution on each live `ProcessEntry`;
3. provides a liveness-filtered, exactly matched, numerically sorted process-ID query for the creator cell;
4. queries that method for terminal `Result` and `Terminated` outcomes;
5. keeps ordinary `Yielded` responses completion-neutral;
6. restores opaque nested tool-call IDs; and
7. preserves the JavaScript result schema and existing process-persistence policy.

Formatter-level unit tests are prepared for terminal success, failure, explicit termination, sorting, and yielded exclusion. Their runtime status remains unverified until the combined branch is compiled and tested.

#### Earlier feasibility prototype

Earlier prototype commit: [`cffcd8dca93ab5c2ff8fa1af262ae7676f5b97a9`](https://github.com/teamleaderleo/codex/commit/cffcd8dca93ab5c2ff8fa1af262ae7676f5b97a9)

That prototype proved that the outer runtime-response boundary can query the existing live-process manager, retain surviving processes, sort their logical IDs, and place the IDs in the untruncated status header without changing persistence or the JavaScript result schema.

Its call-ID-prefix mechanism remains **feasibility evidence only**. Encoding `CellId` into call IDs and recovering ownership with `starts_with` can collide, leaks unrestricted cell strings into identifiers and tracing, and turns a representation convention into an ownership API. The prepared typed-attribution head replaces that mechanism.

Expected header shape:

```text
Script completed
Background sessions still running: 6306, 11236
Wall time 0.3 seconds
Output:
...
```

#### Prepared acceptance work

Acceptance branch: [`research/code-mode-live-session-acceptance`](https://github.com/teamleaderleo/codex/tree/research/code-mode-live-session-acceptance)

- Preserved negative proof: [`7298dcf44f61164ffc25b8bdf5f136281caeb9f5`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5)
- Prepared acceptance commit: [`528171c72c06d8be3471752322b7755a1eac3ac8`](https://github.com/teamleaderleo/codex/commit/528171c72c06d8be3471752322b7755a1eac3ac8)
- Handoff note: [`1ae28a191a7885438abf15f61de273ab37551768`](https://github.com/teamleaderleo/codex/commit/1ae28a191a7885438abf15f61de273ab37551768)

Prepared acceptance coverage includes:

- two discarded live session IDs appearing exactly once and in numeric order;
- one nested process exiting before completion so only the survivor is reported;
- a large emitted payload that cannot truncate or displace the status-header warning;
- an ordinary yielded cell that receives no completion-oriented warning; and
- panic-safe cleanup for every case.

The acceptance work has not yet been run against the typed-attribution implementation.

**Required correction before integration:** the main positive test currently expects the header to begin with `Script completed\nWall time ...`. The selected contract inserts the live-session line between those lines. The corrected assertion should independently require:

1. `Script completed\n` at the start;
2. each actual live session ID exactly once and in numeric order; and
3. `\nWall time ` after the session line.

The one-survivor timing also needs deterministic treatment of the unified-exec minimum yield clamp. Exact creator-cell isolation must be covered either in the integration harness or with a focused manager-level test.

### Recommended implementation contract

Patch 1 should preserve existing typed source metadata through unified exec:

1. Preserve `ToolCallSource::CodeMode { cell_id, runtime_tool_call_id }` through `ExecCommandHandler` into unified-exec context.
2. Store optional typed creator-cell attribution on the live process entry.
3. Query the process manager for currently live processes whose creator cell matches the terminal outer cell.
4. Sort and report surviving logical session IDs in the outer status/header after output truncation.
5. Apply the summary to terminal outcomes: successful result, failed result, and explicit termination.
6. Keep ordinary `Yielded` responses completion-neutral because the outer cell is still active.
7. Preserve the JavaScript `session_id` schema and existing process-persistence policy.
8. Do not create a second liveness registry or infer ownership from emitted JavaScript values or call-ID text.
9. Preserve opaque nested tool-call IDs.

### 3. Publication gate

Keep the issue private until the corrected positive acceptance suite has been integrated with the typed-attribution implementation and has passed.

The final evidence pair should be:

- **Clean baseline regression commit:** [`7298dcf44f61164ffc25b8bdf5f136281caeb9f5`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5)
- **Final tested implementation and acceptance commit or PR:** `<tested-implementation-commit-or-pr>`
- **Positive test command:** `<positive-acceptance-test-command>`
- **Positive test result:** `<positive-acceptance-test-result>`

At publication time, link stable commits or a clean comparison/PR rather than relying on scratch-branch state. The issue can then serve as a concise design record:

**observed incident → six-step reproduction → verified baseline failure → ownership boundary → tested visibility patch**

## Intended persistence history

### Persistence across ordinary turns is deliberate

- PR #8052 originally closed unified-exec sessions at turn completion.
- PR #10799 deliberately reversed that policy and preserved background terminals across ordinary turns.
- PR #14602 preserved background terminals on interrupt, moved cleanup toward explicit `/stop`, and stored a live process before the initial yield wait so interruption could not drop the last process reference.

Therefore the issue should not claim that survival after cell or turn completion is itself erroneous. The bug is that the surviving manager-owned process becomes invisible to the model after its copied handle is discarded.

### Direct exec already treats the live handle as essential state

`ExecCommandToolOutput::response_text` tells the model when a direct exec process remains running and includes its session ID. `ExecCommandToolOutput::code_mode_result` likewise gives JavaScript a typed `session_id`.

Code mode loses that protection when JavaScript emits or retains only selected fields. The outer terminal status is the last reliable place to restore control information for still-live sessions created by that cell.

## Related public issues and distinctions

These are useful prior art and cross-links, not reasons to suppress a tested standalone report.

- **#34866:** similar outer-completed/inner-running symptom; this work adds deliberate handle projection, multiple manager-owned sessions, a verified contract test, and typed creator attribution.
- **#32411:** general loss of un-emitted nested results; this case loses control of independently manager-owned live processes.
- **#33816:** abandonment after a direct session was exposed; this case hides the handles before the model receives the outer result.
- **#14731:** proposes blocking turn completion; this proposal preserves persistence and changes terminal code-cell visibility only.
- **#15723:** parent wake-up after background completion; separate eventing and ownership concern.

Do **not** perform the final related-issue refresh yet. Re-fetch these issues, their recent discussion, and any newer duplicate or merged fix only after the positive suite passes, so the research is current at publication time.

Separate audit findings involving delayed dispatch, shutdown races, remote bulk termination, stale bookkeeping, hidden-subagent policy, and macOS crash recovery should receive their own tests and issue decisions.

---

# Unpublished upstream issue draft

**Title:** Code mode can report completion after discarding live nested exec session handles

## Executive summary

A code-mode JavaScript cell can finish with `Script completed` while nested `exec_command` processes remain alive and their session handles have disappeared from the model-visible result.

The reproduced sequence is:

1. Start two nested `tools.exec_command()` calls with `Promise.all`.
2. Both commands reach `yield_time_ms`; unified exec stores the live processes and returns copied `session_id` handles.
3. JavaScript reads only `.output`, discarding both copied IDs.
4. The JavaScript cell returns successfully.
5. The outer tool result says `Script completed`.
6. Both background terminals remain registered and running, but their IDs are absent from the model-visible result.

Cross-turn background-terminal persistence is intentional. The bug is loss of visibility and control while the outer cell reports terminal completion.

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

The shell commands are compact Unix examples. The verified regression uses bounded, panic-safe cleanup.

## Verified baseline reproduction

The baseline failure was reproduced by `code_mode_completion_does_not_surface_discarded_live_exec_sessions` at commit [`7298dcf44f61164ffc25b8bdf5f136281caeb9f5`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5).

It was run on Linux aarch64 in a local Lima VM hosted on macOS.

Command:

```sh
RUST_MIN_STACK=8388608 \
CARGO_BUILD_JOBS=4 \
CARGO_INCREMENTAL=1 \
CARGO_PROFILE_TEST_DEBUG=0 \
CARGO_TARGET_DIR=/home/lima/.cache/codex-orphan-target \
RUST_BACKTRACE=1 \
cargo test -p codex-core \
  --test code_mode_orphan_sessions \
  code_mode_completion_does_not_surface_discarded_live_exec_sessions \
  -- --exact --nocapture
```

Result:

```text
test code_mode_completion_does_not_surface_discarded_live_exec_sessions ... ok

test result: ok. 1 passed; 0 failed; 0 ignored
```

The passing negative regression confirms that two nested session IDs can be discarded, the outer response can claim completion without surfacing them, and both background terminals can remain alive in the process manager.

## Actual behaviour

The outer result begins with:

```text
Script completed
Wall time ...
Output:
orphan-a|orphan-b
```

At that point, the conversation-level process manager still contains two distinct live sessions. Their IDs appear nowhere in the outer result because JavaScript projected them away.

## Expected behaviour

A terminal outer-cell status should disclose currently live nested unified-exec sessions created by that cell:

```text
Script completed
Background sessions still running: 6306, 11236
Wall time ...
Output:
orphan-a|orphan-b
```

The processes may continue running. The agent retains the information needed to poll, inspect, or terminate them.

## Ownership and root cause

High confidence:

- Code mode owns each nested callback task while dispatching the nested tool call.
- After unified exec stores a yielded process, the conversation-level process manager owns it.
- JavaScript receives only a copied logical session handle; dropping the returned object does not affect the process.
- `ExecCommandToolOutput::code_mode_result` supplies the copied `session_id` to JavaScript.
- JavaScript may retain or emit only selected fields.
- `handle_runtime_response` reports `Script completed` from a successful terminal `RuntimeResponse::Result` without summarising still-live processes created by that cell.

The dispatch path already carries typed `ToolCallSource::CodeMode { cell_id, ... }` metadata, but baseline unified exec does not retain the creator cell on the live process entry.

## Implementation evidence and proposed narrow fix

A typed-attribution implementation has been prepared and statically reviewed at [`cea3f73d97897ca5ede37010cbd96addbabda6a5`](https://github.com/teamleaderleo/codex/commit/cea3f73d97897ca5ede37010cbd96addbabda6a5). It has not yet been compiled or tested.

Prepared acceptance coverage exists at [`528171c72c06d8be3471752322b7755a1eac3ac8`](https://github.com/teamleaderleo/codex/commit/528171c72c06d8be3471752322b7755a1eac3ac8), based on the preserved negative proof. The main completion-header assertion requires correction before integration, and the suite has not yet run against the implementation.

An earlier call-ID-prefix prototype proved that the outer response can query the existing live-process manager, sort surviving IDs, and place them in the untruncated status header without changing persistence or the JavaScript result schema. Prefix matching is feasibility evidence only and is not the proposed ownership API.

The recommended implementation is:

1. Preserve typed `ToolCallSource::CodeMode` creator-cell metadata through unified exec.
2. Store optional creator-cell attribution on each live process entry.
3. On terminal cell outcomes, query for still-live processes created by that cell.
4. Sort and append their logical session IDs to the untruncated outer status header.
5. Keep yielded-cell responses completion-neutral and preserve opaque nested call IDs.

Final implementation evidence:

- Implementation commit or PR: `<tested-implementation-commit-or-pr>`
- Positive acceptance test command: `<positive-acceptance-test-command>`
- Positive acceptance test result: `<positive-acceptance-test-result>`

### Non-goals

This change does not:

- terminate background terminals;
- change persistence across turns or interrupts;
- change the JavaScript-visible nested result schema;
- report a completion warning on an ordinary yielded outer cell;
- define hidden-subagent ownership or completion policy;
- fix delayed dispatch, shutdown races, remote termination, or stale bookkeeping; or
- solve macOS recovery after abrupt runtime death.

## Related issues

- #34866: similar outer-completed/inner-running symptom; this report adds deliberate handle loss, multiple sessions, a verified contract test, and typed creator attribution.
- #32411: general loss of un-emitted nested results; this case loses control of manager-owned live processes.
- #33816: abandonment after a direct session was exposed; this case hides the handles before the outer result reaches the model.
- #14731: proposes blocking turn completion; this proposal preserves persistence and changes visibility only.
- #15723: parent wake-up after background completion; separate eventing concern.

These issue descriptions must be refreshed after the positive suite passes and immediately before publication.

## Maintainer question

Does preserving typed creator-cell attribution on unified-exec process entries and surfacing surviving session IDs in terminal code-mode headers fit the intended ownership contract?

---

## Publication-order variants

Both variants use the same issue body above and require the same completed evidence gate. Do not choose between them until the positive suite and final net-diff review pass.

### Variant A — issue immediately before the PR

1. Complete the positive suite and final review.
2. Refresh related issues and duplicate search.
3. Publish the issue with stable tested commit links.
4. Open the PR immediately afterward and link the issue in the PR body.
5. Add the PR link to the issue if useful.

Advantages: the issue provides a clean problem statement and design record before code review begins. Risk: even a short delay between issue and PR can leave the report temporarily without the code-review link.

Publication-specific line for the issue:

> A tested implementation is ready and will be submitted as a pull request immediately after this report.

### Variant B — issue linked alongside a draft PR

1. Complete the positive suite and final review.
2. Prepare a draft PR without publishing it yet.
3. Refresh related issues and duplicate search.
4. Publish the issue and draft PR as one coordinated pair, cross-linking both.
5. Keep the PR in draft until maintainer feedback and CI status are clear.

Advantages: maintainers can inspect the reproduction, implementation, and tests together. Risk: the issue may read as more implementation-led unless the executive summary remains firmly problem-first.

Publication-specific line for the issue:

> A tested draft implementation and acceptance suite are available in `<draft-pr-link>`.

## Final publication checklist

- [x] Baseline failure reproduced by an executable regression test.
- [x] Baseline regression resolved to commit `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`.
- [x] Baseline regression passed: `1 passed; 0 failed; 0 ignored`.
- [x] Exact baseline test command recorded.
- [x] Test environment described as Linux aarch64 in a Lima VM hosted on macOS.
- [x] Typed creator-cell implementation prepared at `cea3f73d97897ca5ede37010cbd96addbabda6a5`.
- [x] Positive acceptance work prepared at `528171c72c06d8be3471752322b7755a1eac3ac8`.
- [x] Agent 2 handoff recorded at `1ae28a191a7885438abf15f61de273ab37551768`.
- [ ] Correct the positive completion-header assertion.
- [ ] Integrate the preserved negative lineage and corrected positive acceptance work with the typed-attribution implementation.
- [ ] Add or confirm exact creator-cell isolation coverage.
- [ ] Format and inspect the net diff.
- [ ] Compile the integrated implementation.
- [ ] Run relevant code-mode and unified-exec unit tests.
- [ ] Run the complete positive acceptance file with panic-safe teardown.
- [ ] Confirm the one-survivor and truncation cases pass deterministically.
- [ ] Confirm terminal success, failure, and explicit-termination behaviour.
- [ ] Confirm ordinary `Yielded` responses remain completion-neutral.
- [ ] Record the final tested implementation commit or PR.
- [ ] Record the exact positive test command.
- [ ] Record the positive test result.
- [ ] Obtain final review of the combined net diff and confirm no lifecycle-policy expansion.
- [ ] After the positive suite passes, re-check #34866, #32411, #33816, #14731, and #15723, including recent discussion.
- [ ] After the positive suite passes, search for newer duplicates or merged fixes.
- [ ] Replace remaining scratch-branch references where stable tested links are available.
- [ ] Choose publication Variant A or Variant B.
- [ ] Remove every placeholder and verify that no private logs, usernames, prompts, tokens, or unrelated incident data are included.
- [ ] Perform a final word-count and clarity edit.

## Compact handoff

```text
Agent: 4 — history and upstream issue editor
Branch/ref: research/code-mode-orphan-handoffs
Baseline: 20dafe201d91d4405eef05ecd1db0257f13a9ac8
Changed files: notes/code-mode-orphan-fix/agent-4-history-issue-report.md
Tests run and results: Agent 4 ran no tests; verified baseline negative regression remains 1 passed, 0 failed, 0 ignored on Linux aarch64 in a Lima VM hosted on macOS
Recorded prepared evidence: typed-attribution head cea3f73d97897ca5ede37010cbd96addbabda6a5 is statically reviewed but uncompiled and untested; acceptance commit 528171c72c06d8be3471752322b7755a1eac3ac8 and handoff 1ae28a191a7885438abf15f61de273ab37551768 are prepared but not run against the implementation
Required correction: positive completion-header assertion must allow the live-session line between Script completed and Wall time
Remaining placeholders: <tested-implementation-commit-or-pr>; <positive-acceptance-test-command>; <positive-acceptance-test-result>; <draft-pr-link> in Variant B if selected
Remaining unverified evidence: exact creator-cell isolation; integrated formatting and compilation; unit-test results; full positive acceptance results; deterministic one-survivor and truncation results; terminal failure and explicit-termination behaviour; yielded neutrality; panic-safe final cleanup; final net-diff review
Deferred research: related-issue and duplicate refresh must wait until the positive suite passes
Publication decision still open: Variant A — issue immediately before PR; Variant B — issue linked alongside a draft PR
Recommended next action: Agent 2 corrects the acceptance assertion, Agent 1 integrates and runs the combined suite, Agent 3 reviews the tested net diff, then Agent 4 fills all placeholders and refreshes related issues
```