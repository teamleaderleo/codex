# Agent 1 handoff: final Patch 1 candidate

Date: 2026-07-26

## Reconvene packet

This section is the current Agent 1 source of truth for Agent 3, Agent 4, and the human coordinator.

```text
Agent: 1 — implementation and clean-candidate lane
Upstream base: 61a44880a85d2fd0d8770908dea5733495e571c8
Approved clean candidate: 760216784efaee1ba6a3b1250349f31d5f91c7ca
Clean branch: fix/code-mode-live-session-summary-clean
Candidate history: 3 commits directly above upstream
Final verdict from Agent 1: pass
Required code change: none
Concrete contract gap: none
Public-copy correction required: none
Complete workspace test: not run
Upstream issue or PR opened: no
```

### Primary links

- Final clean comparison: https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...760216784efaee1ba6a3b1250349f31d5f91c7ca
- Approved clean head: https://github.com/teamleaderleo/codex/commit/760216784efaee1ba6a3b1250349f31d5f91c7ca
- Agent 1 implementation-conventions review: https://github.com/teamleaderleo/codex/blob/research/code-mode-orphan-handoffs/notes/code-mode-orphan-fix/final-roundtable/agent-1-implementation-conventions.md
- Detailed candidate/upstream failure inventory: https://github.com/teamleaderleo/codex/blob/research/code-mode-orphan-handoffs/notes/code-mode-orphan-fix/agent-1-clean-candidate-project-failure-inventory.md
- Agent 1 retrospective: https://github.com/teamleaderleo/stensibly/issues/246#issuecomment-5081855675
- This handoff: https://github.com/teamleaderleo/codex/blob/research/code-mode-orphan-handoffs/notes/code-mode-orphan-fix/agent-1-clean-candidate-handoff.md

## Final short contract sanity check

Static inspection of the revised tests at `760216784efaee1ba6a3b1250349f31d5f91c7ca` produced a **pass** verdict. No broad tests were rerun for this check.

The final tests clearly retain all five approved behavioural contracts:

1. multiple discarded live sessions are reported once each in deterministic numeric order;
2. exited sessions are excluded;
3. the live-session warning remains in a separate status item outside emitted-output truncation;
4. ordinary yielded responses do not contain the terminal-only warning;
5. only sessions created by the completing cell are reported.

The manager-query unit test directly covers:

- exact creator-cell matching;
- exclusion of another cell;
- exclusion of `creator_cell_id: None`;
- exclusion of exited entries;
- deterministic numeric ordering.

Public wording should describe Patch 1 as visibility-only. Preferred scope sentence:

> Terminal code-mode results disclose the IDs of still-live unified-exec sessions created by that completing cell.

Do not imply that Patch 1 terminates, cleans up, recovers, or prevents orphaned processes.

## Implementation-conventions result

Agent 1's roundtable verdict was **pass with notes**, with no required code or test changes.

- `ExecCommandHandler` is the appropriate boundary for converting existing `ToolCallSource::CodeMode` metadata into typed creator-cell identity.
- `UnifiedExecContext` is an appropriate invocation-scoped carrier.
- `ProcessEntry` is the appropriate manager-owned persistence point.
- `UnifiedExecProcessManager::live_process_ids_created_by_cell` is an appropriately narrow, read-only liveness query.
- The process-store lock is held only for bounded synchronous inspection; there is no nested `.await` while it is held.
- Naming and crate visibility are acceptable.
- Double sorting in the manager and formatter is redundant but harmless.
- The minor `with_creator_cell_id(Option<CellId>)` API-shape wart is not worth changing after validation; it is crate-private and the call site passes a named variable rather than an opaque literal.

Likely maintainer questions are non-blocking:

- whether generic unified-exec state should retain a broader origin type instead of `Option<CellId>`;
- whether the acceptance coverage could be shortened through shared helpers.

No pre-emptive rewrite is recommended.

## Validation and differential evidence

The corrected retained candidate project-run summary for the earlier clean implementation tree was:

```text
3,110 tests run
3,015 passed, including one flaky retry pass
94 failed
1 timed out
9 skipped
```

The exact upstream base was then run with the same repository-native command and equivalent hosted-runner configuration:

```text
Candidate: 3,110 run; 3,015 passed; 94 failed; 1 timed out; 9 skipped
Upstream:  3,102 run; 3,007 passed; 94 failed; 1 timed out; 9 skipped
```

Ninety-three failed-test names and the timeout were shared. The one candidate-only and one upstream-only failure both passed three of three focused runs on each ref in one shared runner and Cargo target directory. Final classification:

- environment or missing dependency: 53 outcomes;
- sandbox or runner limitation: 16 outcomes;
- known or unrelated assertions reproduced upstream: 26 outcomes;
- potentially related to Patch 1: zero;
- unclassified: zero.

The detailed inventory and raw artifact references are linked above. The original GitHub-hosted runners and their local caches are no longer available because they were ephemeral.

## Final candidate comparison summary

The approved candidate is three commits above upstream and changes eight files:

1. `codex-rs/core/src/tools/code_mode/mod.rs`
2. `codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs`
3. `codex-rs/core/src/unified_exec/mod.rs`
4. `codex-rs/core/src/unified_exec/mod_tests.rs`
5. `codex-rs/core/src/unified_exec/process_manager.rs`
6. `codex-rs/core/src/unified_exec/process_manager_tests.rs`
7. `codex-rs/core/tests/suite/code_mode.rs`
8. `codex-rs/core/tests/suite/code_mode/orphan_sessions.rs`

The later commits contain reviewed test organisation, compatibility coverage, manager-query coverage, and truncation-assertion polish. Agent 1's final sanity check found no behavioural-contract regression.

## Patch 2 and Patch 3 clarification

Patch 2 and Patch 3 were planning labels for separate follow-up families, not approved implementation contracts or promised patches.

- Patch 2 groups ownership and cleanup-policy questions, including hidden or subagent completion while live yielded work remains.
- Patch 3 groups runtime-loss and macOS orphan-recovery approaches, including durable process-group tracking, stale-process sweeps, guardians, or stronger termination reporting.

Each family requires its own executable reproduction, ownership statement, product-policy decision, issue, implementation review, and validation. The delayed cross-turn dispatch concern also remains separate and must not be described as reproduced without executable evidence.

## Reconvene instructions

Agent 3 should use:

1. the final clean comparison;
2. the integrated Agent 1 conventions review;
3. the final contract sanity-check section above;
4. Agent 2's approved test-polish evidence;
5. the matched upstream failure inventory;
6. Agent 4's publication review and the roundtable synthesis.

Agent 4 should keep public copy visibility-only and update unpublished evidence to the approved clean head. The human coordinator retains approval over upstream issue publication, PR publication, broader validation, and merge decisions.

No upstream Codex issue or pull request was opened by Agent 1.

## Historical construction record

The first clean implementation head was `3778e1fae6e7e3d885252282a7c5ce67e06730ff`, reconstructed directly on upstream `61a44880a85d2fd0d8770908dea5733495e571c8`. It passed formatting, scoped lint/fix, focused units, and the five-case acceptance target. Subsequent reviewed commits reorganised the integration test into the existing code-mode suite and added the final manager-query and compatibility coverage now present at `760216784efaee1ba6a3b1250349f31d5f91c7ca`.
