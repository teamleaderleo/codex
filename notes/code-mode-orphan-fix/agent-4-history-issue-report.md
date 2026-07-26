# Agent 4 report: final evidence, issue draft, and PR draft

## Status

- Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
- Research refresh date: 2026-07-26
- Repository visibility: this working note is on a public fork and must be treated as publicly accessible.
- Publication status: unpublished. No upstream issue, comment, or pull request has been created.
- Verified baseline regression: [`7298dcf44f61164ffc25b8bdf5f136281caeb9f5`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5)
- Verified acceptance head: [`89ffd99b81e872e3a961767e67fb8ec410df7eae`](https://github.com/teamleaderleo/codex/commit/89ffd99b81e872e3a961767e67fb8ec410df7eae)
- Integrated merge head: [`4263facaf3c7d30b26cae33fd1e679278ac02105`](https://github.com/teamleaderleo/codex/commit/4263facaf3c7d30b26cae33fd1e679278ac02105)
- Published formatted and reviewed head: [`73e5b9fc28de0815975fad3c3d70a6a0b38399b1`](https://github.com/teamleaderleo/codex/commit/73e5b9fc28de0815975fad3c3d70a6a0b38399b1)
- Final reviewed comparison: [`20dafe201d91d4405eef05ecd1db0257f13a9ac8...73e5b9fc28de0815975fad3c3d70a6a0b38399b1`](https://github.com/teamleaderleo/codex/compare/20dafe201d91d4405eef05ecd1db0257f13a9ac8...73e5b9fc28de0815975fad3c3d70a6a0b38399b1)
- Agent 3 final review: [`final-net-diff-review-73e5b9f.md`](https://github.com/teamleaderleo/codex/blob/8577cea6c925dde7453641b7587190285979a3ad/notes/code-mode-orphan-fix/final-net-diff-review-73e5b9f.md), commit [`8577cea6c925dde7453641b7587190285979a3ad`](https://github.com/teamleaderleo/codex/commit/8577cea6c925dde7453641b7587190285979a3ad), verdict **pass**.

**Implementation correctness review is complete.** Remaining work is pre-PR engineering hygiene, final team sanity review, personal wording/presentation review, and publication sequencing.

## Defect and ownership boundary

The verified failure sequence is:

1. A code-mode JavaScript cell launches nested `tools.exec_command()` calls.
2. The commands cross `yield_time_ms`; unified exec stores each live process in the conversation-level process manager and returns a copied `session_id` handle to JavaScript.
3. JavaScript consumes only `.output`, projecting away both copied handles.
4. The JavaScript cell returns successfully.
5. The outer result says `Script completed` while the manager-owned processes remain alive.
6. The model-visible result contains no session IDs with which to poll, inspect, or terminate those processes.

The ownership boundary is now settled:

- **Code mode owns the nested callback task** while the nested tool call is being dispatched and awaited.
- **The conversation-level unified-exec process manager owns the live process** after `store_process` registers it.
- **JavaScript receives only a copied logical handle.** The returned object does not own the process.
- **Dropping or projecting away the handle has no lifecycle effect.** The process remains live in the manager.
- **The defect is model-visible control loss at terminal reporting time**, not unintended process persistence.

Patch 1 is therefore visibility-only. It does not terminate sessions or change cross-turn, interrupt, shutdown, or natural-exit policy.

## Final evidence

### 1. Verified baseline reproduction

Commit: [`7298dcf44f61164ffc25b8bdf5f136281caeb9f5`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5)

Test: `code_mode_completion_does_not_surface_discarded_live_exec_sessions`

Platform: Linux aarch64 under Lima.

Publication-safe equivalent command; a machine-specific Cargo cache path used during the original run has been deliberately omitted from this public note:

```sh
RUST_MIN_STACK=8388608 \
CARGO_BUILD_JOBS=4 \
CARGO_INCREMENTAL=1 \
CARGO_PROFILE_TEST_DEBUG=0 \
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

The negative regression proves that two copied handles can be discarded, the outer result can claim completion without surfacing either ID, both manager-owned processes can remain alive, and panic-safe teardown removes all test processes.

### 2. Corrected acceptance lineage

Acceptance head: [`89ffd99b81e872e3a961767e67fb8ec410df7eae`](https://github.com/teamleaderleo/codex/commit/89ffd99b81e872e3a961767e67fb8ec410df7eae)

Ordered test lineage:

1. negative proof `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`;
2. initial acceptance `528171c72c06d8be3471752322b7755a1eac3ac8`;
3. contract and two-cell isolation correction `0ba57a73ea5895883a21aeb88e923d75a74ed38d`;
4. truncation assertion correction `89ffd99b81e872e3a961767e67fb8ec410df7eae`.

The completion assertion independently requires:

1. `Script completed\n` at the start;
2. each actual surviving session ID exactly once and in numeric order; and
3. `\nWall time ` after the session-summary line.

Coverage includes:

- two discarded surviving IDs;
- deterministic numeric ordering;
- one-survivor filtering after another process exits;
- warning placement outside emitted-output truncation;
- yielded-response neutrality;
- exact two-cell creator isolation; and
- panic-safe cleanup with no remaining registered terminal.

### 3. Published formatted implementation

Branch: [`fix/code-mode-live-session-summary`](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-summary)

Published head: [`73e5b9fc28de0815975fad3c3d70a6a0b38399b1`](https://github.com/teamleaderleo/codex/commit/73e5b9fc28de0815975fad3c3d70a6a0b38399b1)

The head is exactly one commit after integrated merge head `4263facaf3c7d30b26cae33fd1e679278ac02105`.

Formatting comparison: [`4263facaf3c7d30b26cae33fd1e679278ac02105...73e5b9fc28de0815975fad3c3d70a6a0b38399b1`](https://github.com/teamleaderleo/codex/compare/4263facaf3c7d30b26cae33fd1e679278ac02105...73e5b9fc28de0815975fad3c3d70a6a0b38399b1)

That comparison changes only:

- `codex-rs/core/src/tools/code_mode/mod.rs`;
- `codex-rs/core/src/unified_exec/process_manager.rs`.

The delta is Rust formatter line wrapping only. It does not change expressions, branches, data flow, tests, process state, output semantics, or lifecycle policy.

The integrated merge ancestry preserves:

- first parent: typed-attribution implementation `cea3f73d97897ca5ede37010cbd96addbabda6a5`;
- second parent: corrected acceptance head `89ffd99b81e872e3a961767e67fb8ec410df7eae`;
- the original negative proof in acceptance ancestry.

### 4. Canonical validation

Compile/check:

```sh
cargo check \
  --manifest-path codex-rs/Cargo.toml \
  -p codex-core \
  --tests
```

```text
Finished `dev` profile [unoptimized + debuginfo] target(s) in 7m 48s
```

Focused code-mode library tests:

```sh
cargo test -p codex-core --lib terminal_cell_id_excludes_yielded_responses
cargo test -p codex-core --lib terminal_script_status_surfaces_sorted_live_background_sessions
cargo test -p codex-core --lib yielded_script_status_does_not_surface_background_sessions
```

```text
3 passed; 0 failed
```

Focused unified-exec library tests:

```sh
cargo test -p codex-core --lib unified_exec_persists_across_requests
cargo test -p codex-core --lib multi_unified_exec_sessions
cargo test -p codex-core --lib pruning_does_not_evict_live_process_while_exited_process_is_finalizing
```

```text
3 passed; 0 failed
```

Complete acceptance target:

```sh
cargo test -p codex-core \
  --test code_mode_orphan_sessions \
  -- --test-threads=1 --nocapture
```

```text
running 5 tests
test code_mode_completion_reports_only_sessions_created_by_current_cell ... ok
test code_mode_completion_reports_only_surviving_nested_session ... ok
test code_mode_completion_surfaces_discarded_live_exec_sessions ... ok
test large_emitted_output_does_not_truncate_live_session_warning ... ok
test yielded_cell_response_does_not_include_completion_session_warning ... ok

test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 17.12s
```

No skips, flakes, or retries were observed on the correctly scoped commands. Full workspace validation is not claimed.

One incorrectly broad ad hoc test command selected unrelated integration binaries and exhausted runner memory during linking. That was a command-selection and infrastructure event, not a Patch 1 compile or assertion failure. It is excluded from the proposed upstream issue and PR text.

### 5. Final correctness review

Agent 3 reviewed [`20dafe201d91d4405eef05ecd1db0257f13a9ac8...73e5b9fc28de0815975fad3c3d70a6a0b38399b1`](https://github.com/teamleaderleo/codex/compare/20dafe201d91d4405eef05ecd1db0257f13a9ac8...73e5b9fc28de0815975fad3c3d70a6a0b38399b1) and passed the net diff.

The comparison contains seven files: six production files plus `codex-rs/core/tests/code_mode_orphan_sessions.rs`. Agent 3 confirmed:

- **typed creator-cell attribution:** `ToolCallSource::CodeMode` becomes typed `CellId` metadata on `UnifiedExecContext` and the stored `ProcessEntry`;
- **exact-cell live-only filtering:** manager lookup uses exact `CellId` equality, excludes exited processes, and returns sorted logical IDs;
- **terminal-only disclosure:** only `Result` and `Terminated` query and report surviving sessions;
- **yielded-response neutrality:** `Yielded` does not query or expose completion-only session information;
- **warning placement outside truncation:** emitted output is converted and truncated before the status header is prepended;
- **opaque nested call IDs:** UUID-based nested IDs remain opaque and carry no cell identity;
- **unchanged JavaScript schema:** the nested result shape remains compatible; and
- **unchanged lifecycle policy:** no termination, pruning, persistence, shutdown, interrupt, dispatch, subagent, remote-exec, or recovery policy expansion was found.

No further Patch 1 code change was requested by the correctness review.

## Correctness complete versus pre-PR engineering hygiene

### Completed correctness work

- executable negative reproduction;
- typed-attribution implementation;
- corrected positive acceptance coverage;
- one-survivor, truncation, yielded, and two-cell isolation cases;
- formatted tested head published;
- compile/check, six focused library tests, and five acceptance tests passed;
- final baseline net-diff sign-off passed;
- privacy scrub of the proposed public issue and PR text.

### Remaining pre-PR engineering hygiene

These are not unresolved correctness findings. They are the remaining steps for a clean upstream submission:

1. **Clean candidate history:** prepare `<clean-candidate-head>` without research/prototype ancestry while preserving the reviewed net effect.
2. **Sync with current upstream main:** record `<upstream-main-sync-result>` and resolve any real conflicts without expanding Patch 1.
3. **Repository-native validation:** run the current upstream-documented formatter, lint/fix, and test commands on the clean candidate and record `<repository-native-validation-results>`.
4. **Final clean comparison:** publish `<final-clean-candidate-comparison>` and verify it is semantically equivalent to the reviewed `20dafe...73e5` comparison.
5. **Final repository inspection:** fill `<final-repository-inspection-results>` only after the actual outputs are available for `git status --short`, `git diff --check`, and the agreed log/stat/name-status commands. No result is inferred here.
6. **Human review:** complete one final team sanity review and the user's personal wording/presentation pass.
7. **Publication links:** fill `<issue-link>` and `<pull-request-link>` only after publication.

## Upstream issue and fix refresh

Refresh performed on 2026-07-26.

### Search result

- No newer exact duplicate was identified beyond the known closest reports.
- No upstream pull request or merged commit was found that implements typed creator-cell attribution plus terminal exact-cell live-session disclosure.
- Upstream code search did not find the proposed `live_process_ids_created_by_cell` API.
- The exact `"Script completed"` plus nested-session issue search continues to surface #34866 and #32411 as the nearest reports.
- Re-run this search immediately before publication if publication is delayed, because upstream state can change.

### Current distinctions

- **#34866 — open, closest symptom.** It reports one logical command exposing an outer `cell_id` and inner `session_id`, with `Script completed` while the shell remains live. Its discussion explicitly distinguishes that runtime-interface problem from #33816. Patch 1 is narrower: it restores model-visible IDs when JavaScript omits them, supports multiple live sessions, and does not unify the two lifecycle APIs or redefine `Script completed`.
- **#32411 — open.** It covers all awaited-but-unemitted nested results and artifact handles. Patch 1 does not auto-surface completed outputs, exit codes, run IDs, or arbitrary artifacts; it reports only still-live manager-owned session IDs.
- **#33816 — open.** It covers model-side abandonment and duplicate command attempts after a live `session_id` was already exposed. Patch 1 addresses a preceding interface failure where the IDs never reach the model.
- **#14731 — open.** It proposes preventing a turn from completing while unified-exec work remains live. Patch 1 intentionally preserves turn and process persistence policy and changes terminal code-cell visibility only.
- **#15723 — open.** It covers waking a parent after a subprocess or subagent completes. Community fork candidates and runtime-receipt discussion exist, but no linked upstream PR or merged fix is shown. Patch 1 does not add wake-ups or completion delivery.
- **#32188 — open.** It is the consolidated event-driven background-exec wake-up feature discussion. #33712 was closed in favour of #32188. That wake-up mechanism is separate from reporting IDs that are already live when a code cell reaches a terminal response.

No current issue page shows linked upstream development that subsumes this exact tested patch. The standalone issue remains justified, but it should cross-link #34866 prominently and state the narrower scope plainly.

## Publication-order variants and recommendation

Both variants remain viable.

### Variant A — issue immediately followed by the PR

1. Finish clean-candidate hygiene and human review.
2. Publish the issue with the final tested comparison.
3. Open the PR immediately afterward.
4. Cross-link both within the same working session.

### Variant B — issue alongside a draft PR

1. Finish clean-candidate hygiene and human review.
2. Prepare a draft PR without publishing it.
3. Publish the issue and draft PR together.
4. Keep the PR in draft while early feedback and CI arrive.

### Recommendation

**Recommend Variant A: publish the issue, then open the PR immediately afterward.**

The problem statement is independently strong and now has a verified baseline, a tested fix, and final correctness review. Publishing the issue first keeps the discussion problem-led rather than implementation-led. The gap should be only a few minutes, with immediate cross-links. Use Variant B instead only if the upstream-main sync or repository-native checks introduce material uncertainty that makes draft status genuinely useful.

---

# Unpublished upstream issue draft

**Title:** Code mode can report completion after discarding live nested exec session handles

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

- Code mode owns each nested callback task while dispatching and awaiting the nested call.
- After unified exec stores a yielded process, the conversation-level process manager owns it.
- JavaScript receives only a copied logical handle; discarding that handle does not affect the process.
- The baseline dispatch path carries typed `ToolCallSource::CodeMode { cell_id, ... }` metadata, but unified exec does not retain the creator cell on the stored process entry.
- Terminal code-cell rendering therefore cannot recover the still-live sessions created by the cell when JavaScript omits the handles.

## Tested narrow fix

Reviewed implementation head: [`73e5b9fc28de0815975fad3c3d70a6a0b38399b1`](https://github.com/teamleaderleo/codex/commit/73e5b9fc28de0815975fad3c3d70a6a0b38399b1)

Reviewed comparison: [`20dafe201d91d4405eef05ecd1db0257f13a9ac8...73e5b9fc28de0815975fad3c3d70a6a0b38399b1`](https://github.com/teamleaderleo/codex/compare/20dafe201d91d4405eef05ecd1db0257f13a9ac8...73e5b9fc28de0815975fad3c3d70a6a0b38399b1)

The patch:

1. carries typed creator-cell attribution from `ToolCallSource::CodeMode` through unified exec;
2. stores it on already-persisted live process entries;
3. queries exact-cell, still-live process IDs on terminal `Result` and `Terminated` responses;
4. excludes exited processes and sorts the IDs deterministically;
5. prepends the IDs to the status header after emitted-output truncation;
6. keeps ordinary `Yielded` responses completion-neutral;
7. preserves opaque nested call IDs, the JavaScript result schema, and existing lifecycle policy.

## Validation

- Baseline negative reproduction: `1 passed; 0 failed; 0 ignored`.
- Compile/check: passed.
- Focused code-mode library tests: `3 passed; 0 failed`.
- Focused unified-exec library tests: `3 passed; 0 failed`.
- Acceptance target: `5 passed; 0 failed; 0 ignored`.
- Acceptance cases cover two sorted IDs, one survivor, large-output truncation, yielded neutrality, exact two-cell isolation, and panic-safe cleanup.
- Final net-diff review: pass; no lifecycle-policy expansion found.

## Non-goals

This patch does not:

- terminate background terminals;
- change persistence across turns or interrupts;
- change the JavaScript-visible nested result schema;
- block turn completion while a process remains live;
- wake an idle parent when a process or subagent completes;
- auto-surface arbitrary completed nested outputs or artifact handles;
- change hidden-subagent, dispatch, shutdown, remote-termination, or recovery policy.

## Related issues

- #34866 is the closest symptom, but it already exposes an inner `session_id` and asks for clearer wrapper/process lifecycle semantics. This report covers deliberate handle loss, multiple live sessions, manager-state verification, and typed creator attribution.
- #32411 covers arbitrary awaited-but-unemitted nested results and artifact handles. This patch is limited to still-live manager-owned session IDs.
- #33816 covers model-side abandonment after a session ID was exposed. This case hides the IDs before the model receives the terminal result.
- #14731 proposes guarding turn completion while background work remains live. This patch preserves turn and process lifecycle policy.
- #15723 and #32188 cover event-driven wake-up after background completion. This patch reports live IDs at an existing terminal code-cell boundary and adds no wake-up mechanism.

## Maintainer question

Does retaining typed creator-cell attribution on unified-exec process entries and surfacing exact-cell surviving IDs in terminal code-mode headers fit the intended ownership and reporting contract?

---

# Unpublished upstream PR draft

**Proposed title:** `code-mode: surface live nested exec session IDs on terminal completion`

## Summary

- preserve typed code-mode creator-cell attribution on stored unified-exec process entries;
- report exact-cell, still-live nested session IDs in terminal code-mode status headers;
- exclude exited processes and sort IDs deterministically;
- keep yielded responses, JavaScript result schema, opaque nested call IDs, and process lifecycle policy unchanged;
- add focused unit and end-to-end acceptance coverage.

## Problem

A code-mode script can launch nested `exec_command` calls, receive live `session_id` values, and then project those values away by emitting only `.output`. The JavaScript cell can complete successfully while the processes remain alive in the conversation-level process manager. The outer model-visible result then says `Script completed` but provides no IDs for polling or termination.

The process manager already owns the live processes. The missing piece is typed creator attribution that lets the terminal code-cell response identify the matching live sessions without relying on emitted JavaScript values or call-ID text.

## Implementation

- Convert `ToolCallSource::CodeMode { cell_id, .. }` into optional typed creator-cell metadata in `UnifiedExecContext`.
- Copy that metadata onto each stored live `ProcessEntry`.
- Add a read-only manager query that uses exact `CellId` equality, excludes exited processes, and returns sorted logical process IDs.
- Query that method only for terminal `Result` and `Terminated` responses.
- Prepend the live-session summary after emitted output has been converted and truncated.
- Preserve the existing primary success, failure, and termination status text.
- Preserve ordinary `Yielded` status behaviour.

## Behavioural boundary

This PR is visibility-only. It does not terminate processes, alter persistence, block turn completion, wake idle sessions, change nested call IDs, or change the JavaScript-visible result schema.

## Validation

Reviewed source comparison: [`20dafe201d91d4405eef05ecd1db0257f13a9ac8...73e5b9fc28de0815975fad3c3d70a6a0b38399b1`](https://github.com/teamleaderleo/codex/compare/20dafe201d91d4405eef05ecd1db0257f13a9ac8...73e5b9fc28de0815975fad3c3d70a6a0b38399b1)

- `cargo check --manifest-path codex-rs/Cargo.toml -p codex-core --tests`
- focused code-mode library tests: `3 passed; 0 failed`
- focused unified-exec library tests: `3 passed; 0 failed`
- `cargo test -p codex-core --test code_mode_orphan_sessions -- --test-threads=1 --nocapture`
- acceptance result: `5 passed; 0 failed; 0 ignored`
- no skips or flakes on the correctly scoped commands
- final correctness review: pass

Acceptance coverage verifies:

- two discarded live IDs are surfaced exactly once and in numeric order;
- only the surviving process is reported when another exits;
- a large emitted payload cannot truncate the status warning;
- yielded cells do not receive completion-only disclosure;
- one cell cannot disclose another cell's process;
- teardown leaves no registered background terminal.

## Issue

Refs `<issue-link>`.

## Final submission metadata

- clean candidate: `<clean-candidate-head>`
- upstream-main sync: `<upstream-main-sync-result>`
- repository-native checks: `<repository-native-validation-results>`
- final clean comparison: `<final-clean-candidate-comparison>`
- final repository inspection: `<final-repository-inspection-results>`

---

## Final publication checklist

### Correctness and evidence — complete

- [x] Baseline failure preserved and reproduced.
- [x] Corrected positive acceptance lineage preserved.
- [x] Exact creator-cell isolation covered.
- [x] Published formatted head recorded.
- [x] Formatting comparison limited to the two expected Rust files.
- [x] Compile/check passed.
- [x] Six focused library tests passed.
- [x] Five acceptance tests passed with no skips or flakes.
- [x] Agent 3 final net-diff review passed.
- [x] Typed attribution, live-only exact-cell filtering, terminal-only disclosure, yielded neutrality, truncation placement, opaque IDs, schema compatibility, and lifecycle boundary confirmed.
- [x] Related-issue state, comments, newer duplicates, and merged-fix search refreshed.
- [x] Publication issue draft updated.
- [x] One-PR title and body prepared.
- [x] Publication-order recommendation recorded.
- [x] Public-text privacy scrub completed.

### Pre-PR engineering hygiene — open

- [ ] Fill `<clean-candidate-head>`.
- [ ] Fill `<upstream-main-sync-result>`.
- [ ] Fill `<repository-native-validation-results>`.
- [ ] Fill `<final-clean-candidate-comparison>`.
- [ ] Fill `<final-repository-inspection-results>` from actual shell outputs; do not infer it.
- [ ] Agent 3 or another reviewer confirms the clean candidate is equivalent to the reviewed head.
- [ ] Complete final team sanity review.
- [ ] Complete the user's personal wording and presentation pass.
- [ ] Approve Variant A or Variant B.
- [ ] Fill `<issue-link>` and `<pull-request-link>` after publication.

## Compact handoff

```text
Agent: 4 — evidence and publication-preparation owner
Branch/ref: research/code-mode-orphan-handoffs
Baseline: 20dafe201d91d4405eef05ecd1db0257f13a9ac8
Changed files: notes/code-mode-orphan-fix/agent-4-history-issue-report.md
Tests run by Agent 4: none; evidence, upstream research, privacy scrub, and publication-copy update only
Final reviewed implementation: fix/code-mode-live-session-summary @ 73e5b9fc28de0815975fad3c3d70a6a0b38399b1
Final correctness review: pass at 8577cea6c925dde7453641b7587190285979a3ad
Upstream refresh: no newer exact duplicate or merged typed-creator-cell visibility fix found; #34866 remains the closest symptom
Issue draft status: publication-ready pending human wording pass and clean-candidate metadata
PR draft status: title and one-PR body prepared; no PR exists
Recommendation: publish the issue and immediately follow with the PR, cross-linking both
Remaining placeholders: <clean-candidate-head>; <upstream-main-sync-result>; <repository-native-validation-results>; <final-clean-candidate-comparison>; <final-repository-inspection-results>; <issue-link>; <pull-request-link>
Publication status: unpublished
```
