# Validation history for code-mode live-session handle recovery

This ledger centralises the validation evidence behind [openai/codex#35613](https://github.com/openai/codex/issues/35613) and the code-mode live-session-ID implementation.

The implementation evolved through closely related commits. The production behaviour under review is the same narrow data flow throughout the later checkpoints: preserve exact creator-cell provenance, query manager-observed live processes for that cell, sort the logical session IDs numerically, and add them to terminal code-mode status without changing lifecycle or protocol behaviour.

## Relevant refs

| Role | Ref | Notes |
|---|---|---|
| Negative reproduction | [`7298dcf4`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5) | Before-state test: live nested processes remain manager-owned while their handles are absent from model-visible completion output. |
| Earlier consolidated candidate | [`76021678`](https://github.com/teamleaderleo/codex/commit/760216784efaee1ba6a3b1250349f31d5f91c7ca) | Head used for repeated candidate/base compatibility validation before the presentation cap was added. |
| Final bounded implementation milestone | [`eb530466`](https://github.com/teamleaderleo/codex/commit/eb530466cafac0a5aee86342cd2b5ada9047d448) | Independent model-visible display limit of 64, numeric sort-before-truncation, and exact `(+N more)` suffix. |
| Latest implementation head | [`77e7e314`](https://github.com/teamleaderleo/codex/commit/77e7e3149df366236db2426596c23ebbe1d6bb48) | Same production implementation as `eb530466`, plus test-only Windows-target skip annotations for POSIX acceptance commands. The `fix/code-mode-live-session-ids` branch currently resolves to this exact commit. |

## Evidence summary

| Coverage | Ref or tested tree | Result | Evidence |
|---|---|---|---|
| Repeated candidate/base compatibility validation | Earlier `76021678` candidate/base work | 20/20 candidate repetitions and 20/20 base repetitions passed locally | Historical local record; these repetitions predate the bounded final head and are not represented as repetitions of `eb530466` or `77e7e314`. |
| Focused formatter and manager tests | Exact validated tree committed as `eb530466` | 9 passed | [Actions run 30220464228](https://github.com/teamleaderleo/codex/actions/runs/30220464228) |
| Formatting, scoped fixes, diff and worktree checks | Exact validated tree committed as `eb530466` | Passed; worktree clean | [Actions run 30220464228](https://github.com/teamleaderleo/codex/actions/runs/30220464228) |
| Local acceptance | Value-equivalent bounded implementation workspace | 5 passed | [Actions run 30217686056](https://github.com/teamleaderleo/codex/actions/runs/30217686056) |
| Docker/Linux remote acceptance | Same workspace with Ubuntu 24.04 exec server | 4 passed; 1 explicit host-`TempDir` skip | [Actions run 30217686056](https://github.com/teamleaderleo/codex/actions/runs/30217686056) |
| Existing compatibility tests | Same workspace | 2 passed | [Actions run 30217686056](https://github.com/teamleaderleo/codex/actions/runs/30217686056) |
| Full `codex-core` library suite | Latest implementation head `77e7e314` | 2,093 passed; 0 failed; 0 skipped | [Actions run 30291034837](https://github.com/teamleaderleo/codex/actions/runs/30291034837), artifact `code-mode-full-suite-log` |
| Full shared core suite against Windows exec under Wine | Latest implementation head `77e7e314` | No tests executed; two identical Bazel analysis failures before target construction | [Run 30293323612](https://github.com/teamleaderleo/codex/actions/runs/30293323612), [retrigger 30296440567](https://github.com/teamleaderleo/codex/actions/runs/30296440567) |

Additional local test runs were performed during development. This ledger avoids inventing URLs or collapsing unlike refs; it records the repeated local count that was preserved in the project handoff and links every available public CI receipt.

## Exact final-head focused validation

[GitHub Actions run 30220464228](https://github.com/teamleaderleo/codex/actions/runs/30220464228) ran on GitHub-hosted Ubuntu 24.04. The workflow applied the final architecture correction, validated the resulting tree, and then committed that tested tree as `eb530466cafac0a5aee86342cd2b5ada9047d448`.

Commands:

```sh
just fmt
just fix -p codex-core

UNIT_FILTER='test(/(live_process_ids_created_by_cell_filters_exited_and_sorts|terminal_cell_id_excludes_yielded_responses|terminal_script_status_surfaces_sorted_live_background_sessions|terminal_script_status_preserves_sessions_at_display_limit|terminal_script_status_caps_sessions_above_display_limit|terminal_script_status_sorts_before_truncation|terminal_script_status_formats_exact_omitted_count|terminal_script_status_omits_warning_for_empty_sessions|yielded_script_status_does_not_surface_background_sessions)$/)'

just test -p codex-core --lib -E "$UNIT_FILTER" --no-capture --no-tests=fail
git diff --check
git status --porcelain=v1 --untracked-files=all
```

Results:

- `just fmt`: passed;
- `just fix -p codex-core`: passed;
- nine focused tests: passed;
- `git diff --check`: passed;
- final worktree: clean.

## Local and Docker acceptance validation

[GitHub Actions run 30217686056](https://github.com/teamleaderleo/codex/actions/runs/30217686056) ran on GitHub-hosted Ubuntu 24.04 and used an Ubuntu 24.04 Docker exec server for the remote-safe cases.

Results:

- five local acceptance cases passed;
- four Docker remote-safe acceptance cases passed;
- `code_mode_completion_reports_only_surviving_nested_session` was explicitly excluded from remote execution because its PID/release paths use a host `TempDir` not shared with the executor; the case passed locally;
- two selected existing compatibility tests passed;
- formatting, scoped fix and diff checks passed.

The later change from a manager-cap alias to an independent literal `64` preserved the formatter value and did not change the acceptance setup or behaviour, so this acceptance run was not repeated solely for that decoupling.

## Latest-head full library suite

[GitHub Actions run 30291034837](https://github.com/teamleaderleo/codex/actions/runs/30291034837) was launched by [`f980d5a3`](https://github.com/teamleaderleo/codex/commit/f980d5a3e3e2bfe6c9058aaa90dbf1a0aae96954) and ran on GitHub-hosted Ubuntu 24.04.

The workflow checked out exact implementation head `77e7e3149df366236db2426596c23ebbe1d6bb48` and ran:

```sh
just test -p codex-core --lib --no-capture --no-tests=fail
```

Results:

- 2,093 tests passed;
- 0 failed;
- 0 skipped;
- nextest summary duration: 239.445 seconds;
- the job and every workflow step completed successfully.

The uploaded artifact is `code-mode-full-suite-log` (artifact ID `8663148873`, digest `sha256:22e23ceede26120e2646150ef42e654cfca898d26fff4b3ee6494a0f1734fc7f`).

`77e7e314` contains the same production code as `eb530466`; its only additional change is test-only Windows-target skip handling for POSIX acceptance commands.

## Wine/Bazel validation and the POSIX-command boundary

Wine-exec tests require an x86-64 Linux host and Bazel because the harness cross-builds the Windows exec server and runs it under Wine while the Rust integration-test process remains on Linux.

The latest-head Wine workflow is:

- [workflow page](https://github.com/teamleaderleo/codex/actions/workflows/temp-code-mode-wine-suite.yml);
- launcher commit [`d7ebb964`](https://github.com/teamleaderleo/codex/commit/d7ebb96477a384b73c1bf59fb29e7179fc755870), later retriggered by [`2b7b930`](https://github.com/teamleaderleo/codex/commit/2b7b93081361b77f8ddaceaf362a09765b4153bf);
- tested implementation head `77e7e3149df366236db2426596c23ebbe1d6bb48`;
- command:

```sh
bazel test //codex-rs/core:core-all-wine-exec-test \
  --nocache_test_results \
  --test_output=all
```

Two public attempts produced the same result:

- [run 30293323612](https://github.com/teamleaderleo/codex/actions/runs/30293323612);
- [retriggered run 30296440567](https://github.com/teamleaderleo/codex/actions/runs/30296440567).

In both runs, checkout and Bazel setup succeeded, but Bazel stopped during analysis before constructing or launching any test target. The root error was:

```text
codex_rust_crate() got unexpected keyword argument: binary_test_target_compatible_with
```

At `77e7e314`, `codex-rs/windows-sandbox-rs/BUILD.bazel` passes that argument while the `codex_rust_crate` definition in `defs.bzl` does not accept it. That prevents `//codex-rs/windows-sandbox-rs:codex-command-runner` from being declared, cascades into a missing-target error for `core-all-wine-exec-test`, and ends with `No test targets were found`.

This is a reproducible Bazel build-graph incompatibility in the exact checked-out repository snapshot, not a Patch 1 assertion failure and not evidence about the runtime skip guards. No Rust test process started, so no Patch 1 acceptance test or runtime skip message could execute. Re-running the unchanged target a third time would not add evidence unless the Bazel macro/BUILD mismatch is first corrected or the patch is tested on a repository snapshot where that target analyzes successfully.

The Patch 1 `orphan_sessions` acceptance cases also have an important target boundary even after the Bazel target becomes runnable:

- `code_mode_completion_surfaces_discarded_live_exec_sessions`, `large_emitted_output_does_not_truncate_live_session_warning`, `yielded_cell_response_does_not_include_completion_session_warning`, and `code_mode_completion_reports_only_sessions_created_by_current_cell` return early under Wine via `skip_if_target_windows!` because their commands use POSIX shell syntax that is not valid for the Windows exec target;
- `code_mode_completion_reports_only_surviving_nested_session` returns early in every remote environment via `skip_if_remote!` because it embeds host `TempDir` PID/release paths that are not shared with Docker or Wine.

Therefore, even a successful full Wine suite would validate the Bazel/Wine harness and broader shared test suite on the implementation head. It would **not** mean that the five Patch 1 acceptance scenarios executed their substantive assertions against Windows.

## Harness attempts that are not Patch 1 test failures

Four GitHub Actions attempts failed before producing a Patch 1 product-test result and are not counted as assertion failures:

- [run 30217238334](https://github.com/teamleaderleo/codex/actions/runs/30217238334): validation harness failed during linker-swap setup;
- [run 30217425523](https://github.com/teamleaderleo/codex/actions/runs/30217425523): validation harness reached the main step but failed because `uv` was unavailable;
- [run 30293323612](https://github.com/teamleaderleo/codex/actions/runs/30293323612): Wine target failed during Bazel analysis before any test target was constructed;
- [run 30296440567](https://github.com/teamleaderleo/codex/actions/runs/30296440567): identical retrigger confirmed the same repository build-graph incompatibility.

The corrected acceptance run was [30217686056](https://github.com/teamleaderleo/codex/actions/runs/30217686056), the corrected exact final-head focused run was [30220464228](https://github.com/teamleaderleo/codex/actions/runs/30220464228), and the full `codex-core --lib` suite passed in [30291034837](https://github.com/teamleaderleo/codex/actions/runs/30291034837).

## Scope boundary

The implementation and the validation above do not claim changes to process ownership, automatic termination, pruning, recovery, JavaScript schemas, protocol schemas or events, call-ID generation, or lifecycle semantics. The change restores model-visible handles for manager-owned nested work attributed to the exact terminal code-mode cell and bounds that status fragment independently at 64 visible IDs.