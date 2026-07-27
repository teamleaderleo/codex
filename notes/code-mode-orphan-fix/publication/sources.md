# Sources

This index ranks the evidence used by the [issue](issue.md), [pull-request draft](pull-request.md), and [technical deep dive](deep-dive.md). Concrete claims should rely on the highest available source class.

## 1. Current commit-pinned code

- [Current code head `77e7e314`](https://github.com/teamleaderleo/codex/commit/77e7e3149df366236db2426596c23ebbe1d6bb48)
- [Selected upstream base `61a44880`](https://github.com/openai/codex/commit/61a44880a85d2fd0d8770908dea5733495e571c8)
- [Complete base-to-current comparison](https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...77e7e3149df366236db2426596c23ebbe1d6bb48)
- [Bounded-output supplement `760216...` to `eb530466...`](https://github.com/teamleaderleo/codex/compare/760216784efaee1ba6a3b1250349f31d5f91c7ca...eb530466cafac0a5aee86342cd2b5ada9047d448)
- [Target-Windows guard commit `77e7e314`](https://github.com/teamleaderleo/codex/commit/77e7e3149df366236db2426596c23ebbe1d6bb48)

### Creator-cell provenance and storage

- [`ExecCommandHandler` captures the existing code-mode cell identity](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L132-L138)
- [`UnifiedExecContext` carries typed creator metadata](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L76-L99)
- [`ProcessEntry` retains creator-cell attribution](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L189-L200)
- [`store_process` copies creator metadata into the stored entry](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/process_manager.rs#L944-L976)

### Liveness, final-result selection, and bounded formatting

- [`live_process_ids_created_by_cell`: exact-cell, manager-live-only, numerically sorted query](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L168-L180)
- [Final-result lookup and yielded exclusion](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L201-L269)
- [Independent model-visible display-cap definition](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L57-L59)
- [Sorting, bounded prefix, and exact omitted-count formatter](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L270-L305)
- [Separate manager soft process-store capacity](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L70-L76)
- [Target-Windows guards on POSIX-command acceptance cases](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs)

## 2. Current commit-pinned tests

### Focused status tests

- [`terminal_cell_id_excludes_yielded_responses`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L444-L459)
- [`terminal_script_status_surfaces_sorted_live_background_sessions`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L462-L491)
- [`terminal_script_status_preserves_sessions_at_display_limit`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L494-L512)
- [`terminal_script_status_caps_sessions_above_display_limit`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L515-L542)
- [`terminal_script_status_sorts_before_truncation`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L544-L564)
- [`terminal_script_status_formats_exact_omitted_count`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L567-L588)
- [`terminal_script_status_omits_warning_for_empty_sessions`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L590-L599)
- [`yielded_script_status_does_not_surface_background_sessions`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L601-L612)

### Direct manager test

- [`live_process_ids_created_by_cell_filters_exited_and_sorts`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod_tests.rs#L333-L395)

### Aggregate acceptance cases

- [Current five-case acceptance module](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs)

Case names:

1. `code_mode_completion_surfaces_discarded_live_exec_sessions`
2. `code_mode_completion_reports_only_surviving_nested_session`
3. `large_emitted_output_does_not_truncate_live_session_warning`
4. `yielded_cell_response_does_not_include_completion_session_warning`
5. `code_mode_completion_reports_only_sessions_created_by_current_cell`

### Compatibility and negative reproduction

- [`code_mode_can_run_multiple_yielded_sessions`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/tests/suite/code_mode.rs#L1858)
- [`code_mode_wait_can_terminate_and_continue`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/tests/suite/code_mode.rs#L2179)
- [Immutable before-state reproduction `7298dcf4`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5)

## 3. Execution evidence

- [Focused validation on capped head `eb530466...`, run 30220464228](https://github.com/teamleaderleo/codex/actions/runs/30220464228)
- [Local and Docker acceptance validation on the pre-decoupling capped workspace, run 30217686056](https://github.com/teamleaderleo/codex/actions/runs/30217686056)
- [Diagnostic Wine workflow head `d8d194c0...`](https://github.com/teamleaderleo/codex/commit/d8d194c0c2822bce0c1a0b7647c1fabc993fd9a6)
- [Wine attempt environment](https://github.com/teamleaderleo/codex/blob/validation/code-mode-wine-target-guards-results/validation-results/patch1-wine-target-guards/environment.txt)
- [Wine attempt result](https://github.com/teamleaderleo/codex/blob/validation/code-mode-wine-target-guards-results/validation-results/patch1-wine-target-guards/result.txt)
- [Wine Bazel-analysis failure excerpt](https://github.com/teamleaderleo/codex/blob/validation/code-mode-wine-target-guards-results/validation-results/patch1-wine-target-guards/summary.txt)
- [Scrubbed validation record](validation.md)

The Actions runs establish what executed on their recorded refs. The Wine attempt establishes only that the pinned target was blocked before Rust test discovery by an unrelated BUILD/macro mismatch.

## 4. Repository conventions and review guidance

- [Single aggregate integration-test binary convention](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/tests/all.rs#L1-L9)
- [Existing code-mode suite and child-module registration](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/tests/suite/code_mode.rs#L59-L77)
- [Core Wine-exec target and skip-macro guidance](https://github.com/openai/codex/blob/0896bf6fc05ead454888b90044e1a08f99b6d778/codex-rs/core/README.md#L7-L19)
- [800-line change-size guidance](https://github.com/openai/codex/blob/0896bf6fc05ead454888b90044e1a08f99b6d778/.codex/skills/code-review-change-size/SKILL.md)
- [Invitation-only contribution policy](https://github.com/openai/codex/blob/61a44880a85d2fd0d8770908dea5733495e571c8/docs/contributing.md)

## 5. Selected architectural history

| Source | Relevance |
|---|---|
| [Unified execution PR #3288](https://github.com/openai/codex/pull/3288) / [commit `c09ed74a`](https://github.com/openai/codex/commit/c09ed74a163ecea69c32d61ab2bfa1c8490eb611) | Reusable PTY-backed sessions, numeric IDs, persistence, isolation, timeouts, and bounded output. |
| [Tool-system refactor PR #4510](https://github.com/openai/codex/pull/4510) / [commit `33d3ecbc`](https://github.com/openai/codex/commit/33d3ecbccca4b92cfb2a77002387de30302f337f) | Handler, router, registry, and invocation-context boundaries. |
| [JavaScript REPL PR #10674](https://github.com/openai/codex/pull/10674) / [commit `42e22f3b`](https://github.com/openai/codex/commit/42e22f3bde6c851422eb4f7b502457fe86ba91db) | Persistent JavaScript execution. |
| [Code mode on V8 PR #15276](https://github.com/openai/codex/pull/15276) / [commit `e4eedd61`](https://github.com/openai/codex/commit/e4eedd6170580d5b06fb539635a78f261a6b7369) | Rust/V8 code-mode runtime. |
| [Cell actor PR #28599](https://github.com/openai/codex/pull/28599) / [commit `e2f074e1`](https://github.com/openai/codex/commit/e2f074e16c522bfa55d9bcd344a5ea0ba5a4580f) | Single-owner code-cell lifecycle boundary. |

## 6. Related public reports

| Issue | Relationship to Patch 1 |
|---|---|
| [#34866](https://github.com/openai/codex/issues/34866) | Broader wrapper/process completion contradiction; explicitly identifies discarded `session_id` or `exit_code` values. |
| [#33816](https://github.com/openai/codex/issues/33816) | Model-side loss of a yielded session can cause false completion claims and duplicate commands. |
| [#14731](https://github.com/openai/codex/issues/14731) | Proposes keeping a turn active while unified-exec work remains live. |
| [#15723](https://github.com/openai/codex/issues/15723) | Reports missing wake-up for completed background subprocesses and subagents. |
| [#32188](https://github.com/openai/codex/issues/32188) | Requests opt-in event-driven wake-up on background exec completion. |
| [#13733](https://github.com/openai/codex/issues/13733) | Documents the model-turn and token cost of repeated background-process polling. |

These reports show a broader lifecycle and continuation problem space. Patch 1 remains narrower: it restores handles for exact-cell processes that are already live when the final code-mode result is formatted.

#35482 is intentionally not used as Patch 1 impact evidence. Its central incident and requested remedies concern process-group termination, sandbox inspection, timeouts, and disk backpressure, which this patch does not address.

## 7. Technical synthesis

- [Summary](summary.md)
- [Standalone issue](issue.md)
- [Pull-request draft](pull-request.md)
- [Technical deep dive](deep-dive.md)

These documents are synthesis. Their concrete claims should trace back to the commit-pinned code, tests, execution evidence, repository guidance, architectural history, or public issues listed above.