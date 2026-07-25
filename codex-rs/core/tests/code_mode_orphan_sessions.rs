#![allow(clippy::expect_used, clippy::unwrap_used)]

use anyhow::Result;
use anyhow::ensure;
use codex_core::CodexThread;
use codex_features::Feature;
use core_test_support::responses;
use core_test_support::responses::ResponseMock;
use core_test_support::responses::ResponsesRequest;
use core_test_support::responses::ev_assistant_message;
use core_test_support::responses::ev_completed;
use core_test_support::responses::ev_custom_tool_call;
use core_test_support::responses::ev_response_created;
use core_test_support::responses::sse;
use core_test_support::skip_if_no_network;
use core_test_support::test_codex::TestCodex;
use core_test_support::test_codex::test_codex;
use futures::FutureExt;
use serde_json::Value;
use std::panic::AssertUnwindSafe;
use wiremock::MockServer;

fn custom_tool_output_items(req: &ResponsesRequest, call_id: &str) -> Vec<Value> {
    match req.custom_tool_call_output(call_id).get("output") {
        Some(Value::Array(items)) => items.clone(),
        Some(Value::String(text)) => {
            vec![serde_json::json!({ "type": "input_text", "text": text })]
        }
        _ => panic!("custom tool output should be serialized as text or content items"),
    }
}

fn text_item(items: &[Value], index: usize) -> &str {
    items[index]
        .get("text")
        .and_then(Value::as_str)
        .expect("content item should be input_text")
}

fn sorted_process_ids<'a>(ids: impl IntoIterator<Item = &'a str>) -> Vec<i32> {
    let mut ids = ids
        .into_iter()
        .map(|id| id.parse::<i32>().expect("terminal process ID should be numeric"))
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

fn assert_live_session_ids_in_numeric_order(header: &str, process_ids: &[i32]) {
    assert!(
        !process_ids.is_empty(),
        "acceptance assertion requires at least one live process ID"
    );
    assert!(
        process_ids.windows(2).all(|pair| pair[0] < pair[1]),
        "expected process IDs to be supplied in deterministic numeric order: {process_ids:?}"
    );

    let tokens = numeric_tokens(header);
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
                "outer status should contain live session ID {process_id} exactly once: {header:?}"
            );
            matches[0]
        })
        .collect::<Vec<_>>();

    assert!(
        positions.windows(2).all(|pair| pair[0] < pair[1]),
        "outer status should list live session IDs in numeric order: ids={process_ids:?}, header={header:?}"
    );
}

fn assert_process_ids_absent(header: &str, process_ids: &[i32]) {
    let tokens = numeric_tokens(header);
    for process_id in process_ids {
        let expected = process_id.to_string();
        assert!(
            !tokens.iter().any(|token| *token == expected),
            "non-completion status should not disclose nested process ID {process_id}: {header:?}"
        );
    }
}

async fn run_code_mode_turn(
    server: &MockServer,
    prompt: &str,
    code: &str,
) -> Result<(TestCodex, ResponseMock)> {
    responses::mount_sse_once(
        server,
        sse(vec![
            ev_response_created("resp-1"),
            ev_custom_tool_call("call-1", "exec", code),
            ev_completed("resp-1"),
        ]),
    )
    .await;
    let follow_up_mock = responses::mount_sse_once(
        server,
        sse(vec![
            ev_assistant_message("msg-1", "done"),
            ev_completed("resp-2"),
        ]),
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
    let test = builder.build(server).await?;
    test.submit_turn(prompt).await?;
    Ok((test, follow_up_mock))
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

async fn finish_with_cleanup(
    codex: &CodexThread,
    body: std::thread::Result<Result<()>>,
) -> Result<()> {
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

#[cfg_attr(windows, ignore = "no exec_command on Windows")]
#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn code_mode_completion_surfaces_discarded_live_exec_sessions() -> Result<()> {
    skip_if_no_network!(Ok(()));

    let server = responses::start_mock_server().await;
    let (test, follow_up_mock) = run_code_mode_turn(
        &server,
        "start two nested commands and discard their session IDs",
        r#"
const outputs = (await Promise.all([
  tools.exec_command({ cmd: "printf orphan-a; sleep 60", yield_time_ms: 250 }),
  tools.exec_command({ cmd: "printf orphan-b; sleep 60", yield_time_ms: 250 }),
])).map(({ output }) => output);
text(outputs.join("|"));
"#,
    )
    .await?;

    let body = AssertUnwindSafe(async {
        let terminals = test.codex.list_background_terminals().await;
        assert_eq!(
            terminals.len(),
            2,
            "both yielded nested commands should remain alive after the cell completes: {terminals:?}"
        );
        let process_ids =
            sorted_process_ids(terminals.iter().map(|terminal| terminal.process_id.as_str()));

        let request = follow_up_mock.single_request();
        let items = custom_tool_output_items(&request, "call-1");
        assert_eq!(items.len(), 2, "expected status header and emitted text");
        let header = text_item(&items, 0);
        assert!(
            header.starts_with("Script completed\nWall time "),
            "outer result should retain the completion header: {header:?}"
        );
        assert_live_session_ids_in_numeric_order(header, &process_ids);
        assert_eq!(text_item(&items, 1), "orphan-a|orphan-b");

        Ok::<(), anyhow::Error>(())
    })
    .catch_unwind()
    .await;

    finish_with_cleanup(test.codex.as_ref(), body).await
}

#[cfg_attr(windows, ignore = "no exec_command on Windows")]
#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn code_mode_completion_reports_only_surviving_nested_session() -> Result<()> {
    skip_if_no_network!(Ok(()));

    let server = responses::start_mock_server().await;
    let (test, follow_up_mock) = run_code_mode_turn(
        &server,
        "let one yielded nested command exit before the cell completes",
        r#"
const outputs = (await Promise.all([
  tools.exec_command({ cmd: "printf short; sleep 0.2", yield_time_ms: 10 }),
  tools.exec_command({ cmd: "printf survivor; sleep 60", yield_time_ms: 10 }),
])).map(({ output }) => output);
await tools.exec_command({ cmd: "sleep 1" });
text(outputs.join("|"));
"#,
    )
    .await?;

    let body = AssertUnwindSafe(async {
        let terminals = test.codex.list_background_terminals().await;
        assert_eq!(
            terminals.len(),
            1,
            "only the long-lived nested command should survive cell completion: {terminals:?}"
        );
        let process_ids =
            sorted_process_ids(terminals.iter().map(|terminal| terminal.process_id.as_str()));

        let request = follow_up_mock.single_request();
        let items = custom_tool_output_items(&request, "call-1");
        let header = text_item(&items, 0);
        assert_live_session_ids_in_numeric_order(header, &process_ids);
        assert_eq!(text_item(&items, 1), "short|survivor");

        Ok::<(), anyhow::Error>(())
    })
    .catch_unwind()
    .await;

    finish_with_cleanup(test.codex.as_ref(), body).await
}

#[cfg_attr(windows, ignore = "no exec_command on Windows")]
#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn large_emitted_output_does_not_truncate_live_session_warning() -> Result<()> {
    skip_if_no_network!(Ok(()));

    let server = responses::start_mock_server().await;
    let (test, follow_up_mock) = run_code_mode_turn(
        &server,
        "emit a large payload after yielding a nested command",
        r#"
await tools.exec_command({ cmd: "printf large; sleep 60", yield_time_ms: 10 });
text("x".repeat(65536));
"#,
    )
    .await?;

    let body = AssertUnwindSafe(async {
        let terminals = test.codex.list_background_terminals().await;
        assert_eq!(
            terminals.len(),
            1,
            "the yielded nested command should remain live: {terminals:?}"
        );
        let process_ids =
            sorted_process_ids(terminals.iter().map(|terminal| terminal.process_id.as_str()));

        let request = follow_up_mock.single_request();
        let items = custom_tool_output_items(&request, "call-1");
        assert_eq!(items.len(), 2, "expected status header and emitted text");
        assert_live_session_ids_in_numeric_order(text_item(&items, 0), &process_ids);
        assert!(
            text_item(&items, 1).starts_with("xxxxxxxx"),
            "large emitted output should remain a separate content item"
        );

        Ok::<(), anyhow::Error>(())
    })
    .catch_unwind()
    .await;

    finish_with_cleanup(test.codex.as_ref(), body).await
}

#[cfg_attr(windows, ignore = "no exec_command on Windows")]
#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn yielded_cell_response_does_not_include_completion_session_warning() -> Result<()> {
    skip_if_no_network!(Ok(()));

    let server = responses::start_mock_server().await;
    let (test, follow_up_mock) = run_code_mode_turn(
        &server,
        "yield an ordinary running code-mode cell",
        r#"
await tools.exec_command({ cmd: "sleep 60", yield_time_ms: 250 });
await new Promise(() => {});
"#,
    )
    .await?;

    let body = AssertUnwindSafe(async {
        let terminals = test.codex.list_background_terminals().await;
        assert_eq!(
            terminals.len(),
            1,
            "the yielded cell should retain its nested background terminal: {terminals:?}"
        );
        let process_ids =
            sorted_process_ids(terminals.iter().map(|terminal| terminal.process_id.as_str()));

        let request = follow_up_mock.single_request();
        let items = custom_tool_output_items(&request, "call-1");
        let header = text_item(&items, 0);
        assert!(
            header.starts_with("Script running with cell ID "),
            "expected an ordinary yielded-cell status, got {header:?}"
        );
        assert_process_ids_absent(header, &process_ids);

        Ok::<(), anyhow::Error>(())
    })
    .catch_unwind()
    .await;

    finish_with_cleanup(test.codex.as_ref(), body).await
}
