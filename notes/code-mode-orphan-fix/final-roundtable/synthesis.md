# Final Patch 1 roundtable synthesis

Date: 2026-07-26

Reviewed base: `61a44880a85d2fd0d8770908dea5733495e571c8`

Reviewed candidate: `3778e1fae6e7e3d885252282a7c5ce67e06730ff`

## Inputs

- Agent 1: implementation conventions — pass with notes.
- Agent 2: testing conventions — change requested.
- Agent 3: architecture and API conventions — pass with non-blocking notes.
- Agent 4: publication conventions — pass with notes.

## Overall verdict

**Production implementation: pass.**

**Test packaging and robustness: one test-only revision requested before publication.**

No reviewer identified a production-code defect, lifecycle-policy expansion, public protocol change, ownership-boundary error, liveness-authority error, or clean-history problem.

The only requested change is to bring the five acceptance cases into the repository's established aggregated integration-test structure and remove several avoidable test fragilities. The clean production files should remain unchanged.

## Consensus production findings

The four lanes agree that:

- `ExecCommandHandler` is the correct boundary for translating nested code-mode source metadata into process-creation metadata;
- `UnifiedExecContext` is an appropriate transient carrier;
- `ProcessEntry` is the correct durable attribution record for manager-owned live processes;
- `UnifiedExecProcessManager` is the sole liveness authority;
- `live_process_ids_created_by_cell` is narrow, read-only, exact-cell, live-only, deterministically ordered, and crate-private;
- terminal model-facing wording belongs in code mode rather than the general process manager;
- `Yielded` remains completion-neutral;
- the JavaScript schema, nested call IDs, persistence, pruning, termination, shutdown, interrupt, dispatch, and recovery policy remain unchanged;
- the one-commit clean history is appropriate.

No production-code modification is requested.

## Non-blocking production notes

These are plausible maintainer questions, not pre-publication change requests:

1. `ToolCallSource::CodeMode` stores the cell identity as a string before `ExecCommandHandler` reconstructs `CellId`. A broader typed-source cleanup would widen this patch unnecessarily.
2. `UnifiedExecContext::with_creator_cell_id(Option<CellId>)` is a small API-shape wart because repository guidance discourages ambiguous `Option` parameters. The current named-variable callsite is readable and crate-private; changing it now would be churn.
3. IDs are sorted by both the manager query and formatter. The duplicate sorting is harmless and keeps formatter unit tests deterministic.
4. A future generic process-origin model may be useful, but `Option<CellId>` is the narrowest representation required by Patch 1.

## Test-conventions finding

Agent 2's change request is accepted as substantive rather than cosmetic.

Independent verification found:

- `codex-rs/core/tests/all.rs` explicitly defines a single integration test binary;
- `codex-rs/core/tests/suite/mod.rs` aggregates the suite and already registers `code_mode`;
- the standalone `codex-rs/core/tests/code_mode_orphan_sessions.rs` file creates a second integration target;
- it duplicates `custom_tool_output_items`, `text_item`, and code-mode turn setup already present in `tests/suite/code_mode.rs`;
- four tests submit the turn before entering the panic-safe cleanup body, so a submission error after process creation can bypass cleanup;
- the one-survivor case uses fixed process sleeps rather than a bounded or deterministic state transition;
- the yielded-response assertion scans every numeric token rather than asserting directly that the completion-only warning is absent.

The repository guidance also asks test authors to use existing helpers and prefer integration tests under the existing core suite.

## Required test-only revision

Agent 2 should prepare, on a separate branch based on the clean candidate, a test-only patch that:

1. removes the standalone `codex-rs/core/tests/code_mode_orphan_sessions.rs` integration target;
2. places the five acceptance cases in a focused child module of the existing code-mode suite, preferably:
   - `codex-rs/core/tests/suite/code_mode/orphan_sessions.rs`,
   - registered from `codex-rs/core/tests/suite/code_mode.rs`;
3. reuses the parent code-mode helpers instead of duplicating response extraction and turn setup;
4. wraps turn submission and all process-creating setup inside cleanup protection;
5. replaces the yielded numeric-token scan with a direct absence assertion for `Background sessions still running:`;
6. replaces the fixed one-second/two-second race with bounded polling or another deterministic completion handshake;
7. preserves the same five behavioural contracts and does not alter production code.

The preferred child-module shape avoids growing the already large `code_mode.rs` while still using the aggregate integration binary and existing helpers.

## Validation required for the test-only revision

Run only:

- `just fmt`;
- `just fix -p codex-core` if the revised Rust files require it;
- the three affected code-mode unit tests;
- the five revised acceptance cases through the aggregated `all` test binary;
- `git status --short`;
- `git diff --check`.

No new full workspace run or broad matched-base run is requested unless the focused revision exposes a concrete differential failure.

The prior broad-suite classification remains: baseline/environment-limited and not green.

## Review ownership after the test-only patch

- Agent 2 owns preparation and focused validation of the test-only branch.
- Agent 3 will review the resulting test diff and validation receipt.
- Agent 1 should receive only a short final sanity check that the revised tests still express the intended implementation contract; a new full implementation review is unnecessary.
- Agent 4 should wait for the final clean head, then update the unpublished issue and PR drafts. Agent 4 does not need to reread every lane review.

Do not modify the current clean branch directly until the test-only patch is reviewed and accepted.

## Public-copy corrections

The final issue should remain problem-led and concise.

The final PR should explain:

- typed creator-cell attribution;
- the process manager as the sole liveness source;
- exact-cell, live-only, read-only lookup;
- terminal-only reporting and yielded neutrality;
- unchanged lifecycle and JavaScript schema.

Validation wording must say:

- repository-native format and scoped fix passed;
- focused unit tests passed;
- five acceptance cases passed;
- the broad `codex-core` suite was red on both candidate and exact upstream base;
- no persistent candidate-only failure remained;
- the complete workspace suite was not run.

Do not claim that the broad project suite or workspace suite passed.

Patch 2 and Patch 3, agent identities, research ancestry, machine paths, raw logs, and internal review artifacts should be omitted from public copy.

## Deferred follow-up register

The following remain internal, separate, and uncommitted:

- generic process-origin modelling;
- hidden or subagent ownership and cleanup policy;
- process persistence or automatic termination policy;
- unreproduced cross-turn dispatch behaviour;
- shutdown/store-after-drain races;
- remote bulk-termination confirmation;
- natural-exit stale bookkeeping;
- event-driven wake-up after process or subagent completion;
- macOS or runtime-loss orphan recovery;
- reusable background-terminal cleanup guards;
- reusable repository-native validation profiles.

Patch 2 and Patch 3 are planning-family labels only. Each future item requires its own executable reproduction, ownership statement, policy decision, issue, implementation review, and validation.

## Human decisions remaining

After the test-only revision is reviewed:

1. approve final issue and PR wording;
2. approve issue-first-then-PR publication order;
3. approve the exact publication moment;
4. decide whether any additional complete workspace validation is worth its cost;
5. confirm a final related-issue refresh if upstream has moved.
