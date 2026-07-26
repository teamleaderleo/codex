# Agent 4: publication architecture and strict copy audit

Status: internal publication-design material; no upstream issue or pull request has been created.

Reviewed state:

- upstream base: `61a44880a85d2fd0d8770908dea5733495e571c8`;
- final clean candidate: `760216784efaee1ba6a3b1250349f31d5f91c7ca`;
- canonical branch: `fix/code-mode-live-session-summary-clean`;
- current drafts:
  - `notes/code-mode-orphan-fix/publication-drafts/standalone-issue.md`;
  - `notes/code-mode-orphan-fix/publication-drafts/pull-request.md`.

## Executive verdict

The current drafts are factually careful but not yet optimally layered. The issue contains too much implementation and test-detail for a problem report, while the PR lacks commit-pinned code links, a concise alternatives section, and explicit citations to the repository's aggregate-test convention. Both drafts repeat the same validation narrative almost verbatim. Neither draft commits the major factual sins this audit was looking for: neither calls the behaviour a literal memory leak, neither claims the broad `codex-core` suite or workspace suite passed, and both state that process persistence is intentional.

The final package should have three layers:

1. a human-authored synthesis of no more than two paragraphs;
2. a concise technical issue plus a design-oriented PR;
3. linked or collapsible exhaustive evidence for readers who want the full record.

The issue should establish the user-visible defect, impact, reproduction, expected output, and behavioural boundary. The PR should carry implementation rationale, alternatives, code links, test-convention links, and bounded validation. The deep-dive should carry chronology, failed approaches, raw result accounting, and methodology.

## Layer 1: human-authored synthesis

This is an editorial scaffold, not a claim that AI text is the human's own account. The human coordinator should rewrite or explicitly adopt it before publication.

> A code-mode script can start nested terminal sessions, discard the returned session IDs while keeping only command output, and then report `Script completed` even though those sessions are still running. The processes are intentionally allowed to persist, but the model loses the handles needed to inspect or stop them. Depending on the command, that can leave CPU, memory, file descriptors, sockets, locks, subprocesses, or filesystem activity running without an obvious control path. This is not evidence of a literal memory leak; it is a loss-of-control-visibility defect with resource-leak risk.
>
> The proposed patch does not terminate processes or change lifecycle policy. It carries the existing code-mode cell identity into stored live process entries, asks the existing session-level unified-exec process manager which matching sessions are still live when the cell reaches a terminal result, and reports those session IDs in the status header. Focused unit and aggregate acceptance tests pass, repeated compatibility checks pass on both candidate and exact base, and the broader `codex-core` suite remains baseline/environment-limited rather than green.

Publication rule: do not paste this synthesis into the upstream issue as an AI-workflow announcement. It is a human-facing framing layer that may be used in a project post, cover note, or maintainer outreach only after explicit human approval.

## Layer 2: maintainer-facing technical package

### Recommended issue structure

Keep expanded:

1. summary;
2. impact;
3. minimal reproduction;
4. actual output;
5. expected output;
6. behavioural boundary;
7. short validation statement;
8. concise related issues.

Move out of the issue:

- detailed ownership propagation;
- internal type names beyond one clarifying sentence;
- alternatives considered;
- test-packaging archaeology;
- broad-run failure counts;
- clean-history reconstruction;
- agent/reviewer identities;
- methodology and chat provenance.

Use one optional `<details>` block for code/test links and extended validation. Do not collapse the reproduction, impact, expected output, or non-goals.

### Recommended PR structure

Keep expanded:

1. summary and problem;
2. design and data flow;
3. behavioural boundaries;
4. alternatives considered;
5. validation summary;
6. issue link.

Use optional `<details>` blocks for:

- exact test commands and full compatibility repetitions;
- broad-suite differential summary;
- exhaustive code/test link index.

Do not hide the visibility-only boundary or yielded neutrality in a collapsed section.

## Strict section-by-section audit: current standalone issue

| Section | No-BS finding | Required action | Correct destination |
|---|---|---|---|
| Proposed title | Accurate but long. “Still-live nested exec session IDs” is precise; “without exposing” can sound like a security disclosure problem rather than missing control handles. | Prefer a title naming the missing handles and misleading completion state. | Issue title. |
| Summary | Factually accurate. The six-step sequence is longer than necessary and partly repeats the reproduction. “Disappeared” is vivid but slightly anthropomorphic; the IDs were projected away by JavaScript and not restored. | Reduce to two short paragraphs. Define `session ID` as the handle used to poll or terminate a yielded terminal. | Issue. |
| Minimal reproduction | Essential, concrete, and small. It demonstrates deliberate projection to `.output`. | Keep visible. Add one sentence that `yield_time_ms` causes each command to return while its process remains live. Link the aggregate acceptance test. | Issue. |
| Actual behaviour | Clear. The sentence about manager ownership is useful but introduces “session-level unified-exec process manager” without explanation. | Keep output visible. Replace jargon with “Codex still tracks both live terminal sessions internally” and link technical detail from the PR. | Issue. |
| Expected behaviour | Strong and testable. Illustrative IDs are labelled. Truncation caveat is accurate but too detailed at this point. | Keep output visible. Keep one sentence saying the patch restores session IDs but does not stop the processes. Move global-history-limit nuance to a short scope note or optional details. | Issue. |
| Ownership and narrow fix | Correct, but this is PR material. It front-loads internal types and repeats the PR's design. “Code mode owns the nested callback” is unexplained jargon for issue readers. | Replace with a three-bullet scope section: existing manager stays authoritative; exact completing-cell live sessions are reported; no lifecycle or schema change. Move type-level reasoning to PR. | PR, with a compact issue summary. |
| Validation | Accurate counts. Too much repeated detail for an issue. The broad-red explanation is important but can be one sentence. “Linux aarch64” is useful context, not a guarantee of cross-platform coverage. | Keep four units, five aggregate cases, 20/20 candidate, 20/20 base, broad-red caveat, workspace-not-run. Put case-by-case coverage and commands in `<details>` or the evidence index. | Short issue summary; full PR/evidence. |
| Related issues | The distinctions are careful but six issue numbers create a literature-review feel. #34866 is genuinely related. #32411 and #33816 are useful secondary context. The grouped wake-up/lifecycle issues are optional. | Keep #34866 expanded. Put #32411 and #33816 in one compact bullet. Move #14731/#15723/#32188 to optional details or the evidence index unless a maintainer asks. | Issue, compact; appendix for the rest. |
| Publication note | Internal workflow instruction, not public issue content. | Remove before publication. | Private handoff only. |

### Issue-wide copy findings

- **Factual overclaim:** none material. The phrase “The aggregate harness uses cleanup protection that runs after success, returned errors, and panics” is structural and accurate; do not re-expand it into “the five tests verify all cleanup paths.”
- **Weak severity framing:** the current draft omits a direct impact section. Add operational impact without assigning security severity.
- **Misleading memory-leak language:** absent, which is correct. Do not introduce “memory leak.” Use “lost session-handle visibility,” “background-process lifecycle hazard,” or “resource-leak risk.”
- **Unexplained jargon:** `terminal Result`, `Terminated`, `Yielded`, `ProcessEntry`, and `ToolCallSource` belong in the PR, not the issue. “Session ID” needs a short plain-language definition.
- **Absent citations:** add commit-pinned links to the reproduction test, terminal rendering, and final comparison.
- **Excessive repetition:** the validation and behavioural boundary are repeated nearly verbatim in the PR.
- **Missing detail:** add impact and clarify that the process continues because persistence is intentional, not because the patch failed to clean it up.
- **Private-only material:** publication sequencing and reciprocal-link procedure.

## Strict section-by-section audit: current pull request

| Section | No-BS finding | Required action | Correct destination |
|---|---|---|---|
| Proposed title | Accurate and conventional, but “terminal completion” can imply process completion. It actually means the outer code cell reached a terminal response. | Prefer “terminal code-mode results” or “when a code-mode cell finishes.” | PR title. |
| Summary | Accurate, compact, and reviewable. It includes six bullets where four would do. | Merge sorting/exited filtering into the lookup bullet; keep tests as one bullet. | PR. |
| Problem | Strong. It repeats the issue almost verbatim. | Reduce to one paragraph and link the issue after publication. | PR. |
| Design | Correct and appropriately detailed. Missing code links. “Optional typed `CellId` creator metadata” assumes familiarity with the call path. | Add a four-step data-flow list with commit-pinned links. Explain why the manager is the liveness authority. | PR. |
| Behavioural boundaries | Essential and accurate. “Public-protocol” and “JavaScript-schema policy” are slightly abstract. | Keep expanded. State concrete non-changes: no termination, no pruning, no wake-up, no schema field change, no call-ID parsing. | PR. |
| Example output | Useful but duplicates the issue. | Keep a short example or link to issue. Mark IDs illustrative. | PR, optional. |
| Validation | Accurate but long. Counts are correct. It should cite the aggregate-test convention and receipts. | Keep the bounded summary expanded. Move commands, individual case descriptions, broad failure accounting, and platform details into `<details>` or evidence index. | PR + appendix. |
| Related work | #34866 is relevant. The PR should primarily say `Fixes #N`; issue literature belongs in the issue. | Keep one sentence linking #34866 only if it helps distinguish scope. | PR, minimal. |
| Publication note | Internal operational instruction. | Remove before publication; insert actual `Fixes #N` after the issue exists. | Private handoff only. |

### PR-wide copy findings

- **Factual overclaim:** none material.
- **Missing design rationale:** explain why creator-cell identity is carried into the existing manager instead of inferred from JavaScript output or call IDs.
- **Missing alternatives:** add a compact alternatives section.
- **Missing code citations:** add commit-pinned links for source attribution, stored entry/query, terminal rendering, manager unit test, aggregate acceptance module, and single-binary convention.
- **Missing convention citations:** cite `codex-rs/core/tests/all.rs` and the existing `code_mode` module registration that drove the test-only revision.
- **Excessive detail:** case-by-case test explanation and broad-suite accounting can be collapsed.
- **Unnecessary repetition:** problem, boundaries, validation, and #34866 distinction largely duplicate the issue.
- **Private-only material:** launcher troubleshooting, machine cache paths, raw logs, research ancestry, agent identities, and publication procedure.

## Ranked issue titles

### 1. Code mode can report completion after losing live nested session IDs

Best balance of symptom and mechanism. “Losing” is understandable and avoids implying that the process itself is leaked or completed. The phrase is slightly causal; the body must clarify that JavaScript can discard the copied IDs and terminal rendering fails to restore them.

### 2. Code mode hides still-live nested session IDs behind `Script completed`

Most user-visible and memorable. “Hides” is rhetorically stronger and may sound intentional, so it is less neutral than option 1.

### 3. `Script completed` can omit session IDs for nested terminals that are still running

Most descriptive and least jargon-heavy. It is long, but it accurately states the contradiction without implying a memory leak or lifecycle change.

### 4. Code mode can finish without preserving control handles for live nested terminals

Best conceptual framing, but “control handles” is not existing product terminology and would require explanation.

Recommendation: option 1. Use option 3 if maximum literal clarity is preferred over brevity.

## Ranked PR titles

### 1. code-mode: report live nested session IDs in terminal results

Precise about the outer code-mode result and avoids implying that the nested process completed. It describes behaviour rather than implementation.

### 2. code-mode: preserve creator-cell attribution for live session reporting

Best design-oriented title. It is less obvious to users and foregrounds an internal mechanism.

### 3. code-mode: restore live nested session handles when a cell finishes

Clear intent, but “restore” and “handles” are slightly more abstract than the actual output field.

### 4. code-mode: surface live nested exec session IDs on terminal completion

The current title. Accurate, but “terminal completion” is ambiguous between a terminal response and a completed process.

Recommendation: option 1.

## Proposed technical issue copy

### Proposed title

**Code mode can report completion after losing live nested session IDs**

### Proposed body

```markdown
## Summary

A code-mode JavaScript cell can start nested terminal commands, keep only their `.output`, and discard the returned session IDs. The cell can then report `Script completed` while those terminal sessions are still running. Codex still tracks them internally, but the model no longer has the session IDs needed to poll or terminate them.

Background terminal persistence is intentional. The defect is that a terminal code-mode result can lose model-visible control handles for work that remains live.

## Impact

A user or model can believe the script is finished while nested commands continue running without an obvious control path. Depending on the command, the remaining processes may continue consuming CPU, memory, file descriptors, sockets, locks, subprocesses, or filesystem state until they exit or are found and terminated by another route.

This is not evidence of a literal memory leak, and this report does not assign a security severity. It is a control-visibility defect with operational resource-leak risk.

## Minimal reproduction

`yield_time_ms` lets each command return a session ID while its process continues in the background. This example deliberately projects the returned objects down to `.output`:

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

Both nested terminal sessions are still live, but their session IDs are absent from the model-visible result.

## Expected behaviour

```text
Script completed
Background sessions still running: 6306, 11236
Wall time ...
Output:
orphan-a|orphan-b
```

`6306` and `11236` are illustrative session IDs. Reporting them restores the model's ability to poll or terminate the sessions; it does not stop the processes or change their lifetime.

## Behavioural boundary

The proposed fix reports the still-live session IDs created by the completing cell, using the existing session-level unified-exec process manager as the liveness source. It excludes exited sessions, does not report another cell's sessions, and does not add the completion-only warning to an ordinary yielded cell.

No lifecycle, termination, pruning, recovery, protocol, call-ID, or JavaScript result-schema policy changes.

## Validation

On Linux aarch64, repository-native formatting and scoped fix checks passed, four focused unit tests passed, and five aggregate code-mode acceptance cases passed. Two existing compatibility tests also passed 20/20 executions on the candidate and 20/20 on the exact upstream base.

The broader `codex-core` run remained red on both compared refs because of environment, helper-binary, sandbox/runner, and unrelated baseline failures; no persistent candidate-only failure remained. The broad suite is not claimed as green. The complete workspace suite was not run.

<details>
<summary>Code and test references</summary>

- [Creator-cell attribution at nested exec dispatch](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L132-L138)
- [Stored attribution and exact-cell live-only manager query](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L76-L99)
- [Manager query and stored live process entry](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L168-L199)
- [Terminal-only lookup and status rendering](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/code_mode/mod.rs#L199-L300)
- [Executable reproduction and multiple-session acceptance case](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs#L159-L205)
- [Exited-session filtering, truncation placement, yielded neutrality, and two-cell isolation](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs#L207-L504)

</details>

## Related issues

- #34866 is related prior symptom coverage: it also reports `Script completed` while a nested shell remains live. This issue covers the narrower tested case where live session IDs are discarded by JavaScript and not restored in the terminal outer result.
- #32411 covers the broader loss of arbitrary awaited-but-unemitted nested results and artifact handles. #33816 covers model behaviour after a session ID was already exposed.
```

Notes:

- Keep #34866 as prior symptom coverage, not the canonical issue.
- Add the PR link after opening the PR.
- If maintainers consider the secondary related issues distracting, retain only #34866 in the issue and move the rest to the evidence index.

## Proposed technical PR copy

### Proposed title

**code-mode: report live nested session IDs in terminal results**

### Proposed body

```markdown
Fixes #<standalone issue number>

## Summary

- carry code-mode creator-cell identity into stored live process entries;
- query the existing session-level unified-exec process manager for exact-cell, still-live sessions when a code-mode cell reaches a terminal result;
- report the matching session IDs in the status header, while leaving yielded responses and process lifecycle policy unchanged;
- add direct manager coverage and five aggregate code-mode acceptance cases.

## Problem

Nested `exec_command` calls can yield live session IDs to JavaScript, but the script can discard those IDs by emitting only `.output`. The outer cell can then report `Script completed` while the session-level process manager still owns live nested terminals and the model has no ID with which to poll or terminate them.

The issue contains the minimal reproduction and expected output. This PR restores control visibility; it does not terminate or shorten the lifetime of any process.

## Design

1. [`ExecCommandHandler` converts the existing `ToolCallSource::CodeMode` cell value into typed creator metadata](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L132-L138).
2. [`UnifiedExecContext` carries that optional `CellId` to process creation](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L76-L99), and the manager's stored live process entry retains it.
3. [`live_process_ids_created_by_cell` performs a read-only exact-cell lookup, excludes exited entries, and returns sorted logical session IDs](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L168-L199).
4. [Code-mode response handling invokes that lookup only for terminal `Result` and `Terminated` responses, after emitted output is truncated, and prepends the status header](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/code_mode/mod.rs#L199-L300).

The existing process manager remains the sole liveness authority. Creator metadata scopes a read-only query; it does not create a second registry or infer ownership from JavaScript values, command text, or nested call-ID formatting.

## Behavioural boundaries

- successful `Result`, failed `Result`, and explicit `Terminated` responses may report matching still-live session IDs;
- ordinary `Yielded` responses remain completion-neutral;
- exited entries and entries from other cells are excluded;
- nested call IDs remain opaque;
- the JavaScript-visible nested result schema is unchanged;
- no termination, pruning, persistence, shutdown, interrupt, dispatch, wake-up, recovery, or public-protocol policy changes.

The warning is outside code-mode emitted-output truncation because the status header is added after that truncation step. The complete tool result remains subject to later global conversation-history limits.

## Alternatives considered

- **Read the IDs back from emitted JavaScript values:** rejected because the failure is precisely that JavaScript can discard them.
- **Parse cell identity from nested call IDs:** rejected because call IDs are intentionally opaque and carry no supported ownership contract.
- **Maintain a second code-mode liveness registry:** rejected because the unified-exec process manager already owns process state and must remain the source of truth.
- **Change the JavaScript result schema or auto-surface arbitrary nested outputs:** broader than the live-session visibility defect and risks compatibility changes.
- **Terminate processes, block cell/turn completion, or add wake-up events:** lifecycle-policy changes outside this patch.
- **Store a generic process-origin enum:** plausible future generalisation, but `Option<CellId>` is the narrowest crate-private metadata required here.
- **Cap the displayed session list:** not selected because it would knowingly omit live control handles; the result remains subject to existing later global-history limits.

## Validation

- `just fmt`: passed;
- `just fix -p codex-core`: passed;
- four focused unit tests: 4 passed, 0 failed;
- five aggregate code-mode acceptance cases: 5 passed, 0 failed;
- two existing compatibility tests repeated ten times each on the candidate: 20/20 passed;
- the same two tests repeated ten times each on exact upstream base `61a44880a85d2fd0d8770908dea5733495e571c8`: 20/20 passed;
- clean worktree and `git diff --check`: passed.

The broad `just test -p codex-core` comparison was red on both the production-equivalent candidate and exact upstream base. Persistent failures were accounted for as environment/helper-binary, sandbox/runner, or unrelated failures reproduced upstream; repeated focused comparison left no persistent candidate-only failure. The broad suite is not claimed as green. The complete workspace suite was not run.

## Test placement and conventions

The final acceptance cases run through the repository's [single aggregate integration-test binary](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/all.rs#L1-L9) and are registered as a child of the existing [code-mode suite module](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode.rs#L59-L77). The tests reuse parent helpers and use bounded cleanup/exit handling rather than a standalone integration target or fixed sleeps.

<details>
<summary>Focused coverage links</summary>

- [Exact-cell, unattributed-entry, exited-entry, and ordering manager unit test](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod_tests.rs#L332-L395)
- [Multiple live sessions and deterministic ordering](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs#L159-L205)
- [Exited-session exclusion](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs#L207-L282)
- [Warning placement outside emitted-output truncation](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs#L284-L352)
- [Yielded neutrality and completing-cell isolation](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs#L354-L504)

</details>

## Related work

#34866 is related prior symptom coverage. This PR implements the narrower exact-cell live-session reporting contract described by the standalone issue above.
```

Publication note: replace `<standalone issue number>` with the actual number before opening the PR. This placeholder belongs only in this internal design document, not in final public copy.

## Layer 3: exhaustive evidence

The exhaustive record should be linked, not pasted wholesale. Recommended public-safe entry point:

- `notes/code-mode-orphan-fix/deep-dive/evidence-index.md`.

The index should separate:

- final code and tests;
- executable reproduction and validation receipts;
- matched-base differential evidence;
- architecture and publication reviews;
- static external review;
- related issues;
- private/raw material that requires explicit disclosure approval.

Use `<details>` in public copy only for optional code/test references and extended validation. Do not use it to bury the reproduction or the fact that the patch does not terminate processes.

## Material placement matrix

| Material | Human synthesis | Issue | PR | Exhaustive appendix | Private only |
|---|---:|---:|---:|---:|---:|
| Plain-language symptom and impact | yes | yes | brief | yes | no |
| Minimal reproduction and expected output | no | yes, expanded | link/brief | yes | no |
| Typed creator-cell data flow | no | one sentence | yes | yes | no |
| Manager liveness rationale | no | one sentence | yes | yes | no |
| Alternatives considered | no | no | compact | exhaustive | no |
| Exact focused counts | brief | brief | yes | yes | no |
| Exact broad-run failure inventory | no | no | collapsed summary | yes | raw logs private |
| Test packaging reversal | no | no | convention note | yes | launcher debugging private |
| Chat roles and AI methodology | optional separate post | no | no | methodology note | raw chats private |
| Raw logs, JSONL, machine paths, tokens, user data | no | no | no | only scrubbed index | yes |
| Publication sequence and cross-link procedure | no | no | no | internal handoff | yes/internal |

## Remaining human decisions

1. Choose or edit the issue and PR titles.
2. Write or explicitly adopt the two-paragraph human synthesis.
3. Decide whether the deep-dive index itself should be public, linked only on request, or kept internal.
4. Approve the exact severity language; this audit recommends operational resource-risk framing without a security rating.
5. Approve issue-first-then-PR publication and the exact publication time.
6. Approve any disclosure of raw chats, logs, or external-review prompts separately from the code submission.
