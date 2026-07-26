# Validation

This is the public validation record for Patch 1. It records only evidence relevant to the proposed behaviour and its review boundaries.

## Refs

| Role | Ref |
|---|---|
| Selected upstream base | [`61a44880a85d2fd0d8770908dea5733495e571c8`](https://github.com/openai/codex/commit/61a44880a85d2fd0d8770908dea5733495e571c8) |
| Uncapped parent | [`760216784efaee1ba6a3b1250349f31d5f91c7ca`](https://github.com/teamleaderleo/codex/commit/760216784efaee1ba6a3b1250349f31d5f91c7ca) |
| Independent-cap head | [`eb530466cafac0a5aee86342cd2b5ada9047d448`](https://github.com/teamleaderleo/codex/commit/eb530466cafac0a5aee86342cd2b5ada9047d448) |
| Current target-guard head | [`77e7e3149df366236db2426596c23ebbe1d6bb48`](https://github.com/teamleaderleo/codex/commit/77e7e3149df366236db2426596c23ebbe1d6bb48) |
| Earlier broad-comparison candidate, production-equivalent to uncapped parent `760216...` | [`3778e1fae6e7e3d885252282a7c5ce67e06730ff`](https://github.com/teamleaderleo/codex/commit/3778e1fae6e7e3d885252282a7c5ce67e06730ff) |

The current base-to-head comparison changes eight files and 903 lines: 895 insertions and 8 deletions. The 527-line acceptance module accounts for most of the total.

## Change stages

### Stage A: core visibility fix and acceptance development

Parent `760216...` contains the core exact-cell visibility fix and the original acceptance coverage without the model-visible 64-ID cap.

### Stage B: bounded formatter and remote-test harness

The supplement from `760216...` to `eb530466...` is one commit touching three files:

- `codex-rs/core/src/tools/code_mode/mod.rs`
- `codex-rs/core/tests/suite/code_mode.rs`
- `codex-rs/core/tests/suite/code_mode/orphan_sessions.rs`

Its production change introduces the independent literal `64`, sort-before-take behaviour, and exact omitted-count suffix. The same commit also carries test-harness changes: helper extraction, `build_with_auto_env()` adoption, and a local-only guard for the host-`TempDir` survivor case.

The acceptance Actions workspace already contained those test-harness changes. Its only production difference from `eb530466...` was that the display limit remained an alias of the manager's numerically equal capacity rather than an independent literal.

### Stage C: target-Windows test guards

Current head `77e7e314...` is one commit over `eb530466...` and changes only `orphan_sessions.rs`. It imports `skip_if_target_windows!` and applies it to the four remote-capable tests whose command strings require POSIX shell syntax.

The survivor test keeps `skip_if_remote!` because it depends on host `TempDir` paths and is local-only for both Docker and Wine-exec environments.

## Run 30220464228: focused validation on `eb530466...`

Run: [GitHub Actions 30220464228](https://github.com/teamleaderleo/codex/actions/runs/30220464228)  
Platform: GitHub-hosted Ubuntu 24.04  
Validated head: `eb530466cafac0a5aee86342cd2b5ada9047d448`

### Commands

```sh
just fmt
just fix -p codex-core

UNIT_FILTER='test(/(live_process_ids_created_by_cell_filters_exited_and_sorts|terminal_cell_id_excludes_yielded_responses|terminal_script_status_surfaces_sorted_live_background_sessions|terminal_script_status_preserves_sessions_at_display_limit|terminal_script_status_caps_sessions_above_display_limit|terminal_script_status_sorts_before_truncation|terminal_script_status_formats_exact_omitted_count|terminal_script_status_omits_warning_for_empty_sessions|yielded_script_status_does_not_surface_background_sessions)$/)'

just test -p codex-core --lib -E "$UNIT_FILTER" --no-capture --no-tests=fail

git diff --check
git diff --check 760216784efaee1ba6a3b1250349f31d5f91c7ca HEAD
git status --porcelain=v1 --untracked-files=all
```

The workflow also checked that the recorded supplement had one commit, touched the three expected files, used an independent literal `64`, and did not retain a `MAX_UNIFIED_EXEC_PROCESSES` alias in the formatter module.

### Results

- `just fmt`: passed;
- `just fix -p codex-core`: passed;
- nine focused formatter/manager tests: 9 passed, 0 failed;
- `git diff --check`: passed;
- recorded supplement-scope checks: passed;
- worktree after amend: clean.

### Focused test names

1. `tools::code_mode::tests::terminal_cell_id_excludes_yielded_responses`
2. `tools::code_mode::tests::terminal_script_status_surfaces_sorted_live_background_sessions`
3. `tools::code_mode::tests::terminal_script_status_preserves_sessions_at_display_limit`
4. `tools::code_mode::tests::terminal_script_status_caps_sessions_above_display_limit`
5. `tools::code_mode::tests::terminal_script_status_sorts_before_truncation`
6. `tools::code_mode::tests::terminal_script_status_formats_exact_omitted_count`
7. `tools::code_mode::tests::terminal_script_status_omits_warning_for_empty_sessions`
8. `tools::code_mode::tests::yielded_script_status_does_not_surface_background_sessions`
9. `unified_exec::tests::live_process_ids_created_by_cell_filters_exited_and_sorts`

The manager test directly and deterministically covers exited-entry filtering; it does not depend on shell or network timing.

## Run 30217686056: local and Docker acceptance validation

Run: [GitHub Actions 30217686056](https://github.com/teamleaderleo/codex/actions/runs/30217686056)  
Host: GitHub-hosted Ubuntu 24.04  
Remote executor: Docker `ubuntu:24.04` on the same runner

This run exercised the capped behaviour and final remote-test harness before the display constant was decoupled from the manager capacity.

### Test filters

```sh
unit_filter='test(/(live_process_ids_created_by_cell_filters_exited_and_sorts|terminal_cell_id_excludes_yielded_responses|terminal_script_status_surfaces_sorted_live_background_sessions|terminal_script_status_preserves_sessions_at_display_limit|terminal_script_status_caps_sessions_above_display_limit|terminal_script_status_sorts_before_truncation|terminal_script_status_formats_exact_omitted_count|terminal_script_status_omits_warning_for_empty_sessions|yielded_script_status_does_not_surface_background_sessions)$/)'
all_acceptance_filter='test(/suite::code_mode::orphan_sessions::/)'
remote_acceptance_filter='test(/suite::code_mode::orphan_sessions::(code_mode_completion_surfaces_discarded_live_exec_sessions|large_emitted_output_does_not_truncate_live_session_warning|yielded_cell_response_does_not_include_completion_session_warning|code_mode_completion_reports_only_sessions_created_by_current_cell)$/)'
compat_filter='test(/suite::code_mode::(code_mode_can_run_multiple_yielded_sessions|code_mode_wait_can_terminate_and_continue)$/)'
```

### Executed commands

```sh
just fmt
just fix -p codex-core
just test -p codex-core --lib -E "$unit_filter" --no-capture --no-tests=fail

CODEX_TEST_ENVIRONMENT=local \
  just test -p codex-core --test all -E "$all_acceptance_filter" \
  --no-capture --no-tests=fail

CODEX_TEST_ENVIRONMENT=local \
  just test -p codex-core --test all -E "$compat_filter" \
  --no-capture --no-tests=fail

cargo build -p codex-cli --bin codex

docker run --rm -d \
  --network host \
  -v "$codex_bin:/usr/local/bin/codex:ro" \
  ubuntu:24.04 \
  /usr/local/bin/codex exec-server --listen ws://127.0.0.1:0

CODEX_TEST_ENVIRONMENT=docker \
CODEX_TEST_REMOTE_ENV_CONTAINER_NAME="$remote_container" \
CODEX_TEST_REMOTE_EXEC_SERVER_URL="$remote_url" \
  just test -p codex-core --test all -E "$remote_acceptance_filter" \
  --no-capture --no-tests=fail

git diff --check
```

### Local results

- focused formatter/manager tests: 9 passed, 0 failed;
- local acceptance: 5 passed, 0 failed;
- compatibility: 2 passed, 0 failed;
- `git diff --check`: passed.

The compatibility passes belong to this pre-decoupling capped workspace. They are not an exact-current-head compatibility run.

### Docker results

- four Docker acceptance cases were selected;
- selected cases: 4 passed, 0 failed;
- the survivor case was excluded by the workflow filter because its host `TempDir` PID/release paths were unavailable inside the Docker executor;
- the survivor case passed locally.

The Docker command did not execute the survivor test's runtime skip guard, so the record describes a filter exclusion rather than an executed skip.

## Current head `77e7e314...`: guard-only status

The current head adds target-Windows guards to four acceptance cases using POSIX shell commands. This resolves the static Wine-exec selection defect: Wine-exec uses a native Linux test binary against a Windows exec target, so `cfg(windows)` does not protect target-specific command syntax.

No new public Actions run has been executed on `77e7e314...`. In particular, this record does not claim:

- a Wine-exec pass on the current head;
- a compatibility pass on the current head;
- a new Docker run on the current head;
- a broad differential on the current head; or
- a complete workspace run.

Recommended targeted validation:

```sh
bazel test //codex-rs/core:core-all-wine-exec-test \
  --test_filter='suite::code_mode::orphan_sessions::'
```

Expected result: the four POSIX-command cases report target-Windows skips, and the host-path survivor case reports its broader remote skip.

## Broad and workspace coverage

An earlier matched broad `codex-core` comparison used candidate `3778e1fa...`, which was production-equivalent to uncapped parent `760216...`, and exact upstream base `61a44880...`.

- the broad run was red on both refs;
- focused investigation left no persistent candidate-only failure in that comparison;
- this does not make the broad suite green;
- no new broad differential was run for the capped or guard-only heads;
- the complete workspace suite was not run.

## Change-size reviewability

The current diff is above the repository's 800-line guideline. If a split is requested, the smallest coherent first stage is:

1. production provenance, exact-cell manager query, bounded formatter, nine focused tests, and the primary discarded-handle acceptance case;
2. supplemental acceptance coverage for exited-session filtering, large-output placement, yielded neutrality, exact-cell isolation, and remote routing.

This is a proposed review staging plan, not a claimed approval or waiver.

## Artefacts

| Run | Artefact | GitHub-reported SHA-256 digest |
|---|---|---|
| [30220464228](https://github.com/teamleaderleo/codex/actions/runs/30220464228) | `patch1-decouple-30220464228-1` | `0245c51d34a052e0e7a8a449d5504a5378a8180bb73d190dbf776e3ccfc79bfc` |
| [30217686056](https://github.com/teamleaderleo/codex/actions/runs/30217686056) | `patch1-focused-validation-30217686056` | `c518837fe3d6ddb9329f0cef53e91a06d1737e97fbd5045fbea72cde72246076` |

The artefact names reflect the workflows that produced them and do not correspond to the stage labels used in this document.
