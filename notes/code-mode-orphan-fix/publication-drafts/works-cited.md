# Patch 1 works cited

Status: public-facing draft bibliography; unpublished.

This index separates primary sources from secondary synthesis. A link appearing here does not mean every public issue or pull request should include it. The public issue should cite only the sources needed to verify the problem and expected behaviour. The pull request should cite the implementation, tests, conventions, and bounded validation. The deep dive may cite the full record.

## Citation policy

Source priority:

1. **Commit-pinned code or tests** — strongest source for what the repository contains.
2. **Executable receipts and exact comparisons** — strongest source for what was run and observed.
3. **Upstream pull requests, commits, and repository conventions** — architectural and historical context.
4. **Independent review** — useful scrutiny, but not executable proof unless subsequently verified.
5. **Investigation synthesis** — useful chronology and interpretation; concrete claims should point through to stronger evidence.
6. **Private recollection or raw local evidence** — disclose only after explicit review and scrubbing.

Git blame is a navigation tool, not an ownership oracle. Cite the commit or pull request that explains a change. Use CODEOWNERS for current review ownership.

## Canonical code state

| Source | Use |
|---|---|
| [Exact upstream base `61a44880`](https://github.com/openai/codex/commit/61a44880a85d2fd0d8770908dea5733495e571c8) | Selected base for the clean candidate and matched comparison. |
| [Final clean candidate `7602167`](https://github.com/teamleaderleo/codex/commit/760216784efaee1ba6a3b1250349f31d5f91c7ca) | Reviewed implementation and final tests. |
| [Final comparison](https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...760216784efaee1ba6a3b1250349f31d5f91c7ca) | Complete public code/test diff. |

## Primary production-code sources

### Creator-cell provenance

- [`ExecCommandHandler` captures `ToolCallSource::CodeMode` cell identity](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L132-L138).
- [`UnifiedExecContext` carries optional typed creator metadata](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L76-L99).
- [`ProcessEntry` retains creator-cell attribution beside the stored process](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L189-L199).
- [`store_process` copies invocation metadata into the manager-owned entry](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/process_manager.rs#L944-L976).

### Liveness and rendering

- [`live_process_ids_created_by_cell`: exact-cell, live-only, sorted query](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod.rs#L168-L180).
- [Terminal-only lookup and response handling](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/code_mode/mod.rs#L199-L255).
- [Status formatting and `Background sessions still running:` output](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/tools/code_mode/mod.rs#L268-L300).

## Executable reproduction and tests

### Negative proof

- [Immutable negative reproduction `7298dcf4`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5) — demonstrates that JavaScript can discard two session IDs while the manager still lists both live terminals and the outer result omits them.

### Final acceptance coverage

- [Aggregate acceptance module](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs).
- [Multiple live IDs and ordering](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs#L159-L205).
- [Exited-session exclusion with deterministic handshake](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs#L207-L282).
- [Warning placement outside code-mode emitted-output truncation](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs#L284-L352).
- [Yielded-response neutrality](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs#L354-L396).
- [Completing-cell isolation](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs#L397-L504).
- [Direct manager-query unit test](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/src/unified_exec/mod_tests.rs#L332-L395).

## Repository conventions

- [Single aggregate integration-test binary](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/all.rs#L1-L9).
- [Existing code-mode suite and child-module registration](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode.rs#L59-L77).
- [CODEOWNERS assigns `/codex-rs/core/` to `@openai/codex-core-agent-team`](https://github.com/openai/codex/blob/61a44880a85d2fd0d8770908dea5733495e571c8/.github/CODEOWNERS#L1-L10).

## Executable validation records

- [Original aggregate test-polish receipt](https://github.com/teamleaderleo/codex/blob/728e2e07462aea6505925366158b5f04644ad034/notes/code-mode-orphan-fix/agent-2-test-polish-validation-receipt.md).
- [Supplemental repository-native validation receipt](https://github.com/teamleaderleo/codex/blob/728e2e07462aea6505925366158b5f04644ad034/notes/code-mode-orphan-fix/agent-2-test-polish-supplemental-validation-receipt.md).
- [Final test-polish approval](https://github.com/teamleaderleo/codex/blob/728e2e07462aea6505925366158b5f04644ad034/notes/code-mode-orphan-fix/agent-3-final-test-polish-approval-7602167.md).
- [Matched broad project failure inventory](https://github.com/teamleaderleo/codex/blob/728e2e07462aea6505925366158b5f04644ad034/notes/code-mode-orphan-fix/agent-1-clean-candidate-project-failure-inventory.md).

Bounded public summary:

- formatting and scoped fix passed;
- four focused unit tests passed;
- five aggregate acceptance cases passed;
- two compatibility tests passed 20/20 executions on the candidate and 20/20 on the exact base;
- the matched broad `codex-core` suite was red on both refs and is not claimed green;
- no persistent candidate-only failure remained;
- the complete workspace suite was not run.

## Upstream architecture and history

| Source | Architectural relevance |
|---|---|
| [Unified execution PR #3288](https://github.com/openai/codex/pull/3288) / [commit `c09ed74a`](https://github.com/openai/codex/commit/c09ed74a163ecea69c32d61ab2bfa1c8490eb611) | Introduced PTY-backed reusable sessions, numeric session IDs, persistence, isolation, timeouts, and bounded output. |
| [Tool-system refactor PR #4510](https://github.com/openai/codex/pull/4510) / [commit `33d3ecbc`](https://github.com/openai/codex/commit/33d3ecbccca4b92cfb2a77002387de30302f337f) | Established handlers/router/registry/shared invocation boundaries. |
| [JavaScript REPL PR #10674](https://github.com/openai/codex/pull/10674) / [commit `42e22f3b`](https://github.com/openai/codex/commit/42e22f3bde6c851422eb4f7b502457fe86ba91db) | Added feature-gated persistent JavaScript execution. |
| [Code mode on V8 PR #15276](https://github.com/openai/codex/pull/15276) / [commit `e4eedd61`](https://github.com/openai/codex/commit/e4eedd6170580d5b06fb539635a78f261a6b7369) | Moved code mode from external Node execution to an in-process Rust/V8 substrate while preserving model-facing semantics. |
| [Cell actor PR #28599](https://github.com/openai/codex/pull/28599) / [commit `e2f074e1`](https://github.com/openai/codex/commit/e2f074e16c522bfa55d9bcd344a5ea0ba5a4580f) | Established the single-owner cell-lifecycle boundary. |

## Related issues

- [openai/codex#34866](https://github.com/openai/codex/issues/34866) — related prior symptom coverage involving `Script completed`, a still-live nested shell, and omitted nested result state.
- [openai/codex#32411](https://github.com/openai/codex/issues/32411) — broader loss of awaited but unemitted nested results and artifact handles.
- [openai/codex#33816](https://github.com/openai/codex/issues/33816) — model-side abandonment after a live session ID was already exposed.
- [openai/codex#14731](https://github.com/openai/codex/issues/14731), [#15723](https://github.com/openai/codex/issues/15723), and [#32188](https://github.com/openai/codex/issues/32188) — broader completion blocking, wake-up, and lifecycle/eventing questions.

The standalone issue remains justified because it defines a narrower executable contract: JavaScript discards still-live session IDs, the manager retains the processes, and terminal rendering does not restore exact creator-cell live handles.

## Rejected and deferred implementation paths

- [Call-ID-prefix feasibility prototype `cffcd8dc`](https://github.com/teamleaderleo/codex/commit/cffcd8dca93ab5c2ff8fa1af262ae7676f5b97a9) — demonstrated feasibility but rejected string-based ownership attribution.
- [Design-decision record](https://github.com/teamleaderleo/codex/blob/08a04bbe36ce0fc10fe205849a4800d91acf4412/notes/code-mode-orphan-fix/deep-dive/agent-3-design-decisions.md) — reasons for rejecting or deferring schema changes, second registries, automatic termination, global listing, display capping, generic origin modelling, wake-up events, and recovery work.

## Secondary investigation records

These are synthesis and provenance records. They should cite through to primary sources for concrete code or validation claims.

- [Investigation reconstruction](https://github.com/teamleaderleo/codex/blob/3d81c5bc244c8ac0526eb0a7fa29ee297dfc97b7/notes/code-mode-orphan-fix/deep-dive/agent-1-investigation-reconstruction.md).
- [Testing and validation archaeology](https://github.com/teamleaderleo/codex/blob/824f4807a5d1da45e1952378ef390f9278676748/notes/code-mode-orphan-fix/deep-dive/agent-2-test-validation-archaeology.md).
- [Code walkthrough](https://github.com/teamleaderleo/codex/blob/08a04bbe36ce0fc10fe205849a4800d91acf4412/notes/code-mode-orphan-fix/deep-dive/agent-3-code-walkthrough.md).
- [Design decisions](https://github.com/teamleaderleo/codex/blob/08a04bbe36ce0fc10fe205849a4800d91acf4412/notes/code-mode-orphan-fix/deep-dive/agent-3-design-decisions.md).
- [History and threat-model notes](https://github.com/teamleaderleo/codex/blob/363fbf606676e10ff11599255cd39ae4b5299f41/notes/code-mode-orphan-fix/deep-dive/agent-3-history-and-threat-model-notes.md).
- [Publication architecture and copy audit](https://github.com/teamleaderleo/codex/blob/02a6c17613b0f2848525fd30cf5d1d391b322dee/notes/code-mode-orphan-fix/deep-dive/agent-4-publication-architecture.md).
- [Methodology and provenance](https://github.com/teamleaderleo/codex/blob/02a6c17613b0f2848525fd30cf5d1d391b322dee/notes/code-mode-orphan-fix/deep-dive/methodology-and-provenance.md).

## Independent external static review

- [External-review triage](https://github.com/teamleaderleo/codex/blob/728e2e07462aea6505925366158b5f04644ad034/notes/code-mode-orphan-fix/external-review/triage-2026-07-26.md) records one Codex review and one Claude review. Both were static rather than executable.
- Findings that changed the final tests were subsequently checked through repository-native execution before being accepted.

Independent review is useful scrutiny, but it is not a substitute for executable evidence.

## Private-by-default evidence

The following should not be published automatically:

- raw ChatGPT transcripts;
- raw rollout or JSONL logs;
- machine-specific file paths;
- process snapshots containing unrelated user data;
- tokens, URLs, image payloads, prompts, or conversation identifiers;
- unsanitised one-off analysis scripts.

A scrubbed excerpt or private handoff may be considered when it materially answers a maintainer question and the human coordinator explicitly approves disclosure.