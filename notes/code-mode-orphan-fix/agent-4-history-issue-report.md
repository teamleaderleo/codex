# Agent 4 report: upstream history and issue draft

## Status

- Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
- Research date: 2026-07-26
- Publication status: private draft. No upstream issue, comment, or pull request has been published.
- Verified baseline regression: [`7298dcf44f61164ffc25b8bdf5f136281caeb9f5`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5)
- Verified acceptance head: [`89ffd99b81e872e3a961767e67fb8ec410df7eae`](https://github.com/teamleaderleo/codex/commit/89ffd99b81e872e3a961767e67fb8ec410df7eae)
- Canonical remote starting head: [`4263facaf3c7d30b26cae33fd1e679278ac02105`](https://github.com/teamleaderleo/codex/commit/4263facaf3c7d30b26cae33fd1e679278ac02105)
- Validation dispatch: [`ddaad65e0ad98c8bc3400937b11f53fb14dd52b9`](https://github.com/teamleaderleo/codex/commit/ddaad65e0ad98c8bc3400937b11f53fb14dd52b9)
- Current gate: the canonical integrated tree is green locally after Rust formatting, but the exact tested formatting-only descendant has not yet been confirmed on the remote branch or reviewed by Agent 3.

## Conclusion

This work supports a strong standalone issue once the exact tested formatted tree is published and the final net diff is reviewed.

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

### 2. Verified acceptance lineage and equivalent combined run

Implementation exercised: [`cea3f73d97897ca5ede37010cbd96addbabda6a5`](https://github.com/teamleaderleo/codex/commit/cea3f73d97897ca5ede37010cbd96addbabda6a5)

Acceptance head: [`89ffd99b81e872e3a961767e67fb8ec410df7eae`](https://github.com/teamleaderleo/codex/commit/89ffd99b81e872e3a961767e67fb8ec410df7eae)

The acceptance lineage preserves the clean negative proof and contains these ordered test commits:

1. `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`
2. `528171c72c06d8be3471752322b7755a1eac3ac8`
3. `0ba57a73ea5895883a21aeb88e923d75a74ed38d`
4. `89ffd99b81e872e3a961767e67fb8ec410df7eae`

The completion-header assertion is corrected. It independently requires:

1. `Script completed\n` at the start;
2. each actual surviving session ID exactly once and in numeric order; and
3. `\nWall time ` after the session-summary line.

The equivalent combined state passed the complete focused acceptance file:

```sh
cargo test -p codex-core \
  --test code_mode_orphan_sessions \
  -- --test-threads=1 --nocapture
```

```text
test result: ok. 5 passed; 0 failed; 0 ignored
```

That earlier equivalent run completed in 16.37 seconds and established the corrected contract before canonical validation.

### 3. Canonical integrated tree validated locally after Rust formatting

Canonical branch: [`fix/code-mode-live-session-summary`](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-summary)

Remote starting head: [`4263facaf3c7d30b26cae33fd1e679278ac02105`](https://github.com/teamleaderleo/codex/commit/4263facaf3c7d30b26cae33fd1e679278ac02105)

Its two-parent ancestry preserves the verified implementation and test lineages:

- first parent: implementation `cea3f73d97897ca5ede37010cbd96addbabda6a5`;
- second parent: acceptance `89ffd99b81e872e3a961767e67fb8ec410df7eae`;
- the original negative reproduction remains in acceptance ancestry; and
- the integrated tree contains the corrected five-test acceptance file.

#### Formatting result and runbook deviation

The full repository `just fmt` route could not run in the Lima VM because `just`, `dotslash`, and `uv` were absent.

Because Patch 1 changes Rust files only, Agent 2 ran:

```sh
cargo fmt --all
```

from `codex-rs`. It changed only:

```text
codex-rs/core/src/tools/code_mode/mod.rs
codex-rs/core/src/unified_exec/process_manager.rs
```

The changes were formatting-only. This is an explicit Rust-only formatter deviation, not a claim that the full multi-language repository formatter passed.

A local formatting-only commit was created during validation, but its SHA was not captured in the shared handoff. GitHub still resolved the remote branch to `4263facaf3c7d30b26cae33fd1e679278ac02105` when checked.

#### Compile/check

Command:

```sh
cargo check \
  --manifest-path codex-rs/Cargo.toml \
  -p codex-core \
  --tests
```

Result:

```text
Finished `dev` profile [unoptimized + debuginfo] target(s) in 7m 48s
```

Compile/check passed. The reported `proc-macro-error2 v2.0.1` future-incompatibility warning is unrelated to Patch 1.

#### Focused code-mode library tests

Commands:

```sh
cargo test -p codex-core --lib terminal_cell_id_excludes_yielded_responses
cargo test -p codex-core --lib terminal_script_status_surfaces_sorted_live_background_sessions
cargo test -p codex-core --lib yielded_script_status_does_not_surface_background_sessions
```

Result:

```text
3 passed; 0 failed
```

#### Focused unified-exec library tests

Commands:

```sh
cargo test -p codex-core --lib unified_exec_persists_across_requests
cargo test -p codex-core --lib multi_unified_exec_sessions
cargo test -p codex-core --lib pruning_does_not_evict_live_process_while_exited_process_is_finalizing
```

Result:

```text
3 passed; 0 failed
```

#### Complete canonical acceptance target

Command:

```sh
cargo test -p codex-core \
  --test code_mode_orphan_sessions \
  -- --test-threads=1 --nocapture
```

Result:

```text
running 5 tests
test code_mode_completion_reports_only_sessions_created_by_current_cell ... ok
test code_mode_completion_reports_only_surviving_nested_session ... ok
test code_mode_completion_surfaces_discarded_live_exec_sessions ... ok
test large_emitted_output_does_not_truncate_live_session_warning ... ok
test yielded_cell_response_does_not_include_completion_session_warning ... ok

test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 17.12s
```

The target compiled in 1m45s before the 17.12-second execution.

No test skips, flakes, or retries were observed. Panic-safe teardown remained active and left no registered background terminals.

Verified coverage now includes:

- both discarded surviving session IDs appear exactly once and in numeric order;
- an exited process is excluded while the one survivor is reported;
- large emitted output cannot truncate or displace the separately prepended session summary;
- an ordinary yielded cell remains completion-neutral;
- a two-cell case proves exact creator-cell isolation, so Cell A's process is not reported for Cell B;
- unified-exec persistence remains intact in the focused library coverage;
- pruning does not evict a live process while an exited process is finalising; and
- acceptance cleanup leaves no registered background terminal behind.

#### Infrastructure incident, not a patch failure

One ad hoc fallback used an incorrectly broad command of the form:

```sh
cargo test -p codex-core <test-name>
```

That widened the build to unrelated integration-test binaries. Concurrent linkers were killed by signal 9 while linking unrelated targets.

This was a runner/resource and command-selection failure, not a Patch 1 compile error and not a failed test assertion. The corrected explicit `--lib` commands passed all six focused tests. A full workspace suite is not claimed.

### 4. Remaining publication gate

The implementation and targeted validation are green locally. The remaining gate is provenance and final review:

- publish the exact Rust-formatted tested descendant: `<published-formatted-head>`;
- confirm the formatting diff contains only the two expected Rust files: `<published-format-diff-check>`;
- record final repository inspection results: `<final-inspection-results>`;
- record Agent 3's final net-diff review: `<agent-3-review-result>`;
- identify the final reviewed head or clean PR comparison: `<final-reviewed-head-or-pr-comparison>`;
- upstream issue link: `<issue-link>`; and
- pull-request link: `<pull-request-link>`.

Keep the issue and PR unpublished until the exact tested formatted tree is on the remote branch and Agent 3 confirms that the net diff contains no lifecycle-policy expansion or accidental validation artifacts.

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

- **#34866:** similar outer-completed/inner-running symptom; this work adds deliberate handle projection, multiple manager-owned sessions, verified acceptance coverage, and typed creator attribution.
- **#32411:** general loss of un-emitted nested results; this case loses control of independently manager-owned live processes.
- **#33816:** abandonment after a direct session was exposed; this case hides the handles before the model receives the outer result.
- **#14731:** proposes blocking turn completion; this proposal preserves persistence and changes terminal code-cell visibility only.
- **#15723:** parent wake-up after background completion; separate eventing and ownership concern.

Do **not** perform the final related-issue refresh yet. Re-fetch these issues, their recent discussions, and any newer duplicate or merged fix only after Agent 1 publishes the exact formatted tested head and Agent 3 completes the final review, so the research is current at publication time.

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

Typed creator attribution is implemented in `cea3f73d97897ca5ede37010cbd96addbabda6a5`. Corrected acceptance coverage is preserved at `89ffd99b81e872e3a961767e67fb8ec410df7eae`. Canonical merge head `4263facaf3c7d30b26cae33fd1e679278ac02105` preserves both histories and the original negative reproduction.

A Rust-formatted local descendant of that canonical merge head passed:

- compile/check in 7m48s;
- focused code-mode library tests: `3 passed; 0 failed`;
- focused unified-exec library tests: `3 passed; 0 failed`;
- complete acceptance file: `5 passed; 0 failed; 0 ignored`, finished in 17.12s;
- no skips or flakes; and
- panic-safe cleanup with no remaining registered background terminals.

The passing acceptance cases cover two sorted live IDs, one-survivor filtering, large-output truncation protection, yielded-cell neutrality, and exact two-cell creator isolation.

The exact formatted tested descendant is not yet confirmed on the remote branch. Final public evidence:

- tested formatted head or PR: `<final-reviewed-head-or-pr-comparison>`;
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

Refresh these descriptions only after the exact formatted tested head is published and reviewed, immediately before publication.

## Maintainer question

Does preserving typed creator-cell attribution on unified-exec process entries and surfacing surviving session IDs in terminal code-mode headers fit the intended ownership contract?

---

## Publication-order variants

Both variants require the exact formatted tested tree to be published, Agent 3's final review, current related-issue research, and stable issue/PR links. Do not choose yet.

### Variant A — issue immediately before the PR

1. Publish and review the exact tested formatted head.
2. Refresh related issues and duplicate search.
3. Publish the issue with stable tested links.
4. Open the PR immediately afterward and cross-link it.

Publication-specific line:

> A tested implementation is ready and will be submitted as a pull request immediately after this report.

### Variant B — issue linked alongside a draft PR

1. Publish and review the exact tested formatted head.
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
- [x] Canonical merge head `4263facaf3c7d30b26cae33fd1e679278ac02105` preserves implementation, corrected acceptance, and negative ancestry.
- [x] Rust formatting changed only the two expected Rust files in the local validation checkout.
- [x] Canonical local compile/check passed in 7m48s.
- [x] Focused code-mode tests passed: `3 passed; 0 failed`.
- [x] Focused unified-exec tests passed: `3 passed; 0 failed`.
- [x] Complete canonical acceptance file passed: `5 passed; 0 failed; 0 ignored`, 17.12s.
- [x] No skips or flakes were observed.
- [x] Broad fallback linker OOM classified as infrastructure/tool-selection failure, not a patch failure.
- [ ] Fill `<published-formatted-head>`.
- [ ] Fill `<published-format-diff-check>`.
- [ ] Fill `<final-inspection-results>`.
- [ ] Fill `<agent-3-review-result>`.
- [ ] Fill `<final-reviewed-head-or-pr-comparison>`.
- [ ] Confirm final net diff contains no lifecycle-policy expansion or accidental validation artifacts.
- [ ] Refresh #34866, #32411, #33816, #14731, and #15723 after Agent 1 publishes the exact tested head and Agent 3 completes review.
- [ ] Search for newer duplicates or merged fixes at the same publication-time refresh.
- [ ] Choose publication Variant A or Variant B.
- [ ] Fill `<issue-link>` and `<pull-request-link>`.
- [ ] Remove every placeholder and verify that no private logs, usernames, prompts, tokens, machine-specific paths, or unrelated incident data appear in the public issue.
- [ ] Perform a final word-count and clarity edit.

## Compact handoff

```text
Agent: 4 — history and upstream issue editor
Branch/ref: research/code-mode-orphan-handoffs
Baseline: 20dafe201d91d4405eef05ecd1db0257f13a9ac8
Changed files: notes/code-mode-orphan-fix/agent-4-history-issue-report.md
Tests run by Agent 4: none; documentation-only update
Verified evidence recorded: Rust-formatted local descendant of canonical merge head compiled; code-mode units 3/3; unified-exec units 3/3; acceptance 5/5 in 17.12s; no skips or flakes; panic-safe cleanup remained active
Formatting note: full repository formatter prerequisites were absent; cargo fmt --all changed only code_mode/mod.rs and process_manager.rs
Infrastructure note: one invalid broad cargo-test fallback OOMed while linking unrelated integration targets; corrected --lib commands passed
Remote state when checked: fix/code-mode-live-session-summary still resolved to unformatted merge head 4263facaf3c7d30b26cae33fd1e679278ac02105
Remaining placeholders: <published-formatted-head>; <published-format-diff-check>; <final-inspection-results>; <agent-3-review-result>; <final-reviewed-head-or-pr-comparison>; <issue-link>; <pull-request-link>
Deferred research: related-issue and duplicate refresh starts only after the exact tested formatted head is published and Agent 3 completes review
Publication status: unpublished; Variant A and Variant B remain open
Recommended next action: Agent 1 publishes the exact formatted tested tree, Agent 3 reviews the remote net diff, then Agent 4 fills placeholders, refreshes related issues, and performs the final publication edit
```