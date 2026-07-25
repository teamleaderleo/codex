# Code-mode orphan fix: coordination status

Last updated: 2026-07-26
Baseline: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`

## How to use this file

This is the canonical cross-agent status page for the code-mode orphan investigation.

- Every agent should read this file before starting or resuming work.
- The integrator owns updates to this file so parallel agents do not conflict while editing it.
- Each agent should keep detailed work in its own report file or implementation branch, then leave a compact handoff containing: branch/ref, changed files, tests run, blockers, and decisions needed.
- Do not overwrite another agent's report.
- GitHub has no branch-level comment thread. Use a PR review when a PR exists; otherwise record branch reviews here.
- Keep implementation branches based on the recorded baseline unless a rebase is deliberate and documented.

## Current decisions

1. Patch 1 is visibility-only. It must not terminate background sessions or change intended cross-turn persistence.
2. The unified-exec process manager is the source of truth for whether a session remains live.
3. Nested processes should retain typed creator attribution from `ToolCallSource::CodeMode { cell_id, ... }` rather than deriving ownership from JavaScript output or parsing call-ID strings.
4. Keep the JavaScript-visible `session_id` schema compatible.
5. Surface surviving session IDs in the outer status/header after output truncation.
6. Prefer reporting the summary on terminal cell outcomes (`Result`, failure, and explicit termination). A yielded cell is still actively running and normally should not receive a completion-oriented warning.
7. The regression must deliberately discard the nested `session_id` fields and prove that the outer result still discloses both live sessions.

## Agent status

### Agent 1 / integrator prototype

Branch: `fix/code-mode-live-session-summary`

State:

- Three commits ahead of the baseline.
- Changes only `codex-rs/core/src/tools/code_mode/mod.rs`.
- Adds status formatting and live-process lookup.
- Has not yet been validated with the full regression test.

What is worth keeping:

- Querying the live process manager at the outer response boundary.
- Sorting reported IDs.
- Putting the warning in the status header so output truncation cannot erase it.
- Preserving the JavaScript result schema and process persistence policy.

Required revision before treating it as the implementation:

- Do not encode ownership as `exec-cell-<cell_id>-...` and recover it with `starts_with`. `CellId` is an unrestricted string, so prefixes can collide (`1` versus `1-x`) and arbitrary IDs leak into tool-call identifiers and tracing.
- Carry the existing `ToolCallSource::CodeMode` cell identity into unified exec and store creator attribution on the process entry.
- Query by typed creator cell ID.
- Do not add the background-session line to ordinary `Yielded` responses.
- Add the integration regression; current unit coverage proves formatting only.
- Cover terminal success, terminal failure, explicit termination, output truncation, one-of-two processes exiting, and sorted IDs.

Review verdict: useful prototype and formatter scaffolding; ownership mechanism should be replaced.

### Agent 2 / regression test

Branch: `research/code-mode-live-session-test`

State:

- One commit ahead of the baseline.
- Adds `codex-rs/core/tests/code_mode_orphan_sessions.rs`.
- Starts two nested commands with `Promise.all`, destructures only `{ output }`, proves two background terminals remain registered, proves the outer header omits their IDs, and performs cleanup even after a panic.

Value:

- This is direct executable evidence of the interface failure and should be reused as the foundation for Patch 1 validation.

Refinement needed:

- The test currently uses `printf ...; sleep 60`, is ignored on Windows, and uses the network-backed model-test harness.
- Prefer an existing cross-platform long-running helper or fixture if available.
- Convert the negative assertion into the expected positive assertion on the implementation branch.
- Keep the panic-safe teardown and final empty-process assertion.

Review verdict: important even though it is not implementation work; it turns the incident into a reproducible contract test.

### Agent 3 / ownership and API audit

State: read-only audit completed outside the repository.

Key conclusions incorporated into this file:

- Code-mode owns callback tasks, but after unified exec yields the conversation-level process manager owns the live process.
- JavaScript receives only a copied numeric handle; dropping the object has no ownership effect.
- Session shutdown and ordinary turn completion have different cleanup semantics by design.
- Typed creator-cell attribution in the process manager is the smallest reliable Patch 1 design.

Additional follow-up findings, separate from Patch 1:

- The shared code-mode dispatch receiver may allow a delayed old-cell invocation to run through a later turn worker.
- Session shutdown can race with an already-dispatched nested exec storing a process after the manager drain.
- Remote exec-server bulk termination is fire-and-forget in one path.
- Natural process exit can leave manager bookkeeping until a later refresh or removal action.

These deserve separate tests/issues rather than expansion of the visibility patch.

### Agent 4 / upstream history and issue draft

Implementation branch: `fix/macos-orphan-recovery`

State:

- The implementation branch is still identical to the baseline.
- Research was recorded in `agent-4-history-issue-report.md` on the handoff branch.
- No issue, comment, PR, or code change was published.

What is useful:

- Strong six-step statement of the bug.
- Correct distinction between intended cross-turn persistence and accidental loss of control handles.
- Good related-issue map and a usable private issue draft.
- Correct recommendation to keep macOS recovery and hidden-subagent policy separate.

Required revision before publication:

- Describe Agent 1's call-ID-prefix change as prototype feasibility evidence, not the recommended ownership contract.
- Recommend typed creator-cell attribution using the existing `ToolCallSource::CodeMode` path.
- Incorporate Agent 3's ownership analysis.
- Link a clean regression commit and a tested implementation commit rather than scratch branches where possible.
- Keep the issue focused on discarded live-session handles; put dispatch, shutdown-race, and macOS crash-recovery findings in separate follow-ups.

Review verdict: valuable issue-writing work; hold publication until the test and implementation design are consolidated.

## Recommended next sequence

1. Revise Agent 1's implementation to use typed creator-cell attribution in unified exec.
2. Bring Agent 2's regression onto that branch and change it to assert both live IDs appear in the outer terminal header.
3. Run focused unit and integration tests, including teardown and truncation cases.
4. Update Agent 4's issue draft with the tested design and Agent 3's ownership findings.
5. Decide whether to publish the issue before proposing an upstream PR, consistent with the repository working rules.
6. Track the delayed-dispatch, shutdown-race, remote-termination, and stale-bookkeeping findings as separate candidate issues.

## Handoff template

Agents should finish with this compact block in their own report or final message:

```text
Agent:
Branch/ref:
Baseline:
Changed files:
Tests run and results:
Confirmed findings:
Open risks:
Decision requested:
Recommended next action:
```
