# Validation

This record separates the code refs and test environments so passes are attributed only to the versions that actually ran.

## Refs

| Role | Ref |
|---|---|
| Selected upstream base | [`61a44880a85d2fd0d8770908dea5733495e571c8`](https://github.com/openai/codex/commit/61a44880a85d2fd0d8770908dea5733495e571c8) |
| Uncapped parent | [`760216784efaee1ba6a3b1250349f31d5f91c7ca`](https://github.com/teamleaderleo/codex/commit/760216784efaee1ba6a3b1250349f31d5f91c7ca) |
| Independent-cap head | [`eb530466cafac0a5aee86342cd2b5ada9047d448`](https://github.com/teamleaderleo/codex/commit/eb530466cafac0a5aee86342cd2b5ada9047d448) |
| Current target-guard head | [`77e7e3149df366236db2426596c23ebbe1d6bb48`](https://github.com/teamleaderleo/codex/commit/77e7e3149df366236db2426596c23ebbe1d6bb48) |
| Diagnostic Wine workflow head | [`d8d194c0c2822bce0c1a0b7647c1fabc993fd9a6`](https://github.com/teamleaderleo/codex/commit/d8d194c0c2822bce0c1a0b7647c1fabc993fd9a6) |
| Earlier broad-comparison candidate, production-equivalent to uncapped parent | [`3778e1fae6e7e3d885252282a7c5ce67e06730ff`](https://github.com/teamleaderleo/codex/commit/3778e1fae6e7e3d885252282a7c5ce67e06730ff) |

The current base-to-head comparison changes eight files and 903 lines: 895 insertions and 8 deletions. The 527-line acceptance module accounts for most of the total.

## Result matrix

| Coverage | Ref/workspace | Result |
|---|---|---|
| Focused formatter and manager tests | `eb530466...` | 9 passed |
| Formatting, scoped fixes, diff and cleanliness checks | `eb530466...` | passed |
| Local acceptance | pre-decoupling capped workspace with final remote harness | 5 passed |
| Docker/Linux remote acceptance | same workspace; four selected remote-safe cases | 4 passed |
| Existing compatibility tests | same workspace | 2 passed |
| Wine/Windows-target acceptance | current code head `77e7e314...` | blocked during Bazel analysis; 0 Rust tests executed |

## Focused validation: run 30220464228

Run: [GitHub Actions 30220464228](https://github.com/teamleaderleo/codex/actions/runs/30220464228)  
Platform: GitHub-hosted Ubuntu 24.04  
Validated head: `eb530466cafac0a5aee86342cd2b5ada9047d448`

Commands:

```sh
just fmt
just fix -p codex-core

UNIT_FILTER='test(/(live_process_ids_created_by_cell_filters_exited_and_sorts|terminal_cell_id_excludes_yielded_responses|terminal_script_status_surfaces_sorted_live_background_sessions|terminal_script_status_preserves_sessions_at_display_limit|terminal_script_status_caps_sessions_above_display_limit|terminal_script_status_sorts_before_truncation|terminal_script_status_formats_exact_omitted_count|terminal_script_status_omits_warning_for_empty_sessions|yielded_script_status_does_not_surface_background_sessions)$/)'

just test -p codex-core --lib -E "$UNIT_FILTER" --no-capture --no-tests=fail

git diff --check
git diff --check 760216784efaee1ba6a3b1250349f31d5f91c7ca HEAD
git status --porcelain=v1 --untracked-files=all
```

Results:

- `just fmt`: passed;
- `just fix -p codex-core`: passed;
- focused tests: 9 passed, 0 failed;
- supplement-scope checks: passed;
- `git diff --check`: passed;
- worktree: clean.

The nine focused tests comprise eight formatter/status cases and one direct manager-query case. The manager test is the deterministic evidence for exact-cell filtering, exited-entry exclusion, and numeric ordering.

## Local and Docker acceptance: run 30217686056

Run: [GitHub Actions 30217686056](https://github.com/teamleaderleo/codex/actions/runs/30217686056)  
Host: GitHub-hosted Ubuntu 24.04  
Remote executor: Docker `ubuntu:24.04`

This run exercised the capped behaviour and final remote-test harness before the display constant was decoupled from the manager's numerically equal capacity.

Key filters:

```sh
all_acceptance_filter='test(/suite::code_mode::orphan_sessions::/)'
remote_acceptance_filter='test(/suite::code_mode::orphan_sessions::(code_mode_completion_surfaces_discarded_live_exec_sessions|large_emitted_output_does_not_truncate_live_session_warning|yielded_cell_response_does_not_include_completion_session_warning|code_mode_completion_reports_only_sessions_created_by_current_cell)$/)'
compat_filter='test(/suite::code_mode::(code_mode_can_run_multiple_yielded_sessions|code_mode_wait_can_terminate_and_continue)$/)'
```

Results:

- local acceptance: 5 passed, 0 failed;
- Docker acceptance: four selected cases passed, 0 failed;
- survivor case: excluded by the Docker workflow filter because its host `TempDir` paths were unavailable inside the executor; passed locally;
- compatibility: 2 passed, 0 failed;
- `git diff --check`: passed.

The Docker record is a filter exclusion, not an executed runtime skip. The compatibility passes belong to this pre-decoupling capped workspace and are not attributed to exact current head `77e7e314...`.

## Current guard head and Wine attempt

Current code head `77e7e314...` is one test-only commit over `eb530466...`. It imports `skip_if_target_windows!` and applies it to the four acceptance cases whose command strings require POSIX shell syntax. The host-path survivor case retains `skip_if_remote!`.

A targeted Wine-exec validation was attempted through diagnostic workflow head `d8d194c0...` on an x86-64 Ubuntu runner using Bazel 9.0.0.

Target and forwarded Rust filter:

```sh
bazel test //codex-rs/core:core-all-wine-exec-test \
  --nocache_test_results \
  --test_output=all \
  --test_arg='suite::code_mode::orphan_sessions::' \
  --test_arg='--nocapture'
```

Recorded environment:

```text
agent=Agent 69
code_head=77e7e3149df366236db2426596c23ebbe1d6bb48
platform=Linux ... x86_64 GNU/Linux
bazel=bazel 9.0.0
target=//codex-rs/core:core-all-wine-exec-test
filter=suite::code_mode::orphan_sessions::
```

Bazel stopped during analysis before test discovery:

```text
ERROR: codex_rust_crate() got unexpected keyword argument: binary_test_target_compatible_with
ERROR: ... no such target '//codex-rs/windows-sandbox-rs:codex-windows-sandbox-setup'
ERROR: Analysis of target '//codex-rs/core:core-all-wine-exec-test' failed
ERROR: No test targets were found, yet testing was requested
```

Interpretation:

- Bazel exit status: 1;
- Rust tests discovered: 0;
- Patch 1 pass/fail result: none—the suite was never reached;
- failure site: an unrelated `windows-sandbox-rs` BUILD/macro inconsistency in the pinned repository snapshot;
- worktree after the attempt: clean.

Readable evidence:

- [environment](https://github.com/teamleaderleo/codex/blob/validation/code-mode-wine-target-guards-results/validation-results/patch1-wine-target-guards/environment.txt)
- [result](https://github.com/teamleaderleo/codex/blob/validation/code-mode-wine-target-guards-results/validation-results/patch1-wine-target-guards/result.txt)
- [failure excerpt](https://github.com/teamleaderleo/codex/blob/validation/code-mode-wine-target-guards-results/validation-results/patch1-wine-target-guards/summary.txt)
- [clean worktree record](https://github.com/teamleaderleo/codex/blob/validation/code-mode-wine-target-guards-results/validation-results/patch1-wine-target-guards/git-status.txt)

This evidence replaces the earlier statement that no Wine run had been attempted. It does not establish a Wine pass or a Patch 1 failure.

## Broad and workspace coverage

An earlier broad `codex-core` comparison used candidate `3778e1fa...`, which was production-equivalent to uncapped parent `760216...`, and exact upstream base `61a44880...`.

- the broad run was red on both refs;
- focused investigation found no persistent candidate-only failure;
- no broad differential was run for the capped or guard-only heads;
- the complete workspace suite was not run.

## Review size

If maintainers request a split, the smallest coherent first stage is the production provenance, manager query, bounded formatter, nine focused tests, and the primary discarded-handle acceptance reproduction. The remaining acceptance cases can follow separately.

This is a reviewability option, not a correctness dependency.

## Artifacts

| Run | Artifact | GitHub-reported SHA-256 digest |
|---|---|---|
| [30220464228](https://github.com/teamleaderleo/codex/actions/runs/30220464228) | `patch1-decouple-30220464228-1` | `0245c51d34a052e0e7a8a449d5504a5378a8180bb73d190dbf776e3ccfc79bfc` |
| [30217686056](https://github.com/teamleaderleo/codex/actions/runs/30217686056) | `patch1-focused-validation-30217686056` | `c518837fe3d6ddb9329f0cef53e91a06d1737e97fbd5045fbea72cde72246076` |

The diagnostic Wine evidence was also published as readable text on a separate validation-results branch because the available connector could not reliably enumerate push-triggered Actions runs.