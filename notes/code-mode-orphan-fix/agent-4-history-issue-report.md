# Agent 4 report: upstream history and issue draft

## Status

- Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
- Research date: 2026-07-26
- Publication status: private draft. No upstream issue, comment, or pull request has been published.
- Verified baseline regression: [`7298dcf44f61164ffc25b8bdf5f136281caeb9f5`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5)
- Verified acceptance head: [`89ffd99b81e872e3a961767e67fb8ec410df7eae`](https://github.com/teamleaderleo/codex/commit/89ffd99b81e872e3a961767e67fb8ec410df7eae)
- Canonical integrated head: [`4263facaf3c7d30b26cae33fd1e679278ac02105`](https://github.com/teamleaderleo/codex/commit/4263facaf3c7d30b26cae33fd1e679278ac02105)
- Publication gate: make the canonical branch green, complete final review, refresh related issues, and replace the remaining publication placeholders.

## Conclusion

This work supports a strong standalone issue once the remaining canonical-branch gate is met.

The bug is:

1. A code-mode JavaScript cell launches nested `tools.exec_command()` calls.
2. The commands cross `yield_time_ms`; unified exec stores each live process in the conversation-level process manager and returns a copied `session_id` handle to JavaScript.
3. JavaScript consumes only `.output`, projecting away both copied handles.
4. The JavaScript cell returns successfully.
5. The outer result says `Script completed` while the manager-owned processes remain alive.
6. The model-visible result contains no session IDs with which to poll, inspect, or terminate those processes.

Background-terminal persistence is intentional. The defect is loss of model-visible control information at a terminal outer-cell boundary.

## Confirmed ownership boundary

- **Code mode owns the nested callback task.** The cell actor tracks the callback while the nested tool call is being dispatched and awaited.
- **Unified exec transfers live-process ownership to the conversation-level process manager.** Once `UnifiedExecProcessManager::store_process` retains the process, ordinary cell or turn completion does not release it.
- **JavaScript receives only a copied logical session handle.** The returned object does not own the process.
- **Dropping or projecting away that handle has no lifecycle effect.** The process manager continues to own the live process.
- **The interface defect occurs at reporting time.** The outer cell reports terminal completion without restoring the control information that JavaScript omitted.

Patch 1 therefore changes visibility rather than termination or persistence.

## Evidence stages

### 1. Verified baseline reproduction

Commit: [`7298dcf44f61164ffc25b8bdf5f136281caeb9f5`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5)

Test: `code_mode_completion_does_not_surface_discarded_live_exec_sessions`

Environment: Linux aarch64 in a local Lima VM hosted on macOS. Private host usernames and log locations are omitted.

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

The negative regression confirms that JavaScript can discard two copied session IDs, the outer result can report `Script completed` without surfacing either ID, both manager-owned processes can remain alive, and panic-safe teardown removes all test processes.

### 2. Verified equivalent combined acceptance state

Implementation exercised: [`cea3f73d97897ca5ede37010cbd96addbabda6a5`](https://github.com/teamleaderleo/codex/commit/cea3f73d97897ca5ede37010cbd96addbabda6a5)

Acceptance head: [`89ffd99b81e872e3a961767e67fb8ec410df7eae`](https://github.com/teamleaderleo/codex/commit/89ffd99b81e872e3a961767e67fb8ec410df7eae)

The acceptance lineage preserves the clean negative proof and contains these ordered test commits:

1. `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
2. `528171c72c06d8be3471752322b7755a1eac3ac8`
3. `0ba57a73ea5895883a21aeb88e923d75a74ed38d`
4. `89ffd99b81e872e3a961767e67fb8ec410df7eae`

The completion-header assertion is corrected. It now independently requires:

1. `Script completed\n` at the start;
2. each actual surviving session ID exactly once and in numeric order; and
3. `\nWall time ` after the session-summary line.

Exact successful command:

```sh
RUST_MIN_STACK=8388608 \
CARGO_BUILD_JOBS=4 \
CARGO_INCREMENTAL=1 \
CARGO_PROFILE_TEST_DEBUG=0 \
CARGO_TARGET_DIR=/home/lima/.cache/codex-orphan-target \
RUST_BACKTRACE=1 \
cargo test -p codex-core \
  --test code_mode_orphan_sessions \
  -- --nocapture --test-threads=1
```

Verified equivalent combined result:

```text
test result: ok. 5 passed; 0 failed; 0 ignored
```

Harness-reported execution time: `16.37s`.

Verified coverage:

- both discarded surviving session IDs appear exactly once and in numeric order;
- an exited process is excluded while the one survivor is reported;
- large emitted output cannot truncate or displace the separately prepended session summary;
- an ordinary yielded cell remains completion-neutral;
- a two-cell case proves exact creator-cell isolation, so Cell A's process is not reported for Cell B; and
- panic-safe teardown leaves no registered background terminals.

The first combined run reached four passes and one failure because the large-output test over-specified the retained excerpt. Acceptance head `89ffd99b81e872e3a961767e67fb8ec410df7eae` corrected only that assertion, after which the complete five-test file passed.

### 3. Canonical integrated branch and remaining gate

Canonical branch: [`fix/code-mode-live-session-summary`](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-summary)

Integrated head: [`4263facaf3c7d30b26cae33fd1e679278ac02105`](https://github.com/teamleaderleo/codex/commit/4263facaf3c7d30b26cae33fd1e679278ac02105)

Its ancestry and tree preserve the verified work:

- first parent: typed-attribution implementation head `cea3f73d97897ca5ede37010cbd96addbabda6a5`;
- second parent: verified acceptance head `89ffd99b81e872e3a961767e67fb8ec410df7eae`;
- the original negative reproduction remains in acceptance ancestry;
- the corrected positive suite is present in the integrated tree; and
- the integrated production-and-test state matches the equivalent combined state exercised successfully by Agent 2.

The following remain open on the canonical branch:

- formatting and inspected diff: `<canonical-format-result>`;
- canonical compile or focused no-run result: `<canonical-compile-result>`;
- focused code-mode and unified-exec unit-test results: `<focused-unit-test-results>`;
- repeated five-test acceptance result from `4263facaf3c7d30b26cae33fd1e679278ac02105`: `<canonical-repeat-acceptance-result>`;
- final reviewed clean head or PR comparison: `<final-reviewed-head-or-pr-comparison>`;
- upstream issue link: `<issue-link>`; and
- pull-request link: `<pull-request-link>`.

Keep the issue unpublished until these are resolved and the final net-diff review confirms that Patch 1 contains no lifecycle-policy expansion.

## Recommended implementation contract

Patch 1 should:

1. preserve `ToolCallSource::CodeMode { cell_id, runtime_tool_call_id }` through `ExecCommandHandler` into unified-exec context;
2. store optional typed creator-cell attribution on the live process entry;
3. query the process manager for currently live processes whose creator cell exactly matches the terminal outer cell;
4. exclude exited processes and sort surviving logical session IDs numerically;
5. report those IDs in the untruncated outer status header for successful `Result`, failed `Result`, and explicit `Terminated` outcomes;
6. keep ordinary `Yielded` responses completion-neutral;
7. preserve the JavaScript `session_id` schema, opaque nested call IDs, and existing persistence policy; and
8. avoid a second liveness registry and avoid inferring ownership from JavaScript values or call-ID strings.

The earlier call-ID-prefix prototype remains feasibility evidence only. It proved that the response boundary can query the existing manager and place sorted IDs in the untruncated header, but prefix matching is not the ownership API.

Expected header shape:

```text
Script completed
Background sessions still running: 6306, 11236
Wall time 0.3 seconds
Output:
...
```

## Intended persistence history

- PR #8052 originally closed unified-exec sessions at turn completion.
- PR #10799 deliberately reversed that policy and preserved background terminals across ordinary turns.
- PR #14602 preserved background terminals on interrupt, moved cleanup toward explicit `/stop`, and stored a live process before the initial yield wait so interruption could not drop the last process reference.

The issue must not describe survival after cell or turn completion as the bug. The bug is that a surviving manager-owned process becomes invisible to the model after JavaScript discards its copied handle.

Direct exec already treats the live handle as essential state: `ExecCommandToolOutput::response_text` reports a running process and its session ID, while `ExecCommandToolOutput::code_mode_result` gives JavaScript a typed `session_id`. The outer terminal status is the last reliable place to restore control information that JavaScript omits.

## Related public issues and distinctions

Current private distinctions:

- **#34866:** similar outer-completed/inner-running symptom; this work adds deliberate handle projection, multiple manager-owned sessions, a verified contract test, and typed creator attribution.
- **#32411:** general loss of un-emitted nested results; this case loses control of independently manager-owned live processes.
- **#33816:** abandonment after a direct session was exposed; this case hides the handles before the model receives the outer result.
- **#14731:** proposes blocking turn completion; this proposal preserves persistence and changes terminal code-cell visibility only.
- **#15723:** parent wake-up after background completion; separate eventing and ownership concern.

Do **not** perform the final related-issue refresh yet. Re-fetch these issues, their recent discussions, and any newer duplicate or merged fix only after the canonical branch is green, so the research is current at publication time.

Separate findings involving delayed dispatch, shutdown races, remote bulk termination, stale bookkeeping, hidden-subagent policy, and macOS crash recovery remain outside Patch 1.

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

The shell commands are compact Unix examples. The regression and acceptance tests use bounded, panic-safe cleanup.

## Verified baseline reproduction

The baseline failure was reproduced by `code_mode_completion_does_not_surface_discarded_live_exec_sessions` at [`7298dcf44f61164ffc25b8bdf5f136281caeb9f5`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5).

It passed on Linux aarch64 in a local Lima VM hosted on macOS:

```text
test code_mode_completion_does_not_surface_discarded_live_exec_sessions ... ok

test result: ok. 1 passed; 0 failed; 0 ignored
```

The test confirms that two nested handles can be discarded, the outer response can claim completion without surfacing them, and both processes can remain alive in the conversation-level manager.

## Actual behaviour

```text
Script completed
Wall time ...
Output:
orphan-a|orphan-b
```

At that point, the manager still contains two distinct live sessions. Their IDs appear nowhere in the outer result because JavaScript projected them away.

## Expected behaviour

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
- `handle_runtime_response` reports terminal cell completion without summarising still-live processes created by that cell.
- The dispatch path already carries typed `ToolCallSource::CodeMode { cell_id, ... }` metadata, but baseline unified exec does not retain creator-cell attribution on the process entry.

## Implementation and acceptance evidence

Typed creator attribution is implemented in `cea3f73d97897ca5ede37010cbd96addbabda6a5`. Corrected acceptance coverage is preserved at `89ffd99b81e872e3a961767e67fb8ec410df7eae`. Canonical integrated head `4263facaf3c7d30b26cae33fd1e679278ac02105` merges those two histories and preserves the original negative reproduction in ancestry.

The equivalent combined state passed the complete focused acceptance file:

```sh
RUST_MIN_STACK=8388608 \
CARGO_BUILD_JOBS=4 \
CARGO_INCREMENTAL=1 \
CARGO_PROFILE_TEST_DEBUG=0 \
CARGO_TARGET_DIR=/home/lima/.cache/codex-orphan-target \
RUST_BACKTRACE=1 \
cargo test -p codex-core \
  --test code_mode_orphan_sessions \
  -- --nocapture --test-threads=1
```

```text
test result: ok. 5 passed; 0 failed; 0 ignored
```

The passing cases cover two sorted live IDs, one-survivor filtering, large-output truncation protection, yielded-cell neutrality, exact two-cell creator isolation, and panic-safe cleanup.

Before publication, add the canonical-branch validation record:

- formatting: `<canonical-format-result>`;
- compile or no-run: `<canonical-compile-result>`;
- focused unit tests: `<focused-unit-test-results>`;
- repeated acceptance: `<canonical-repeat-acceptance-result>`;
- final reviewed head or PR comparison: `<final-reviewed-head-or-pr-comparison>`;
- issue: `<issue-link>`; and
- PR: `<pull-request-link>`.

## Proposed narrow fix

1. Preserve typed `ToolCallSource::CodeMode` creator-cell metadata through unified exec.
2. Store optional creator-cell attribution on each live process entry.
3. On terminal cell outcomes, query for still-live processes created by that cell.
4. Exclude exited processes, sort surviving IDs, and append them to the untruncated status header.
5. Keep yielded-cell responses completion-neutral and preserve opaque nested call IDs.

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

- #34866: similar outer-completed/inner-running symptom; this report adds deliberate handle loss, multiple sessions, verified acceptance coverage, and typed creator attribution.
- #32411: general loss of un-emitted nested results; this case loses control of manager-owned live processes.
- #33816: abandonment after a direct session was exposed; this case hides the handles before the outer result reaches the model.
- #14731: proposes blocking turn completion; this proposal preserves persistence and changes visibility only.
- #15723: parent wake-up after background completion; separate eventing concern.

Refresh these descriptions only after the canonical branch is green and immediately before publication.

## Maintainer question

Does preserving typed creator-cell attribution on unified-exec process entries and surfacing surviving session IDs in terminal code-mode headers fit the intended ownership contract?

---

## Publication-order variants

Both variants require a green canonical branch, final net-diff review, current related-issue research, and stable issue/PR links. Do not choose yet.

### Variant A — issue immediately before the PR

1. Finish canonical validation and review.
2. Refresh related issues and duplicate search.
3. Publish the issue with stable tested links.
4. Open the PR immediately afterward and cross-link it.

Publication-specific line:

> A tested implementation is ready and will be submitted as a pull request immediately after this report.

### Variant B — issue linked alongside a draft PR

1. Finish canonical validation and review.
2. Prepare a draft PR without publishing it yet.
3. Refresh related issues and duplicate search.
4. Publish the issue and draft PR as one cross-linked pair.

Publication-specific line:

> A tested draft implementation and acceptance suite are available in `<pull-request-link>`.

## Final publication checklist

- [x] Baseline failure preserved and reproduced at `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`.
- [x] Baseline regression passed: `1 passed; 0 failed; 0 ignored`.
- [x] Typed creator-cell implementation prepared at `cea3f73d97897ca5ede37010cbd96addbabda6a5`.
- [x] Corrected acceptance head preserved at `89ffd99b81e872e3a961767e67fb8ec410df7eae`.
- [x] Header assertion allows the session summary between completion and wall time.
- [x] One-survivor timing is deterministic.
- [x] Large-output truncation coverage passes.
- [x] Yielded-cell behaviour remains completion-neutral.
- [x] Exact two-cell creator isolation is covered.
- [x] Complete acceptance file passed on the equivalent combined state: `5 passed; 0 failed; 0 ignored`.
- [x] Canonical integrated head `4263facaf3c7d30b26cae33fd1e679278ac02105` preserves implementation, corrected acceptance, and negative ancestry.
- [ ] Fill `<canonical-format-result>`.
- [ ] Fill `<canonical-compile-result>`.
- [ ] Fill `<focused-unit-test-results>`.
- [ ] Fill `<canonical-repeat-acceptance-result>`.
- [ ] Fill `<final-reviewed-head-or-pr-comparison>`.
- [ ] Confirm final net diff contains no lifecycle-policy expansion.
- [ ] After the canonical branch is green, refresh #34866, #32411, #33816, #14731, and #15723.
- [ ] After the canonical branch is green, search for newer duplicates or merged fixes.
- [ ] Choose publication Variant A or Variant B.
- [ ] Fill `<issue-link>` and `<pull-request-link>`.
- [ ] Remove every placeholder and verify that no private logs, usernames, prompts, tokens, or unrelated incident data are included.
- [ ] Perform a final word-count and clarity edit.

## Compact handoff

```text
Agent: 4 — history and upstream issue editor
Branch/ref: research/code-mode-orphan-handoffs
Baseline: 20dafe201d91d4405eef05ecd1db0257f13a9ac8
Changed files: notes/code-mode-orphan-fix/agent-4-history-issue-report.md
Tests run by Agent 4: none; documentation-only update
Verified evidence recorded: baseline negative 1/1 passed; equivalent combined acceptance 5/5 passed; corrected completion-header assertion; one-survivor, truncation, yielded, exact two-cell isolation, and panic-safe cleanup coverage
Canonical integrated head: 4263facaf3c7d30b26cae33fd1e679278ac02105, with implementation first parent cea3f73d97897ca5ede37010cbd96addbabda6a5 and acceptance second parent 89ffd99b81e872e3a961767e67fb8ec410df7eae; negative ancestry preserved
Remaining placeholders: <canonical-format-result>; <canonical-compile-result>; <focused-unit-test-results>; <canonical-repeat-acceptance-result>; <final-reviewed-head-or-pr-comparison>; <issue-link>; <pull-request-link>
Remaining unverified: canonical formatting and inspected diff; canonical compile/no-run; focused code-mode and unified-exec units; repeated five-test acceptance from canonical head; final reviewed clean head; final net-diff policy review
Deferred research: related-issue and duplicate refresh begins only after the canonical branch is green
Publication status: unpublished; Variant A and Variant B remain open
Recommended next action: Agent 1 completes canonical validation, Agent 3 reviews the green net diff, then Agent 4 fills placeholders, refreshes related issues, and performs the final publication edit
```
