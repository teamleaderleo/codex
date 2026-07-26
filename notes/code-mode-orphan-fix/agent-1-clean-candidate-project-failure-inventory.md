# Clean-candidate `codex-core` project-test failure inventory

Date: 2026-07-26

Candidate: `3778e1fae6e7e3d885252282a7c5ce67e06730ff`

Exact upstream comparison ref: `61a44880a85d2fd0d8770908dea5733495e571c8`

Command on both refs: `just test -p codex-core` using `ubuntu-latest`, the repository `.github/actions/setup-ci` action, `cargo-nextest 0.9.114`, `CARGO_BUILD_JOBS=4`, `CARGO_INCREMENTAL=1`, `CARGO_PROFILE_TEST_DEBUG=0`, and `RUST_BACKTRACE=1`.

## Correction to the earlier compact handoff

The retained nextest output reports **94 failed tests, one timed-out test, and nine skipped tests** on the candidate. The earlier `93 failed` / `3017 passed` summary was an incorrect transcription. The raw candidate summary is `3015 passed (1 flaky), 94 failed, 1 timed out, 9 skipped` out of 3,110 tests.

## Differential summary

- Candidate: 3,110 run; 3,015 passed (one flaky); 94 failed; one timed out; nine skipped.
- Upstream base: 3,102 run; 3,007 passed; 94 failed; one timed out; nine skipped.
- 93 failed-test names and the one timed-out test are shared between candidate and upstream.
- Candidate-only: `codex-core::all suite::unified_exec::unified_exec_formats_large_output_summary`.
- Upstream-only: `codex-core::all suite::compact_resume_fork::snapshot_rollback_followup_turn_trims_context_updates`.
- The eight additional candidate tests are the three focused unit tests and five acceptance tests added by Patch 1; all eight passed.

## Retry and flake record

- The local nextest profile retries once.
- 96 tests received a second attempt: 94 persistent failures, one persistent timeout, and one first-attempt failure that passed on retry.
- Flaky pass: `codex-core::all suite::rollout_budget::restates_the_current_remainder_after_rollback`.
- Every persistent candidate failure failed both attempts; the timed-out test timed out twice.

## Final classification totals

- Environment or missing dependency: 53 shared outcomes.
- Sandbox or runner limitation: 16 candidate outcomes, including the one timeout and the project-run-only unified-exec flake.
- Known/unrelated assertion: 26 shared outcomes reproduced on exact upstream.
- Potentially related to Patch 1: zero.
- Unclassified: zero.

## Skipped tests

- `codex-core::all suite::code_mode_elicitation::code_mode_holds_yielded_result_during_permission_request`
- `codex-core::all suite::compact::manual_compact_non_context_failure_retries_then_emits_task_error`
- `codex-core::all suite::compact_remote::remote_compact_persists_replacement_history_in_rollout`
- `codex-core::all suite::live_cli::live_create_file_hello_txt`
- `codex-core::all suite::live_cli::live_print_working_directory`
- `codex-core::all suite::pending_input::injected_user_input_triggers_follow_up_request_with_deltas`
- `codex-core::all suite::shell_snapshot::macos_unified_exec_uses_shell_snapshot`
- `codex-core::all suite::shell_snapshot::windows_unified_exec_uses_shell_snapshot`
- `codex-core::all suite::unified_exec::write_stdin_ctrl_c_reports_unsupported_interrupt_to_model_on_windows`

The clean patch adds eight non-ignored tests and changes no ignore annotations, so the candidate and upstream skip sets are the same.

## Environment or missing dependency

- **FAIL** `codex-core::all suite::cli_stream::exec_cli_applies_model_instructions_file` — Missing helper binary `codex` (`CARGO_BIN_EXE_codex` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::cli_stream::exec_cli_profile_applies_model_instructions_file` — Missing helper binary `codex` (`CARGO_BIN_EXE_codex` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::cli_stream::integration_creates_and_checks_session_file` — Missing helper binary `codex` (`CARGO_BIN_EXE_codex` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::cli_stream::responses_api_stream_cli` — Missing helper binary `codex` (`CARGO_BIN_EXE_codex` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::cli_stream::responses_mode_stream_cli` — Missing helper binary `codex` (`CARGO_BIN_EXE_codex` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::cli_stream::responses_mode_stream_cli_does_not_attempt_oauth_refresh_for_personal_access_tokens_after_401` — Missing helper binary `codex` (`CARGO_BIN_EXE_codex` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::cli_stream::responses_mode_stream_cli_supports_openai_base_url_config_override` — Missing helper binary `codex` (`CARGO_BIN_EXE_codex` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::cli_stream::responses_mode_stream_cli_supports_personal_access_tokens` — Missing helper binary `codex` (`CARGO_BIN_EXE_codex` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::code_mode::code_mode_can_print_content_only_mcp_tool_result_fields` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::code_mode::code_mode_can_print_error_mcp_tool_result_fields` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::code_mode::code_mode_can_print_structured_mcp_tool_result_fields` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::code_mode::code_mode_can_use_mcp_image_result_with_image_helper` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::code_mode::code_mode_exports_all_tools_metadata_for_namespaced_mcp_tools` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::code_mode::code_mode_exposes_mcp_tools_on_global_tools_object` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::code_mode::code_mode_exposes_namespaced_mcp_tools_on_global_tools_object` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::code_mode::code_mode_exposes_normalized_illegal_mcp_tool_names` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::code_mode::code_mode_lists_global_scope_items` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::code_mode::code_mode_only_can_call_mcp_tool` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::code_mode::code_mode_uses_non_prefixed_mcp_tool_names_when_feature_enabled` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::hooks::permission_request_hook_denies_network_approval_with_custom_message` — Required file/path was absent (os error 2).
- **FAIL** `codex-core::all suite::hooks_mcp::post_tool_use_records_mcp_tool_payload_and_context_with_legacy_prefixed_names` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::hooks_mcp::post_tool_use_records_mcp_tool_payload_and_context_with_non_prefixed_names` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::hooks_mcp::pre_tool_use_rewrites_mcp_tool_before_execution` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::mcp_refresh_cleanup::refresh_keeps_superseded_mcp_server_alive_for_in_flight_calls` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::mcp_tool_cache::regular_mcp_definition_cache_preserves_live_session_state` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::multi_exec_server_sandbox::two_exec_servers_isolate_workspace_write_roots` — Missing helper binary `codex` (`CARGO_BIN_EXE_codex` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::plugins::explicit_plugin_mentions_keep_non_conflicting_mcp_for_chatgpt_auth` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::plugins::explicit_plugin_mentions_use_apps_for_chatgpt_dual_surface_plugins` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::plugins::explicit_plugin_mentions_use_mcp_for_api_key_dual_surface_plugins` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::rmcp_client::local_stdio_server_uses_runtime_fallback_cwd_when_config_omits_cwd` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::rmcp_client::openai_form_capability_is_advertised_to_mcp_servers` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::rmcp_client::openai_form_capability_is_not_advertised_by_default` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::rmcp_client::openai_form_capability_updates_for_loaded_thread` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::rmcp_client::stdio_encrypted_content_responses_round_trip` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::rmcp_client::stdio_image_responses_are_sanitized_for_text_only_model` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::rmcp_client::stdio_image_responses_preserve_original_detail_metadata` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::rmcp_client::stdio_image_responses_resize_large_image` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::rmcp_client::stdio_image_responses_round_trip` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::rmcp_client::stdio_mcp_parallel_tool_calls_default_false_runs_serially` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::rmcp_client::stdio_mcp_parallel_tool_calls_opt_in_runs_concurrently` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::rmcp_client::stdio_mcp_read_only_tool_calls_run_concurrently_without_server_opt_in` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::rmcp_client::stdio_mcp_tool_call_includes_sandbox_state_meta` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::rmcp_client::stdio_mcp_tool_names_respect_selected_servers` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::rmcp_client::stdio_server_propagates_explicit_local_env_var_source` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::rmcp_client::stdio_server_propagates_whitelisted_env_vars` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::rmcp_client::stdio_server_round_trip` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::rmcp_client::stdio_server_uses_configured_cwd_before_runtime_fallback` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::sqlite_state::mcp_call_marks_thread_memory_mode_polluted_when_configured` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::token_budget::token_budget_context_injects_plain_thread_hint_text` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::truncation::mcp_image_output_preserves_image_and_no_text_summary` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::truncation::mcp_tool_call_output_exceeds_limit_truncated_for_model` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::truncation::mcp_tool_call_output_not_truncated_with_custom_limit` — Missing helper binary `test_stdio_server` (`CARGO_BIN_EXE_test_stdio_server` unavailable and fallback binary absent).
- **FAIL** `codex-core::all suite::workspace_roots::workspace_roots_allow_file_and_command_writes` — Required file/path was absent (os error 2).

## Sandbox or runner limitation

- **TIMEOUT** `codex-core image_preparation::tests::detail_policies_apply_the_expected_budgets` — Timed out after 60 seconds on both attempts.
- **FAIL** `codex-core::all suite::apply_patch_cli::apply_patch_cli_preserves_existing_hard_link_outside_workspace` — Filesystem sandbox helper aborted with SIGABRT (signal 6).
- **FAIL** `codex-core::all suite::apply_patch_cli::apply_patch_cli_rejects_move_path_traversal_outside_workspace` — Filesystem sandbox helper aborted with SIGABRT (signal 6).
- **FAIL** `codex-core::all suite::approvals::approval_matrix_covers_group::read_only` — Sandboxed command aborted with signal 6.
- **FAIL** `codex-core::all suite::approvals::approval_matrix_covers_group::workspace_write` — Sandboxed command aborted with signal 6.
- **FAIL** `codex-core::all suite::approvals::approving_execpolicy_amendment_persists_policy_and_skips_future_prompts` — Sandboxed command aborted with signal 6.
- **FAIL** `codex-core::all suite::extension_sandbox::extension_tool_uses_granted_turn_permissions_without_local_persistence` — Filesystem sandbox helper aborted with SIGABRT (signal 6).
- **FAIL** `codex-core::all suite::hooks::permission_request_hook_allows_network_approval_without_prompt` — Timed out waiting for the network-approval hook.
- **FAIL** `codex-core::all suite::network_approval::ambiguous_unattributed_network_request_is_not_assigned_to_active_calls` — Timed out waiting for commands to start.
- **FAIL** `codex-core::all suite::network_approval::cancelled_guardian_network_review_fails_closed_without_rewriting_turn_state` — Timed out waiting for parent and Guardian cancellation.
- **FAIL** `codex-core::all suite::network_approval::guardian_receives_exact_triggers_for_concurrent_network_requests` — Timed out waiting for both Guardian network reviews.
- **FAIL** `codex-core::all suite::request_permissions::request_permissions_grants_apply_to_later_shell_command_calls` — Nested command timed out.
- **FAIL** `codex-core::all suite::request_permissions::request_permissions_grants_apply_to_later_shell_command_calls_without_inline_permission_feature` — Nested command timed out.
- **FAIL** `codex-core::all suite::request_permissions::request_permissions_preapprove_explicit_exec_permissions_outside_on_request` — Child process exited 134 (SIGABRT).
- **FAIL** `codex-core::all suite::workspace_roots::workspace_roots_deny_file_and_command_writes_outside_roots` — Child process exited 134 (SIGABRT).

## Known/unrelated assertion

- **FAIL** `codex-core::all suite::approvals::denying_network_policy_amendment_persists_policy_and_skips_future_network_prompt` — expected network approval request before completion
- **FAIL** `codex-core::all suite::approvals::network_approval_flow_survives_danger_full_access_session_start` — expected network approval request before completion
- **FAIL** `codex-core::all suite::approvals::network_approval_retry_keeps_deny_read_sandbox_for_escalated_command` — expected network approval request before completion
- **FAIL** `codex-core::all suite::approvals::spawned_subagent_execpolicy_amendment_propagates_to_parent_session` — expected subagent command to create file
- **FAIL** `codex-core::all suite::hooks_mcp::pre_tool_use_blocks_mcp_tool_before_execution_with_legacy_prefixed_names` — Verifications failed:
- **FAIL** `codex-core::all suite::hooks_mcp::pre_tool_use_blocks_mcp_tool_before_execution_with_non_prefixed_names` — Verifications failed:
- **FAIL** `codex-core::all suite::network_approval::allowing_network_policy_amendment_persists_context_and_bypasses_prompt` — expected network approval request before completion
- **FAIL** `codex-core::all suite::network_approval::guardian_network_approval_preserves_action_and_outcome_routing` — assertion failed: `(left == right)`
- **FAIL** `codex-core::all suite::network_approval::guardian_receives_exact_trigger_for_single_network_request` — assertion failed: `(left == right)`
- **FAIL** `codex-core::all suite::network_approval::timed_out_guardian_network_review_uses_timeout_outcome_without_user_fallback` — unexpected timed-out Guardian tool output: write_stdin failed: Unknown process id 1000
- **FAIL** `codex-core::all suite::network_approval::user_network_approval_once_session_and_denial_semantics` — expected network approval request before completion
- **FAIL** `codex-core::all suite::request_permissions::partial_request_permissions_grants_do_not_preapprove_new_permissions` — assertion failed: `(left == right)`
- **FAIL** `codex-core::all suite::request_permissions::relative_additional_permissions_resolve_against_tool_workdir::exec_command` — unexpected exit code/output: Some(134)
- **FAIL** `codex-core::all suite::request_permissions::relative_additional_permissions_resolve_against_tool_workdir::shell_command` — touch command should create requested path
- **FAIL** `codex-core::all suite::request_permissions::request_permissions_grants_apply_to_later_exec_command_calls` — assertion failed: `(left == right)`
- **FAIL** `codex-core::all suite::request_permissions::with_additional_permissions_requires_approval_under_on_request` — touch command should create requested path
- **FAIL** `codex-core::all suite::request_permissions::workspace_write_with_additional_permissions_can_write_outside_cwd` — assertion failed: result.stdout.contains("outside-cwd-ok")
- **FAIL** `codex-core::all suite::search_tool::tool_search_indexes_only_enabled_non_app_mcp_tools` — Verifications failed:
- **FAIL** `codex-core::all suite::search_tool::tool_search_surfaced_mcp_tool_errors_are_returned_to_model` — Verifications failed:
- **FAIL** `codex-core::all suite::search_tool::tool_search_uses_non_app_mcp_server_instructions_as_namespace_description` — Verifications failed:
- **FAIL** `codex-core::all suite::tools::sandbox_denied_shell_command_returns_original_output` — Error: exit code prefix present
- **FAIL** `codex-core::all suite::tools::shell_command_enforces_glob_deny_read_policy` — Error: exit code prefix present
- **FAIL** `codex-core::all suite::unified_exec::unified_exec_enforces_glob_deny_read_policy` — expected allowed file contents in unified exec output: ParsedUnifiedExecOutput { chunk_id: Some("c250b8"), wall_time_seconds: 0.6757, process_id: None, exit_code: Some(134), original_token_count: Some(0), output: "" }
- **FAIL** `codex-core::all suite::unified_exec::unified_exec_network_denial_emits_failed_background_end_event` — assertion failed: `(left == right)`
- **FAIL** `codex-core::all suite::unified_exec::unified_exec_runs_under_sandbox` — regex did not match actual value
- **FAIL** `codex-core::all suite::unified_exec::unified_exec_short_lived_network_denial_emits_failed_end_event` — assertion failed: `(left == right)`

## Sandbox or runner limitation — project-run-only differential

- **FAIL** `codex-core::all suite::unified_exec::unified_exec_formats_large_output_summary` — regex did not match during the broad candidate project run; the exact test then passed three of three times on the candidate and three of three times on upstream in one shared runner/cache. Classified as a concurrency or run-order flake, not Patch 1.

## Upstream-only differential failure

- **FAIL** `codex-core::all suite::compact_resume_fork::snapshot_rollback_followup_turn_trims_context_updates` — timeout waiting for event during the broad upstream project run; the exact test then passed three of three times on the candidate and three of three times on upstream in the same shared runner/cache. Classified as a concurrency or run-order flake.

## Code-mode and unified-exec focus

- Eleven existing `suite::code_mode` tests failed; all eleven failed because `test_stdio_server` was absent, and all eleven failed identically on upstream.
- The three new Patch 1 code-mode unit tests passed.
- The five dedicated `code_mode_orphan_sessions` acceptance tests passed in the separate named-target run.
- Four existing `suite::unified_exec` failures reproduced on upstream.
- One existing unified-exec test, `unified_exec_formats_large_output_summary`, failed only in the broad candidate project run. It subsequently passed three of three focused runs on each ref in one shared runner/cache, so it is classified as a concurrency/run-order flake rather than Patch 1.

## Evidence-based conclusion

The full upstream comparison reproduced 93 of the candidate's 94 failed-test names and the single timeout. The sole candidate-only failure and sole upstream-only failure both disappeared in focused reruns: each test passed six of six total executions across the two refs, with three executions per ref in the same runner/cache. All Patch 1-added tests passed. There are therefore no candidate failures left classified as potentially related or unclassified. The broad project command remains red because its generic hosted-runner environment does not provide required helper binaries and does not support several sandbox-sensitive suites reliably.

## Raw evidence

- Candidate Actions run: https://github.com/teamleaderleo/codex/actions/runs/30187752834
- Candidate artifact: `agent1-clean-candidate-verification`, artifact ID `8627702233`, digest `sha256:ec74788834d70deba61c35bb21f74d558f64680850537956084b86a223203736`.
- Upstream Actions run: https://github.com/teamleaderleo/codex/actions/runs/30188725567
- Upstream artifact: `agent1-upstream-base-project-test`, artifact ID `8627945626`, digest `sha256:0d74a72b85d8ef9f99e7e854a847c12148d386c8a91f8524487162933ea668b3`.
- Candidate raw log inside artifact: `project_tests.log`.
- Upstream raw log inside artifact: `upstream-project-tests.log`.
- Upstream nextest listing inside artifact: `upstream-nextest-list.json`.
- Focused differential run: https://github.com/teamleaderleo/codex/actions/runs/30189231784
- Focused differential artifact: `agent1-focused-differential`, artifact ID `8628058918`, digest `sha256:67ed58e7d2f37636ac70a72e933b61e1b1da8a5d3ede5b37c14a730babc83258`.
- Focused result: both differential tests passed 3/3 on the candidate and 3/3 on upstream in one runner with one Cargo target cache.

## Runner and cache availability

The original candidate runner is not still available. GitHub-hosted runners are ephemeral. The upstream comparison used the same runner image class, setup action, tool versions, environment variables, and command, but a fresh VM and fresh Cargo target directory; no `actions/cache` cache was persisted between those two full project runs. The focused two-test differential uses one new runner and one shared Cargo target directory across both refs.
