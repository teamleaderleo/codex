#![allow(clippy::expect_used, clippy::unwrap_used)]

use anyhow::Result;
use anyhow::ensure;
use codex_core::CodexThread;
use codex_features::Feature;
use core_test_support::responses;
use core_test_support::responses::ResponsesRequest;
use core_test_support::responses::ev_assistant_message;
use core_test_support::responses::ev_completed;
use core_test_support::responses::ev_custom_tool_call;
use core_test_support::responses::ev_response_created;
use core_test_support::responses::sse;
use core_test_support::skip_if_no_network;
use core_test_support::test_codex::test_codex;
use futures::FutureExt;
use serde_json::Value;
use std::collections::HashSet;
use std::panic::AssertUnwindSafe;

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

#[cfg_attr(windows, ignore = "no exec_command on Windows")]
#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn code_mode_completion_does_not_surface_discarded_live_exec_sessions() -> Result<()> {
    skip_if_no_network!(Ok(()));

    let server = responses::start_mock_server().await;
    responses::mount_sse_once(
        &server,
        sse(vec![
            ev_response_created("resp-1"),
            ev_custom_tool_call(
                "call-1",
                "exec",
                r#"
const outputs = (await Promise.all([
  tools.exec_command({ cmd: "printf orphan-a; sleep 60", yield_time_ms: 250 }),
  tools.exec_command({ cmd: "printf orphan-b; sleep 60", yield_time_ms: 250 }),
])).map(({ output }) => output);
text(outputs.join("|"));
"#,
            ),
            ev_completed("resp-1"),
        ]),
    )
    .await;
    let follow_up_mock = responses::mount_sse_once(
        &server,
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
    let test = builder.build(&server).await?;

    let body = AssertUnwindSafe(async {
        test.submit_turn("start two nested commands and discard their session IDs")
            .await?;

        let terminals = test.codex.list_background_terminals().await;
        assert_eq!(
            terminals.len(),
            2,
            "both yielded nested commands should remain alive after the cell completes: {terminals:?}"
        );
        let session_ids = terminals
            .iter()
            .map(|terminal| terminal.process_id.as_str())
            .collect::<HashSet<_>>();
        assert_eq!(session_ids.len(), 2, "sessions should have distinct IDs");

        let request = follow_up_mock.single_request();
        let items = custom_tool_output_items(&request, "call-1");
        assert_eq!(items.len(), 2, "expected status header and emitted text");
        let header = text_item(&items, 0);
        assert!(
            header.starts_with("Script completed\nWall time "),
            "outer result should claim terminal completion: {header:?}"
        );
        assert!(
            header.ends_with(" seconds\nOutput:\n"),
            "unexpected outer result header: {header:?}"
        );
        assert!(
            !header.contains("session"),
            "current outer status should omit the live nested sessions: {header:?}"
        );
        assert_eq!(text_item(&items, 1), "orphan-a|orphan-b");

        Ok::<(), anyhow::Error>(())
    })
    .catch_unwind()
    .await;

    let cleanup_result = terminate_all_background_terminals(test.codex.as_ref()).await;
    match body {
        Ok(result) => {
            cleanup_result?;
            result?;
        }
        Err(panic) => {
            if let Err(error) = cleanup_result {
                eprintln!("background terminal cleanup failed after panic: {error:#}");
            }
            std::panic::resume_unwind(panic);
        }
    }

    Ok(())
}
