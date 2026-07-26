# Agent 2 testing-conventions review

Agent: Agent 2
Lane: reproduction, acceptance, and validation
Reviewed base: `61a44880a85d2fd0d8770908dea5733495e571c8`
Reviewed candidate: `3778e1fae6e7e3d885252282a7c5ce67e06730ff`
Verdict: change requested

Concrete findings:
- The three new `code_mode` unit tests are located consistently in the existing module-local `#[cfg(test)]` block and use descriptive behaviour-oriented names. Their exact string assertions are appropriate because they directly exercise the user-visible `format_script_status` formatter.
- The five acceptance cases exercise the important behavioural contracts: surviving-session visibility, exclusion of exited sessions, current-cell attribution, yielded-response neutrality, deterministic numeric ordering, and warning preservation outside emitted-output truncation.
- The dedicated `codex-rs/core/tests/code_mode_orphan_sessions.rs` target does not follow the dominant current `codex-core` convention. `tests/all.rs` documents a single integration binary that aggregates modules from `tests/suite/`, and `tests/suite/mod.rs` already registers `code_mode`. The new standalone target also duplicates helpers already present in `tests/suite/code_mode.rs`, including custom-tool output extraction, text-item access, and code-mode turn setup.
- `assert_process_ids_absent` can produce a false failure in the yielded-response test. It treats every numeric token in the header as a possible process ID, but the yielded header necessarily contains a numeric cell ID. A process ID that happens to equal the cell ID would fail the test even though no completion-only background-session warning was emitted.
- Cleanup is panic-safe after the assertion future begins: `catch_unwind` preserves the original panic, `finish_with_cleanup` attempts termination, and cleanup failures are surfaced or logged. Cleanup does not cover every setup failure, because the first four tests call `run_code_mode_turn(...).await?` before entering the guarded body; `run_code_mode_turn` submits the turn and may return an error after creating a background process.
- `code_mode_completion_reports_only_surviving_nested_session` is unnecessarily timing-sensitive. It relies on a one-second process exit plus a separate two-second sleep rather than polling a state transition with a bounded timeout or triggering completion deterministically.
- The large-output assertion is appropriately contract-focused: it does not require one exact truncation representation or a wall-clock value, only that emitted output remains represented separately from the untruncated status header.
- The Unix and network limitations are explicit through the Windows ignore and established network-skip convention. Those constraints are reasonable for nested shell-process behaviour, but validation reporting must count skips separately from passes.

Required code or test changes:
- Move the five acceptance cases into `tests/suite/code_mode.rs`, or into a focused code-mode submodule registered through `tests/suite/mod.rs`, and reuse the existing code-mode test helpers rather than retaining a new standalone integration binary.
- Replace the yielded-response numeric-token absence assertion with a direct contract assertion that the completion-only background-session warning or parsed session-summary field is absent.
- Extend cleanup protection to cover turn submission and other setup steps that can create background terminals before returning an error.
- Replace the fixed one-second/two-second process race with bounded state polling or another deterministic exit mechanism.
- After those edits, rerun only the affected module unit tests and the affected code-mode integration cases; no broad workspace rerun is requested by this review.

Public-copy corrections:
- Describe validation as patch-scoped unit tests and five acceptance cases passing, formatting and exact-file review passing, and the observed project-suite result matching the upstream base.
- State explicitly that the broad project suite was not green in the environment. The supported claim is no candidate-specific differential regression in the observed suite result, not a fully green workspace or an unconditional “all tests passed.”
- Distinguish platform skips, test failures, compilation failures, linker/resource failures, and matched-base infrastructure failures in any validation table.

Likely maintainer concerns:
- A new 521-line standalone integration target when the crate already aggregates integration modules through `tests/all.rs` and `tests/suite/`.
- Duplicated code-mode response and setup helpers rather than extending the existing suite.
- Fixed sleeps in a process-lifecycle test.
- Manual panic-cleanup plumbing that still leaves a setup-error gap; maintainers may prefer a reusable terminal-cleanup guard in test support.
- Assertions that parse incidental numeric tokens rather than checking the named warning contract directly.

Deferred follow-ups:
- Record a repository-native validation profile that declares target kind (`--lib`, aggregated `all`, or an explicitly approved standalone target), exact filters, serial requirements, platform/skip conditions, resource expectations, base and candidate SHAs, and whether the result is a direct pass or matched-base differential.
- Consider a reusable panic-safe background-terminal cleanup guard in `core_test_support`; keep that helper refactor separate unless maintainers request it as part of this patch.
- Keep broad runner/resource improvements and generic fallback selection separate from Patch 1.

Human decisions requested:
- Decide whether maintainers should receive the acceptance cases directly in the existing `tests/suite/code_mode.rs` file or in a smaller registered submodule; either follows the aggregate-test convention, but the preferred review shape is a maintainer judgement.
- Approve the final bounded validation wording before upstream publication because the project suite remained baseline/environment-limited rather than green.
