# Agent 1 reconstruction: Patch 1 discovery and investigation

Date: 2026-07-26

Status: internal engineering record. This document is not part of the clean upstream candidate and is not automatically suitable for public release.

## Scope and evidence labels

This reconstruction follows the chronology from the original macOS incident through the first executable negative proof and the eventual Patch 1 acceptance contract. It does not reconstruct later publication, clean-history, or broad-validation work except where that work clarifies an earlier decision.

Every factual paragraph uses one of these labels:

- **Directly preserved evidence** — reviewable in a named repository file, commit, test, workflow artifact, or public related issue.
- **Reliable recollection** — retained from the original investigation conversation, but the underlying private local artifact is not present in this fork.
- **Inference** — a conclusion drawn from preserved code and evidence; the supporting sources are named.
- **Missing evidence** — material known to have existed but not retained in a form that can be cited or published safely.

The strongest public internal sources are:

- the preserved incident summary in [`../README.md`](../README.md);
- the Patch 1 research handoff in [`../patch-1-live-session-summary.md`](../patch-1-live-session-summary.md);
- the ownership and provenance record in [`../decision-log.md`](../decision-log.md);
- the immutable negative reproduction commit [`7298dcf4`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5);
- the corrected acceptance lineage [`528171c7`](https://github.com/teamleaderleo/codex/commit/528171c72c06d8be3471752322b7755a1eac3ac8), [`0ba57a73`](https://github.com/teamleaderleo/codex/commit/0ba57a73ea5895883a21aeb88e923d75a74ed38d), and [`89ffd99b`](https://github.com/teamleaderleo/codex/commit/89ffd99b81e872e3a961767e67fb8ec410df7eae);
- the rejected call-ID-prefix feasibility prototype [`cffcd8dc`](https://github.com/teamleaderleo/codex/commit/cffcd8dca93ab5c2ff8fa1af262ae7676f5b97a9);
- the final selected contract and evidence index in [`../coordination-status.md`](../coordination-status.md).

Raw private rollout logs, desktop session metadata, process listings, machine-specific paths, image data, and the original one-off local analysis script are intentionally absent from the public fork.

## Chronological reconstruction

### 1. The original user-visible symptom

**Directly preserved evidence.** The investigation began after two Playwright command groups from an earlier Codex Desktop task were found still alive on macOS days after the task had apparently finished. The preserved incident summary records that the process groups had been adopted by PID 1, and that persisted Codex process metadata tied them to the same conversation and commands. It also records the observed Desktop bundle, platform, and the three nested operations involved: desktop screenshot, mobile screenshot, and `curl`. See [`../README.md`](../README.md), especially “Confirmed incident”.

**Reliable recollection.** The immediate user-facing concern was not initially phrased as “lost model-visible control information”. It appeared as unexplained long-lived browser/Node work and substantial resource use after a screenshot task had completed. The first questions were therefore operational: what launched the processes, whether they were still doing useful work, whether they were safe to terminate, and whether the current application version still exhibited the same problem.

**Reliable recollection.** Early process inspection separated several measurements and identities that were initially easy to conflate:

- the top-level shell or Node command versus Chromium descendants;
- resident memory versus broader process footprint and swapped memory;
- PID versus process-group ID;
- the current parent process versus the original launcher;
- the command's working directory versus proof of which product launched it;
- a process being adopted by PID 1 versus proof that graceful shutdown had failed.

The precise process-table commands and outputs are not retained. No exact memory values, PIDs, paths, or command lines are reproduced here.

### 2. Locating the relevant session and JSONL

**Reliable recollection.** The process investigation was narrowed by correlating safe pieces of local metadata rather than searching every Desktop log indiscriminately. The sequence was approximately:

1. inspect command text, start time, parent, process group, working directory, and child relationships for the surviving process groups;
2. identify matching persisted Codex process/session records;
3. use the associated conversation or thread identity to locate the corresponding local session/rollout JSONL;
4. search only the timestamp window and command markers associated with the screenshot attempt;
5. map nearby cell, nested-tool-call, wait, completion, and process records into one timeline.

**Directly preserved evidence.** The resulting correlation is summarised without private identifiers in [`../README.md`](../README.md): the two Playwright commands belonged to the same code-mode cell and conversation; the first attempt was later replaced by a different URL; the original sessions were never terminated; and the process groups remained alive after owner loss. The privacy boundary for this evidence is recorded in [`../decision-log.md`](../decision-log.md), “Evidence provenance”.

**Missing evidence.** The following are not present in the fork:

- the exact local session and rollout file paths;
- the conversation/thread identifier used to find them;
- the persisted registry rows;
- the original process-table snapshot;
- the exact command used to locate or filter the JSONL.

Reconstructing those details would require an export from the original machine or chat. Any export should be scrubbed of prompts, user data, tokens, URLs, image data, machine paths, and unrelated conversation content before being shared.

### 3. Temporary scripts, filters, and searches

**Reliable recollection.** The local JSONL was too large and sensitive to inspect by printing whole records. A one-off schema-safe scanner was created or proposed to emit only:

- event type;
- timestamp or ordering information;
- selected cell, item, call, and process identifiers;
- field names;
- short command markers;
- nearby lifecycle records.

Long strings, encrypted fields, binary/image payloads, and unrelated message bodies were omitted or redacted. The exact source of this scanner was not retained.

**Reliable recollection.** Targeted filters then concentrated on:

- the Playwright screenshot command markers and the `curl` sibling;
- the first screenshot attempt rather than the later successful fallback;
- the code-mode cell identifier;
- nested tool-call/item identifiers;
- `wait` handling;
- unified-exec yield and process/session identifiers;
- outer `Script completed` output;
- termination or cleanup records around the same interval.

**Reliable recollection.** A first reading incorrectly concluded that no `wait` call had occurred. Reinspection found that the wait operation was present but its arguments were encoded differently from the records initially searched. This correction moved attention from “the host forgot to wait for the code cell” to “the waited cell can still become terminal after nested commands yield”.

**Directly preserved evidence.** Repository-side searches then followed the exact data path later formalised in the runtime-scout prompt: nested `tools.exec_command()` → `ExecCommandToolOutput` → JavaScript `session_id` → terminal `RuntimeResponse::Result` → outer `Script completed` → still-live manager state. That call-path assignment is preserved in [`../copy-paste-agent-prompts.md`](../copy-paste-agent-prompts.md), “Prompt 2 — Runtime data-flow scout”.

**Directly preserved evidence.** Source and history searches included these symbols and behaviours:

- [`ExecCommandToolOutput::code_mode_result`](https://github.com/teamleaderleo/codex/blob/20dafe201d91d4405eef05ecd1db0257f13a9ac8/codex-rs/core/src/tools/context.rs), which serialised `session_id: Option<i32>` alongside `output`;
- [`handle_runtime_response`](https://github.com/teamleaderleo/codex/blob/20dafe201d91d4405eef05ecd1db0257f13a9ac8/codex-rs/core/src/tools/code_mode/mod.rs), which rendered `Script completed` from the terminal runtime response without consulting manager state;
- [`ExecCommandHandler::handle_call`](https://github.com/teamleaderleo/codex/blob/20dafe201d91d4405eef05ecd1db0257f13a9ac8/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs), where `ToolInvocation::source` existed but was discarded by the baseline destructuring;
- [`UnifiedExecContext`, `ProcessStore`, and `ProcessEntry`](https://github.com/teamleaderleo/codex/blob/20dafe201d91d4405eef05ecd1db0257f13a9ac8/codex-rs/core/src/unified_exec/mod.rs);
- [`UnifiedExecProcessManager::store_process`](https://github.com/teamleaderleo/codex/blob/20dafe201d91d4405eef05ecd1db0257f13a9ac8/codex-rs/core/src/unified_exec/process_manager.rs), which retained the live process in the session manager;
- upstream history establishing intentional cross-turn persistence, recorded in [`../decision-log.md`](../decision-log.md), including openai/codex#10799 and openai/codex#14602.

### 4. What the incident logs showed

**Directly preserved evidence.** The preserved incident sequence is:

1. one code-mode JavaScript cell launched three nested commands through `Promise.all`: two Playwright screenshots and one `curl`;
2. each nested exec used a 30-second yield window;
3. the outer cell first yielded after roughly 11 seconds;
4. Codex invoked the cell wait path;
5. around the nested 30-second yield boundary, both Playwright commands returned live unified-exec session IDs internally and continued running;
6. the JavaScript selected or printed only each result's `.output`, discarding `session_id`;
7. the outer cell reported `Script completed`;
8. the agent retried the screenshot work using another URL and completed the turn;
9. no termination was issued for the first two sessions;
10. the associated macOS process groups remained alive after owner loss.

This sequence is preserved in [`../README.md`](../README.md) and [`../patch-1-live-session-summary.md`](../patch-1-live-session-summary.md).

**Reliable recollection.** The investigation distinguished two screenshot attempts. The orphaned groups belonged to the first attempt, while the later fallback succeeded. This prevented the successful fallback from being mistaken for proof that the original commands had completed or been cleaned up.

**Reliable recollection.** The local records exposed logical unified-exec session/process IDs but did not provide a reliable persisted OS PID for later recovery. The OS process table separately showed the surviving process groups and descendants. This distinction helped split the work into Patch 1 visibility and a separate macOS owner-loss/recovery family. The preserved macOS research handoff records the same limitation: logical records existed, but the Desktop registry did not retain a usable OS PID for safe reclamation. See [`../patch-3-macos-orphan-recovery.md`](../patch-3-macos-orphan-recovery.md).

**Inference.** The absence of a nearby terminal cleanup event did not by itself prove a defect in ordinary turn completion, because upstream intentionally preserves unified-exec background terminals. The evidence proved that sessions remained live and became undisclosed; it did not prove that ordinary cell or turn completion was required to kill them. That distinction was confirmed by source/history review rather than by the private logs alone. See [`../decision-log.md`](../decision-log.md), “Existing intended behaviour”.

## What we initially thought

### A broad “process leak” or memory problem

**Reliable recollection.** The first framing was broad: stale browser/Node process groups were consuming resources after a task, so the problem looked like a process or memory leak in Desktop. That description was useful for discovery but too imprecise for Patch 1. No evidence showed unreachable allocated memory, so the final documentation deliberately uses “orphaned live process”, “resource leak risk”, and “lost control-handle visibility” instead. This terminology rule is preserved in [`README.md`](README.md).

### The processes might not belong to Codex

**Reliable recollection.** Working-directory and command clues initially left open whether the processes were launched manually, by an IDE, by another automation system, or by Codex. Parentage alone could not resolve that because the original owner had exited and the groups had been adopted by PID 1.

**Evidence that changed the view.** Persisted Codex process/session metadata and the matching rollout timeline associated the commands with the same conversation and code-mode work. The public fork preserves only the scrubbed conclusion, not the identifying rows. See [`../README.md`](../README.md).

### The current release might still reproduce an old cleanup problem

**Reliable recollection.** The surviving processes had started before a later application update. The investigation therefore stopped treating their existence as proof that the then-current release still reproduced the owner-loss problem. A clean launch/quit reproduction would have been required for that claim.

**Missing evidence.** No controlled current-Desktop relaunch/force-quit matrix was preserved for Patch 1. That belongs to the deferred macOS recovery family.

### The cell might never have been waited

**Reliable recollection.** The first JSONL pass missed the wait operation. A second pass found it under a different encoding. That false lead was discarded.

### The browser work might merely have been slow but still attached

**Reliable recollection.** Process state, process-group separation, adoption by PID 1, and the elapsed time since the original turn ruled out a simple “still completing normally under the original owner” interpretation. However, these facts supported owner loss, not the narrower Patch 1 diagnosis by themselves.

## What the system was actually doing

### Nested unified exec returned a copied control handle

**Directly preserved evidence.** At the baseline, `ExecCommandToolOutput::code_mode_result` constructed a JavaScript-visible object containing fields including `exit_code`, `session_id`, and `output`. The `session_id` value was copied from `process_id`; it was not an ownership-bearing Rust handle. See the baseline [`context.rs`](https://github.com/teamleaderleo/codex/blob/20dafe201d91d4405eef05ecd1db0257f13a9ac8/codex-rs/core/src/tools/context.rs).

### The manager, not JavaScript, owned the live process

**Directly preserved evidence.** Unified exec stored an `Arc<UnifiedExecProcess>` in `ProcessEntry` inside the session-level `ProcessStore`. JavaScript received only the numeric logical ID. Dropping or projecting away the JavaScript object did not remove the manager entry or terminate the process. The ownership transition and its consequences are recorded in [`../decision-log.md`](../decision-log.md), “Confirmed ownership boundary”.

### Persistence was intentional

**Directly preserved evidence.** Upstream history explicitly preserved unified-exec processes across turns and preserved background terminals on interrupt, with explicit cleanup separated into `/stop`. The relevant upstream PRs and merge commits are recorded in [`../decision-log.md`](../decision-log.md). Therefore “the process remains alive after a turn” was not, by itself, the Patch 1 defect.

### The terminal outer status was blind to manager state

**Directly preserved evidence.** The baseline `handle_runtime_response` derived status only from `RuntimeResponse`: yielded → `Script running`, terminated → `Script terminated`, successful result → `Script completed`, failed result → `Script failed`. It truncated emitted code-mode content and then prepended that status. It did not query the unified-exec manager for still-live sessions. See baseline [`code_mode/mod.rs`](https://github.com/teamleaderleo/codex/blob/20dafe201d91d4405eef05ecd1db0257f13a9ac8/codex-rs/core/src/tools/code_mode/mod.rs).

### Typed creator-cell information existed but was not retained

**Directly preserved evidence.** `ToolCallSource::CodeMode` already carried `cell_id` and `runtime_tool_call_id`, but baseline `ExecCommandHandler::handle_call` destructured the invocation without preserving `source`. `UnifiedExecContext` and `ProcessEntry` had no creator-cell field. See baseline [`tools/context.rs`](https://github.com/teamleaderleo/codex/blob/20dafe201d91d4405eef05ecd1db0257f13a9ac8/codex-rs/core/src/tools/context.rs), [`exec_command.rs`](https://github.com/teamleaderleo/codex/blob/20dafe201d91d4405eef05ecd1db0257f13a9ac8/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs), and [`unified_exec/mod.rs`](https://github.com/teamleaderleo/codex/blob/20dafe201d91d4405eef05ecd1db0257f13a9ac8/codex-rs/core/src/unified_exec/mod.rs).

## Distinguishing expected behaviour from actual behaviour

### Expected behaviour

**Inference, grounded in preserved policy and API.** A background terminal may intentionally remain alive across a cell, turn, or interrupt. But while it remains live, the model needs a session ID to poll, inspect, send input, or terminate it. Direct unified-exec output already treats a live process ID as model-facing control state, and code mode already includes the same ID in the nested JSON result. See [`../decision-log.md`](../decision-log.md), “Existing code patterns reused”.

**Selected Patch 1 expectation.** If terminal code-mode JavaScript discards a still-live nested session ID, the outer terminal status should restore visibility by listing the surviving IDs created by that completing cell. It should not terminate the sessions. The public before/after contract is preserved in [`../publication-drafts/standalone-issue.md`](../publication-drafts/standalone-issue.md).

### Actual behaviour

**Directly preserved evidence.** JavaScript could reduce the nested result to `.output`; the cell could return successfully; the outer result would say `Script completed`; and the session-level manager would continue owning the process. The model received no remaining ID. The immutable negative test at [`7298dcf4`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5) reproduced exactly that state.

## Discarded hypotheses

### 1. “Ordinary process persistence is the bug”

**Discarded.** Upstream deliberately preserves background terminals across turns and interrupts. Automatic termination would change product policy and could break servers, watchers, and interactive work. Sources: [`../decision-log.md`](../decision-log.md), openai/codex#10799, and openai/codex#14602.

### 2. “JavaScript dropping the result object should release the process”

**Discarded.** JavaScript holds a copied integer ID, while the process manager owns an `Arc` to the live process. Object lifetime in JavaScript does not control manager ownership. Source: [`../decision-log.md`](../decision-log.md), “Confirmed ownership boundary”.

### 3. “Add the warning to nested `.output`”

**Discarded for Patch 1.** It would alter the raw-output field and still depend on JavaScript printing or retaining that field. JavaScript could discard the entire result. Source: [`../decision-log.md`](../decision-log.md), “Alternatives considered”.

### 4. “Inspect only values retained or emitted by JavaScript”

**Discarded.** It misses the confirmed failure because the relevant handle is deliberately projected away. Sources: [`../patch-1-live-session-summary.md`](../patch-1-live-session-summary.md) and [`../decision-log.md`](../decision-log.md).

### 5. “Add a second per-cell live-session registry in code mode”

**Discarded.** A second registry would duplicate manager liveness, add cleanup and race obligations, and risk disagreement with the existing process store. The process manager was selected as the liveness source of truth. Source: [`../decision-log.md`](../decision-log.md).

### 6. “Encode ownership in nested call-ID text”

**Useful prototype, rejected contract.** Prototype [`cffcd8dc`](https://github.com/teamleaderleo/codex/commit/cffcd8dca93ab5c2ff8fa1af262ae7676f5b97a9) prefixed nested call IDs with the cell ID, listed manager processes, and filtered by `starts_with`. It proved that the response boundary and untruncated status placement worked. It was rejected because unrestricted cell strings could collide, cell IDs would leak into tracing/identifiers, and a naming convention would become an ownership API. Source: [`../decision-log.md`](../decision-log.md), “Feasibility prototype”.

### 7. “Change the JavaScript schema or require explicit persistence opt-in”

**Deferred.** Both approaches require compatibility and product-policy decisions. Existing scripts already receive `session_id`; Patch 1 could restore visibility without changing that schema. Source: [`../decision-log.md`](../decision-log.md).

### 8. “Block completion or terminate sessions when a hidden subagent completes”

**Deferred to a separate planning family.** Hidden-subagent ownership is a genuine policy question, but it is broader than restoring lost IDs. See [`../patch-2-subagent-yielded-cell-cleanup.md`](../patch-2-subagent-yielded-cell-cleanup.md).

### 9. “Solve macOS owner loss in the same patch”

**Deferred to a separate planning family.** macOS lacks the Linux parent-death path, and safe recovery requires owner identity, PID/PGID reuse protection, and crash semantics. See [`../patch-3-macos-orphan-recovery.md`](../patch-3-macos-orphan-recovery.md).

### 10. “The successful retry proves the first attempt ended”

**Discarded.** The retry used another URL and was a separate operation. The original groups and logical sessions remained. This distinction is part of the preserved incident summary in [`../README.md`](../README.md).

## Evidence that changed the diagnosis

| Transition | Evidence | Resulting understanding |
|---|---|---|
| Resource symptom → real surviving commands | Process groups remained under PID 1 and matched persisted Codex metadata. [`../README.md`](../README.md) | The issue was not just stale UI text or a completed browser child record. |
| Ambiguous launcher → same Codex conversation | Matching process/session metadata and rollout timeline. [`../README.md`](../README.md) | The commands were attributable to the original code-mode work, while private identifiers stayed unpublished. |
| Missing wait hypothesis → terminal cell after nested yields | Reinspection found the wait call; preserved timeline records outer yield, wait, nested 30-second yields, then completion. [`../README.md`](../README.md) | The critical boundary was nested exec yield followed by terminal cell completion. |
| Cleanup-only diagnosis → intentional persistence plus hidden controls | Upstream persistence history and manager ownership. [`../decision-log.md`](../decision-log.md) | The process staying alive was expected; losing its model-visible ID was not. |
| JavaScript ownership hypothesis → copied handle | Baseline `code_mode_result` plus manager `ProcessEntry`. [`context.rs`](https://github.com/teamleaderleo/codex/blob/20dafe201d91d4405eef05ecd1db0257f13a9ac8/codex-rs/core/src/tools/context.rs), [`unified_exec/mod.rs`](https://github.com/teamleaderleo/codex/blob/20dafe201d91d4405eef05ecd1db0257f13a9ac8/codex-rs/core/src/unified_exec/mod.rs) | Discarding the JSON field did not alter process lifetime. |
| General warning idea → exact terminal-cell lookup | Baseline `ToolCallSource::CodeMode` existed, but the handler dropped it. [`exec_command.rs`](https://github.com/teamleaderleo/codex/blob/20dafe201d91d4405eef05ecd1db0257f13a9ac8/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs) | Creator-cell metadata had to be retained on the stored process. |
| Call-ID-prefix prototype → typed attribution | Prototype worked but had collision and representation risks. [`cffcd8dc`](https://github.com/teamleaderleo/codex/commit/cffcd8dca93ab5c2ff8fa1af262ae7676f5b97a9), [`../decision-log.md`](../decision-log.md) | Preserve typed `CellId`; keep call IDs opaque. |
| Plausible diagnosis → executable baseline proof | Negative test [`7298dcf4`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5) passed on baseline. | The hidden-live-session state no longer depended on the private incident logs. |
| “Some live IDs” → exact ownership contract | Two-cell acceptance added in [`0ba57a73`](https://github.com/teamleaderleo/codex/commit/0ba57a73ea5895883a21aeb88e923d75a74ed38d). | A completing cell must not disclose another cell's process IDs. |

## The point at which the diagnosis narrowed

**Inference supported by preserved evidence.** The decisive point was the combination of three findings:

1. background persistence was explicitly intentional;
2. the manager retained the process independently of JavaScript;
3. the outer terminal status did not query manager state and the baseline did not retain creator-cell identity on process entries.

At that point, Patch 1 stopped being “make sure screenshot processes die” and became:

> Preserve existing background-process lifetime, but restore model-visible control information when a terminal code-mode cell has discarded copied session IDs.

This wording is consistent across [`../decision-log.md`](../decision-log.md), [`../workflow-retrospective-2026-07-26.md`](../workflow-retrospective-2026-07-26.md), and the unpublished [`../publication-drafts/standalone-issue.md`](../publication-drafts/standalone-issue.md).

The abrupt-owner-loss/macOS orphan problem remained real but separate. Patch 1 neither proves nor fixes that path.

## From diagnosis to executable reproduction

### Designing the first negative proof

**Directly preserved evidence.** Agent 2's initial assignment required the smallest regression test that would:

- run two nested commands in `Promise.all`;
- make each command live long enough to yield;
- deliberately retain only `output`;
- allow the outer cell to complete;
- prove two manager-owned sessions remained live;
- prove the outer status omitted them;
- terminate all spawned processes even after an assertion panic.

The assignment is preserved in [`../agent-2-test-runtime-prompt.md`](../agent-2-test-runtime-prompt.md).

**Directly preserved evidence.** Commit [`7298dcf4`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5) implemented the negative test `code_mode_completion_does_not_surface_discarded_live_exec_sessions` using:

```js
const outputs = (await Promise.all([
  tools.exec_command({ cmd: "printf orphan-a; sleep 60", yield_time_ms: 250 }),
  tools.exec_command({ cmd: "printf orphan-b; sleep 60", yield_time_ms: 250 }),
])).map(({ output }) => output);
text(outputs.join("|"));
```

The test then:

- queried `list_background_terminals()` and required two distinct live sessions;
- inspected the next model request and required `Script completed`;
- required the status not to contain session information;
- required emitted output `orphan-a|orphan-b`;
- used `catch_unwind` plus explicit terminal cleanup and a post-cleanup manager check.

**Directly preserved evidence.** The negative test passed on the Linux aarch64 Lima runner: `1 passed; 0 failed; 0 ignored`. The preserved branch, commit, and result are recorded in [`../coordination-status.md`](../coordination-status.md) and the later runtime report [`../agent-2-test-runtime-report.md`](../agent-2-test-runtime-report.md).

**Inference.** This test was intentionally a negative proof: passing meant the baseline bug was present. Keeping it immutable allowed later positive tests to evolve without erasing the clean baseline demonstration.

**Limitation.** The first version used Unix shell commands and was ignored on Windows. It was deterministic enough for the selected runner, but not a platform-complete proof of all backends.

## How the acceptance contract evolved

### Stage 1: convert the negative proof into positive behavioural coverage

**Directly preserved evidence.** Commit [`528171c7`](https://github.com/teamleaderleo/codex/commit/528171c72c06d8be3471752322b7755a1eac3ac8) changed the primary test from “IDs are absent” to “both live IDs appear exactly once in numeric order”. It also added:

- one-survivor coverage;
- large-output/truncation coverage;
- ordinary yielded-cell neutrality;
- shared cleanup helpers.

**Issue discovered.** This initial acceptance version contained assertions that were stricter than the product contract. In particular, it expected the old `Script completed` → `Wall time` adjacency even though the new warning was intentionally inserted between them, and its large-output check assumed a particular retained prefix. The retrospective records the first mismatch explicitly. See [`../workflow-retrospective-2026-07-26.md`](../workflow-retrospective-2026-07-26.md), “A test assertion initially contradicted the selected output contract”.

### Stage 2: align assertions with independent invariants

**Directly preserved evidence.** Commit [`0ba57a73`](https://github.com/teamleaderleo/codex/commit/0ba57a73ea5895883a21aeb88e923d75a74ed38d) separated the completion prefix, live-session summary, and wall-time line. It also made the one-survivor timing less fragile and added the two-cell creator-isolation case.

This changed the contract from “the header contains these numbers somewhere” to:

- the result begins with the correct terminal status;
- the live-session summary appears before wall time;
- expected IDs appear once and in numeric order within that summary;
- unrelated process IDs are absent.

### Stage 3: stop asserting an incidental truncator representation

**Directly preserved evidence.** Commit [`89ffd99b`](https://github.com/teamleaderleo/codex/commit/89ffd99b81e872e3a961767e67fb8ec410df7eae) relaxed the large-output assertion. The truncator could preserve a head/tail excerpt or an omission marker; the behavioural requirement was only that emitted output remain represented separately from the untruncated status header.

### Stage 4: final repository-conventions polish

**Directly preserved evidence.** Later test-only work moved the five cases into the aggregate code-mode suite, reused parent helpers, wrapped the process-creating submission itself in panic-safe cleanup, replaced fixed sleeps with a bounded deterministic exit handshake, added a network-independent manager query unit test, and stopped pinning exact content-item cardinality. The final state and receipts are indexed in [`../coordination-status.md`](../coordination-status.md). The final approved clean candidate is [`76021678`](https://github.com/teamleaderleo/codex/commit/760216784efaee1ba6a3b1250349f31d5f91c7ca).

The final five behavioural contracts were:

1. multiple discarded live sessions are reported in deterministic numeric order;
2. exited sessions are excluded;
3. the warning remains separate from emitted-output truncation;
4. ordinary yielded responses do not contain the terminal-only warning;
5. only sessions created by the completing cell are reported.

## Why exact creator-cell attribution became necessary

### The manager could answer liveness but not origin

**Directly preserved evidence.** At baseline, the manager knew process ID, tool call ID, cwd, session, and live process object, but `ProcessEntry` had no creator code-mode cell. `ToolInvocation` already carried `ToolCallSource::CodeMode { cell_id, ... }`; `ExecCommandHandler` dropped it. See the baseline files linked above and [`../decision-log.md`](../decision-log.md), “Current metadata gap”.

### “List all live processes” was too broad

**Inference.** A conversation can legitimately contain background terminals from earlier cells, direct tool calls, or other work. Reporting every live manager entry at each code-cell completion would disclose unrelated sessions and make the warning misleading.

### Call-ID text was not a safe ownership model

**Directly preserved evidence.** The prefix prototype demonstrated feasibility but failed the ownership review. Cell IDs are unrestricted strings; prefix matching can collide; and embedding cell IDs in call IDs changes identifiers and traces. Source: [`../decision-log.md`](../decision-log.md), “Feasibility prototype”.

### The two-cell case made the requirement executable

**Directly preserved evidence.** The two-cell test added in [`0ba57a73`](https://github.com/teamleaderleo/codex/commit/0ba57a73ea5895883a21aeb88e923d75a74ed38d) left a process from Cell A alive, then completed Cell B with another live process. It required Cell B's summary to contain only Cell B's process ID and explicitly exclude Cell A's ID.

**Inference.** This test turned creator attribution from an implementation preference into a behavioural requirement. Exact typed identity was the smallest reliable way to satisfy it without parsing output or redesigning the public protocol.

## Major hypotheses and their final status

| Hypothesis | Status | Evidence |
|---|---|---|
| Ordinary turn completion should kill every yielded exec | Rejected for Patch 1 | Persistence policy in [`../decision-log.md`](../decision-log.md) |
| The JavaScript result owns the process | Rejected | Manager `Arc` ownership and copied `session_id` |
| The host never waited for the cell | Rejected after log reinspection | Reliable recollection; raw excerpt missing |
| The successful fallback was the original process finishing | Rejected | Preserved incident sequence in [`../README.md`](../README.md) |
| Manager state was stale while OS processes were gone | Rejected for the incident | Manager records plus live PID-1 process groups; private raw correlation not retained |
| Add warning to nested output | Rejected | Still discardable by JavaScript |
| Observe only emitted JavaScript values | Rejected | Confirmed failure deliberately discards the handle |
| Add a second code-mode liveness registry | Rejected | Duplicates manager state and cleanup obligations |
| Encode cell ownership in call IDs | Prototype only; rejected | [`cffcd8dc`](https://github.com/teamleaderleo/codex/commit/cffcd8dca93ab5c2ff8fa1af262ae7676f5b97a9) and [`../decision-log.md`](../decision-log.md) |
| Retain typed creator cell on manager entry | Selected | Existing `ToolCallSource::CodeMode`, exact two-cell requirement |
| Auto-terminate hidden-subagent sessions | Deferred planning family | [`../patch-2-subagent-yielded-cell-cleanup.md`](../patch-2-subagent-yielded-cell-cleanup.md) |
| Add macOS crash recovery | Deferred planning family | [`../patch-3-macos-orphan-recovery.md`](../patch-3-macos-orphan-recovery.md) |
| Delayed cross-turn dispatch is another confirmed bug | Not confirmed | Static finding only; [`../coordination-status.md`](../coordination-status.md) |

## Evidence that is directly preserved

The following can be reviewed without access to the original machine:

- scrubbed incident chronology: [`../README.md`](../README.md);
- Patch 1 design space and initial regression requirements: [`../patch-1-live-session-summary.md`](../patch-1-live-session-summary.md);
- intended persistence policy, ownership model, metadata gap, prototype rejection, and alternatives: [`../decision-log.md`](../decision-log.md);
- baseline source at `20dafe201d91d4405eef05ecd1db0257f13a9ac8`;
- negative proof: [`7298dcf4`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5);
- initial positive acceptance: [`528171c7`](https://github.com/teamleaderleo/codex/commit/528171c72c06d8be3471752322b7755a1eac3ac8);
- contract and two-cell correction: [`0ba57a73`](https://github.com/teamleaderleo/codex/commit/0ba57a73ea5895883a21aeb88e923d75a74ed38d);
- truncation correction: [`89ffd99b`](https://github.com/teamleaderleo/codex/commit/89ffd99b81e872e3a961767e67fb8ec410df7eae);
- rejected prefix prototype: [`cffcd8dc`](https://github.com/teamleaderleo/codex/commit/cffcd8dca93ab5c2ff8fa1af262ae7676f5b97a9);
- final selected contract and clean candidate index: [`../coordination-status.md`](../coordination-status.md);
- runtime results for the investigation implementation: [`../agent-2-test-runtime-report.md`](../agent-2-test-runtime-report.md).

## Remaining evidentiary gaps

### Raw private incident evidence

**Missing evidence.** The fork does not contain the raw session JSONL, Desktop registry, process table, screenshots, prompts, URLs, environment, or user data. This is intentional. Without the original machine export, this reconstruction cannot provide exact:

- file names or sizes;
- line numbers in the JSONL;
- process IDs or process-group IDs;
- timestamps beyond the scrubbed approximate sequence;
- machine paths;
- scanner script source;
- filter commands;
- raw event payloads.

### Exact log-location procedure

**Missing evidence.** The high-level method is reliably recalled, but the exact lookup commands and registry schema fields were not preserved. A future evidence export should include a scrubbed map such as:

```text
process-group evidence → persisted logical process record → conversation/thread identifier → rollout file → selected event IDs
```

It should omit all unrelated content.

### Independent reproduction of macOS owner loss

**Missing evidence for Patch 1.** The original incident showed owner-loss persistence, but Patch 1's executable test reproduced only the visibility failure while the session manager remained alive. It did not reproduce force quit, crash, upgrade, PID-1 adoption, or restart recovery. Those claims remain in the Patch 3 research family.

### Hidden-subagent lifecycle policy

**Missing policy decision.** The incident involved hidden/subagent context, but Patch 1 did not decide whether such sessions should be killed, transferred, or block completion. Patch 2 and Patch 3 are planning labels, not promised patches.

### Current Desktop release status

**Missing evidence.** The original groups predated at least one later update. No controlled matrix proves whether the same abrupt-owner-loss behaviour exists in a newer Desktop bundle. Public Patch 1 claims should stay at the code-mode visibility layer.

## Material that could be offered privately after scrubbing

Subject to explicit human approval, the following could strengthen external review without publishing raw logs:

- a minimal chronological table of selected event types and relative timestamps;
- the three scrubbed nested command categories and yield values;
- selected cell, call, and logical process IDs replaced with consistent pseudonyms;
- a process-group table containing only relative age, PPID/PGID relationships, and state;
- the one-off JSONL scanner after removing paths, identifiers, and payload printing;
- selected registry rows with conversation, command, and machine identifiers replaced;
- a statement of which fields were intentionally omitted.

The raw chat transcript, full rollout, machine paths, tokens, image data, and unrelated user content should remain private.

## Final reconstructed diagnosis

**Directly preserved conclusion.** A terminal code-mode cell could await nested unified-exec calls until they yielded, receive copied live `session_id` values, discard those IDs by selecting only `.output`, and return successfully. The session-level unified-exec manager intentionally retained the processes, while the outer runtime rendered `Script completed` without querying manager state. Because baseline process entries did not retain typed creator-cell attribution, terminal rendering could not safely restore the matching IDs.

**Selected Patch 1 response.** Preserve typed `ToolCallSource::CodeMode` creator-cell identity through `UnifiedExecContext` into `ProcessEntry`; query the existing manager for exact-cell, live-only, numerically sorted logical IDs; and add them to terminal `Result` and `Terminated` status outside emitted-output truncation. Keep ordinary `Yielded` neutral, call IDs opaque, JavaScript `session_id` compatible, and background-process lifetime unchanged.

That diagnosis is narrower than the original operational symptom, but it is the part supported by a deterministic negative reproduction and a bounded acceptance contract.