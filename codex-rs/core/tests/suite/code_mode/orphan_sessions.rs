#![allow(clippy::expect_used)]

use super::*;
use anyhow::ensure;
use codex_core::CodexThread;
use core_test_support::skip_if_remote;
use core_test_support::skip_if_target_windows;
use futures::FutureExt;
use pretty_assertions::assert_eq;
use std::future::Future;
use std::panic::AssertUnwindSafe;

const COMPLETED_PREFIX: &str = "Script completed\n";
const WALL_TIME_PREFIX: &str = "\nWall time ";
const BACKGROUND_SESSIONS_WARNING: &str = "Background sessions still running:";

fn sorted_process_ids<'a>(ids: impl IntoIterator<Item = &'a str>) -> Vec<i32> {
    let mut ids = ids
        .into_iter()
        .map(|id| {
            id.parse::<i32>()
                .expect("terminal process ID should be numeric")
        })
        .collect::<Vec<_>>();
    let original_len = ids.len();
    ids.sort_unstable();
    ids.dedup();
    assert_eq!(
        ids.len(),
        original_len,
        "background terminals should have distinct process IDs"
    );
    ids
}

fn numeric_tokens(text: &str) -> Vec<&str> {
    text.split(|character: char| !character.is_ascii_digit())
        .filter(|token| !token.is_empty())
        .collect()
}

fn assert_completed_prefix(header: &str) {
    assert!(
        header.starts_with(COMPLETED_PREFIX),
        "outer result should begin with the completion line: {header:?}"
    );
}

fn session_summary_before_wall_time(header: &str) -> &str {
    let wall_time_index = header
        .find(WALL_TIME_PREFIX)
        .expect("outer result should retain a wall-time line after the session summary");
    assert!(
        wall_time_index > COMPLETED_PREFIX.len(),
        "wall-time line should follow a non-empty session summary: {header:?}"
    );
    &header[COMPLETED_PREFIX.len()..wall_time_index]
}

fn assert_live_session_ids_in_numeric_order(summary: &str, process_ids: &[i32]) {
    assert!(
        !process_ids.is_empty(),
        "acceptance assertion requires at least one live process ID"
    );
    assert!(
        process_ids.windows(2).all(|pair| pair[0] < pair[1]),
        "expected process IDs to be supplied in deterministic numeric order: {process_ids:?}"
    );

    let tokens = numeric_tokens(summary);
    let positions = process_ids
        .iter()
        .map(|process_id| {
            let expected = process_id.to_string();
            let matches = tokens
                .iter()
                .enumerate()
                .filter_map(|(index, token)| (*token == expected).then_some(index))
                .collect::<Vec<_>>();
            assert_eq!(
                matches.len(),
                1,
                "session summary should contain live session ID {process_id} exactly once: {summary:?}"
            );
            matches[0]
        })
        .collect::<Vec<_>>();

    assert!(
        positions.windows(2).all(|pair| pair[0] < pair[1]),
        "session summary should list live session IDs in numeric order: ids={process_ids:?}, summary={summary:?}"
    );
}

fn assert_process_ids_absent(text: &str, process_ids: &[i32]) {
    let tokens = numeric_tokens(text);
    for process_id in process_ids {
        let expected = process_id.to_string();
        assert!(
            !tokens.iter().any(|token| *token == expected),
            "status should not disclose nested process ID {process_id}: {text:?}"
        );
    }
}

async fn terminate_all_background_terminals(codex: &CodexThread) -> Result<()> {
    let terminals = codex.list_background_terminals().await;
    let mut failures = Vec::new();

    for terminal in terminals {
        match terminal.process_id.parse::<i32>() {
            Ok(process_id) => {
                if !codex.terminate_background_terminal(process_id).await {
                    failures.push(format!("failed to terminate session {process_id}"));
                }
            }
            Err(error) => failures.push(format!(
                "invalid background session ID {}: {error}",
                terminal.process_id
            )),
        }
    }

    let remaining = codex.list_background_terminals().await;
    ensure!(
        failures.is_empty() && remaining.is_empty(),
        "background terminal cleanup failed: failures={failures:?}, remaining={remaining:?}"
    );
    Ok(())
}

async fn finish_with_cleanup<T>(
    codex: &CodexThread,
    body: std::thread::Result<Result<T>>,
) -> Result<T> {
    let cleanup_result = terminate_all_background_terminals(codex).await;
    match body {
        Ok(result) => {
            cleanup_result?;
            result
        }
        Err(panic) => {
            if let Err(error) = cleanup_result {
                eprintln!("background terminal cleanup failed after panic: {error:#}");
            }
            std::panic::resume_unwind(panic);
        }
    }
}

async fn run_with_background_terminal_cleanup<T>(
    test: &TestCodex,
    body: impl Future<Output = Result<T>>,
) -> Result<T> {
    let body = AssertUnwindSafe(body).catch_unwind().await;
    finish_with_cleanup(test.codex.as_ref(), body).await
}

#[cfg_attr(windows, ignore = "no exec_command on Windows")]
#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn code_mode_completion_surfaces_discarded_live_exec_sessions() -> Result<()> {
    skip_if_no_network!(Ok(()));
    skip_if_target_windows!(
        Ok(()),
        "test commands use POSIX shell syntax unsupported by the Windows exec target",
    );

    let server = responses::start_mock_server().await;
    let (test, follow_up_mock) = prepare_code_mode_turn_with_auto_env(
        &server,
        r#"
const outputs = (await Promise.all([
  tools.exec_command({ cmd: "printf orphan-a; sleep 60", yield_time_ms: 250 }),
  tools.exec_command({ cmd: "printf orphan-b; sleep 60", yield_time_ms: 250 }),
])).map(({ output }) => output);
text(outputs.join("|"));
"#,
    )
    .await?;

    run_with_background_terminal_cleanup(&test, async {
        test.submit_turn("start two nested commands and discard their session IDs")
            .await?;

        let terminals = test.codex.list_background_terminals().await;
        assert_eq!(
            terminals.len(),
            2,
            "both yielded nested commands should remain alive after the cell completes: {terminals:?}"
        );
        let process_ids = sorted_process_ids(
            terminals
                .iter()
                .map(|terminal| terminal.process_id.as_str()),
        );

        let request = follow_up_mock.single_request();
        let items = custom_tool_output_items(&request, "call-1");
        assert_eq!(items.len(), 2, "expected status header and emitted text");
        let header = text_item(&items, 0);
        assert_completed_prefix(header);
        let session_summary = session_summary_before_wall_time(header);
        assert_live_session_ids_in_numeric_order(session_summary, &process_ids);
        assert_eq!(text_item(&items, 1), "orphan-a|orphan-b");

        Ok(())
    })
    .await
}

#[cfg_attr(windows, ignore = "no exec_command on Windows")]
#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn code_mode_completion_reports_only_surviving_nested_session() -> Result<()> {
    skip_if_no_network!(Ok(()));
    // This case intentionally embeds host TempDir paths in shell commands. Those paths are not
    // shared with Docker or Wine executors, so forcing it remote would test an invalid filesystem
    // topology rather than natural process exit.
    skip_if_remote!(
        Ok(()),
        "PID/release paths use a host TempDir that is not shared with the remote executor",
    );

    let temp_dir = tempfile::TempDir::new()?;
    let pid_path = temp_dir.path().join("short.pid");
    let release_path = temp_dir.path().join("release");
    let pid_path = shlex::try_join([pid_path.to_string_lossy().as_ref()])?;
    let release_path = shlex::try_join([release_path.to_string_lossy().as_ref()])?;
    let short_command = format!(
        "printf '%s' \"$$\" > {pid_path}; printf short; \
         while [ ! -f {release_path} ]; do sleep 0.05; done"
    );
    let await_short_exit_command = format!(
        "touch {release_path}; \
         for _ in $(seq 1 100); do \
           if ! kill -0 \"$(cat {pid_path})\" 2>/dev/null; then \
             printf exited; exit 0; \
           fi; \
           sleep 0.05; \
         done; \
         printf timeout; exit 1"
    );
    let code = format!(
        r#"
const short = await tools.exec_command({{
  cmd: {short_command:?},
  yield_time_ms: 250,
}});
const survivor = await tools.exec_command({{
  cmd: "printf survivor; sleep 60",
  yield_time_ms: 250,
}});
const completion = await tools.exec_command({{
  cmd: {await_short_exit_command:?},
  yield_time_ms: 6000,
}});
if (completion.output !== "exited") {{
  throw new Error(`short session did not exit: ${{completion.output}}`);
}}
text([short.output, survivor.output].join("|"));
"#
    );

    let server = responses::start_mock_server().await;
    let (test, follow_up_mock) = prepare_code_mode_turn(&server, &code).await?;

    run_with_background_terminal_cleanup(&test, async {
        test.submit_turn("let one yielded nested command exit before the cell completes")
            .await?;

        let terminals = test.codex.list_background_terminals().await;
        assert_eq!(
            terminals.len(),
            1,
            "only the long-lived nested command should survive cell completion: {terminals:?}"
        );
        let process_ids = sorted_process_ids(
            terminals
                .iter()
                .map(|terminal| terminal.process_id.as_str()),
        );

        let request = follow_up_mock.single_request();
        let items = custom_tool_output_items(&request, "call-1");
        let header = text_item(&items, 0);
        assert_completed_prefix(header);
        let session_summary = session_summary_before_wall_time(header);
        assert_live_session_ids_in_numeric_order(session_summary, &process_ids);
        assert_eq!(text_item(&items, 1), "short|survivor");

        Ok(())
    })
    .await
}

#[cfg_attr(windows, ignore = "no exec_command on Windows")]
#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn large_emitted_output_does_not_truncate_live_session_warning() -> Result<()> {
    skip_if_no_network!(Ok(()));
    skip_if_target_windows!(
        Ok(()),
        "test commands use POSIX shell syntax unsupported by the Windows exec target",
    );

    let server = responses::start_mock_server().await;
    let (test, follow_up_mock) = prepare_code_mode_turn_with_auto_env(
        &server,
        r#"
await tools.exec_command({ cmd: "printf large; sleep 60", yield_time_ms: 250 });
text("x".repeat(65536));
"#,
    )
    .await?;

    run_with_background_terminal_cleanup(&test, async {
        test.submit_turn("emit a large payload after yielding a nested command")
            .await?;

        let terminals = test.codex.list_background_terminals().await;
        assert_eq!(
            terminals.len(),
            1,
            "the yielded nested command should remain live: {terminals:?}"
        );
        let process_ids = sorted_process_ids(
            terminals
                .iter()
                .map(|terminal| terminal.process_id.as_str()),
        );

        let request = follow_up_mock.single_request();
        let items = custom_tool_output_items(&request, "call-1");
        let header_index = items
            .iter()
            .position(|item| {
                item.get("text")
                    .and_then(Value::as_str)
                    .is_some_and(|text| text.starts_with(COMPLETED_PREFIX))
            })
            .expect("completion status header should remain a separate text item");
        let header = text_item(&items, header_index);
        assert_completed_prefix(header);
        assert!(
            header.contains(BACKGROUND_SESSIONS_WARNING),
            "status header should retain the live-session warning: {header:?}"
        );
        let session_summary = session_summary_before_wall_time(header);
        assert_live_session_ids_in_numeric_order(session_summary, &process_ids);

        // The emitted payload is intentionally above the default code-mode token limit. The
        // truncator may retain a head/tail excerpt or replace part of it with an omission marker;
        // this test only requires that some non-empty emitted output remains represented
        // separately from the untruncated status header.
        assert!(
            items.iter().enumerate().any(|(index, item)| {
                index != header_index
                    && item
                        .get("text")
                        .and_then(Value::as_str)
                        .is_some_and(|text| !text.is_empty())
            }),
            "large emitted output should remain represented separately after truncation: {items:?}"
        );

        Ok(())
    })
    .await
}

#[cfg_attr(windows, ignore = "no exec_command on Windows")]
#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn yielded_cell_response_does_not_include_completion_session_warning() -> Result<()> {
    skip_if_no_network!(Ok(()));
    skip_if_target_windows!(
        Ok(()),
        "test commands use POSIX shell syntax unsupported by the Windows exec target",
    );

    let server = responses::start_mock_server().await;
    let (test, follow_up_mock) = prepare_code_mode_turn_with_auto_env(
        &server,
        r#"
await tools.exec_command({ cmd: "sleep 60", yield_time_ms: 250 });
await new Promise(() => {});
"#,
    )
    .await?;

    run_with_background_terminal_cleanup(&test, async {
        test.submit_turn("yield an ordinary running code-mode cell")
            .await?;

        let terminals = test.codex.list_background_terminals().await;
        assert_eq!(
            terminals.len(),
            1,
            "the yielded cell should retain its nested background terminal: {terminals:?}"
        );

        let request = follow_up_mock.single_request();
        let items = custom_tool_output_items(&request, "call-1");
        let header = text_item(&items, 0);
        assert!(
            header.starts_with("Script running with cell ID "),
            "expected an ordinary yielded-cell status, got {header:?}"
        );
        assert!(
            !header.contains(BACKGROUND_SESSIONS_WARNING),
            "yielded output must not contain the completion-only background-session warning: {header:?}"
        );

        Ok(())
    })
    .await
}

#[cfg_attr(windows, ignore = "no exec_command on Windows")]
#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn code_mode_completion_reports_only_sessions_created_by_current_cell() -> Result<()> {
    skip_if_no_network!(Ok(()));
    skip_if_target_windows!(
        Ok(()),
        "test commands use POSIX shell syntax unsupported by the Windows exec target",
    );

    let server = responses::start_mock_server().await;
    let response_mock = responses::mount_sse_sequence(
        &server,
        vec![
            sse(vec![
                ev_response_created("resp-a-1"),
                ev_custom_tool_call(
                    "call-a",
                    "exec",
                    r#"
await tools.exec_command({ cmd: "printf cell-a; sleep 60", yield_time_ms: 250 });
text("cell-a");
"#,
                ),
                ev_completed("resp-a-1"),
            ]),
            sse(vec![
                ev_assistant_message("msg-a", "cell a done"),
                ev_completed("resp-a-2"),
            ]),
            sse(vec![
                ev_response_created("resp-b-1"),
                ev_custom_tool_call(
                    "call-b",
                    "exec",
                    r#"
await tools.exec_command({ cmd: "printf cell-b; sleep 60", yield_time_ms: 250 });
text("cell-b");
"#,
                ),
                ev_completed("resp-b-1"),
            ]),
            sse(vec![
                ev_assistant_message("msg-b", "cell b done"),
                ev_completed("resp-b-2"),
            ]),
        ],
    )
    .await;
    let mut builder = test_codex()
        .with_model("test-gpt-5.1-codex")
        .with_config(|config| {
            config
                .features
                .enable(Feature::CodeMode)
                .expect("code mode should be enabled");
        });
    let test = builder.build_with_auto_env(&server).await?;

    run_with_background_terminal_cleanup(&test, async {
        test.submit_turn("start a background process from cell A")
            .await?;
        let cell_a_terminals = test.codex.list_background_terminals().await;
        assert_eq!(
            cell_a_terminals.len(),
            1,
            "cell A should leave one live process: {cell_a_terminals:?}"
        );
        let cell_a_process_id = sorted_process_ids(
            cell_a_terminals
                .iter()
                .map(|terminal| terminal.process_id.as_str()),
        )[0];

        test.submit_turn("start a background process from cell B")
            .await?;
        let all_terminals = test.codex.list_background_terminals().await;
        assert_eq!(
            all_terminals.len(),
            2,
            "both cells should retain their own live process: {all_terminals:?}"
        );
        let all_process_ids = sorted_process_ids(
            all_terminals
                .iter()
                .map(|terminal| terminal.process_id.as_str()),
        );
        let cell_b_process_ids = all_process_ids
            .into_iter()
            .filter(|process_id| *process_id != cell_a_process_id)
            .collect::<Vec<_>>();
        assert_eq!(
            cell_b_process_ids.len(),
            1,
            "cell B should add exactly one distinct live process"
        );

        let request = response_mock
            .last_request()
            .expect("second cell should send its completion output");
        let items = custom_tool_output_items(&request, "call-b");
        assert_eq!(items.len(), 2, "expected status header and emitted text");
        let header = text_item(&items, 0);
        assert_completed_prefix(header);
        let session_summary = session_summary_before_wall_time(header);
        assert_live_session_ids_in_numeric_order(session_summary, &cell_b_process_ids);
        assert_process_ids_absent(session_summary, &[cell_a_process_id]);
        assert_eq!(text_item(&items, 1), "cell-b");

        Ok(())
    })
    .await
}
