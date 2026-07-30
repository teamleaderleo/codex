#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / "codex-rs" / "core" / "src" / "client.rs"
AGENT_WS_TESTS = ROOT / "codex-rs" / "core" / "tests" / "suite" / "agent_websocket.rs"
CLIENT_WS_TESTS = ROOT / "codex-rs" / "core" / "tests" / "suite" / "client_websockets.rs"


def replace_exact(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one exact match, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_exact(
    CLIENT,
    """            let (incremental_request, previous_response_id_from_untraced_warmup) =
                self.prepare_websocket_request(&request);
""",
    """            let force_full_after_responses_lite_prewarm = !warmup
                && model_info.use_responses_lite
                && self.websocket_session.last_response_from_untraced_warmup;
            let (incremental_request, previous_response_id_from_untraced_warmup) =
                if force_full_after_responses_lite_prewarm {
                    // Responses Lite carries its tool manifest in the input prefix. End the
                    // untraced warmup chain so the first generated turn sends its current
                    // request identity in full and any retry remains independent of warmup state.
                    self.websocket_session.last_response_rx = None;
                    (None, false)
                } else {
                    self.prepare_websocket_request(&request)
                };
""",
    "websocket request preparation",
)

agent_test = r'''
#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn websocket_first_responses_lite_turn_sends_exact_current_request_after_startup_prewarm() -> Result<()>
{
    skip_if_no_network!(Ok(()));

    let server = start_websocket_server(vec![vec![
        vec![ev_response_created("warm-1"), ev_completed("warm-1")],
        vec![
            ev_response_created("resp-1"),
            ev_assistant_message("msg_1", "hello"),
            ev_completed("resp-1"),
        ],
    ]])
    .await;

    let mut builder = test_codex()
        .with_model_info_override("gpt-5.4", |model_info| {
            model_info.use_responses_lite = true;
            model_info.tool_mode = Some(ToolMode::CodeMode);
        })
        .with_model("gpt-5.4");
    let test = builder.build_with_websocket_server(&server).await?;
    test.submit_turn_with_policy("hello", test.config.legacy_sandbox_policy())
        .await?;

    assert_eq!(server.handshakes().len(), 1);
    let connection = server.single_connection();
    assert_eq!(connection.len(), 2);
    let warmup = connection
        .first()
        .expect("missing Responses Lite warmup request")
        .body_json();
    let generated = connection
        .get(1)
        .expect("missing Responses Lite generated request")
        .body_json();

    assert_eq!(warmup["generate"].as_bool(), Some(false));
    assert_eq!(warmup["input"][0]["type"].as_str(), Some("additional_tools"));
    assert!(
        warmup["input"][0]["tools"]
            .as_array()
            .is_some_and(|tools| !tools.is_empty()),
        "prewarm should carry a nonempty Responses Lite tool manifest"
    );

    assert_eq!(generated.get("previous_response_id"), None);
    assert_eq!(generated.get("tools"), None);
    assert_eq!(generated["input"], warmup["input"]);
    assert_eq!(generated["model"], warmup["model"]);
    assert_eq!(generated["reasoning"], warmup["reasoning"]);
    assert_eq!(generated["parallel_tool_calls"], warmup["parallel_tool_calls"]);

    server.shutdown().await;
    Ok(())
}

'''

replace_exact(
    AGENT_WS_TESTS,
    """#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn websocket_first_turn_handles_handshake_delay_with_startup_prewarm() -> Result<()> {
""",
    agent_test
    + """#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn websocket_first_turn_handles_handshake_delay_with_startup_prewarm() -> Result<()> {
""",
    "Responses Lite startup-prewarm regression insertion",
)

client_tests = r'''
#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn responses_lite_reuses_generated_response_after_full_first_turn() {
    skip_if_no_network!();

    let server = start_websocket_server(vec![vec![
        vec![ev_response_created("warm-1"), ev_completed("warm-1")],
        vec![
            ev_response_created("resp-1"),
            ev_assistant_message("msg_1", "assistant output"),
            ev_completed("resp-1"),
        ],
        vec![ev_response_created("resp-2"), ev_completed("resp-2")],
    ]])
    .await;

    let mut provider = websocket_provider(&server);
    provider.name = ModelProviderInfo::create_openai_provider(/*base_url*/ None).name;
    let harness = websocket_harness_with_provider_options(
        provider,
        /*runtime_metrics_enabled*/ true,
        /*concurrent_reasoning_summaries_enabled*/ true,
        /*enabled_features*/ &[],
    )
    .await;
    let mut lite_model_info = harness.model_info.clone();
    lite_model_info.use_responses_lite = true;
    let mut client_session = harness.client.new_session();
    let prompt_one = prompt_with_input(vec![message_item("hello")]);
    let prompt_two = prompt_with_input(vec![
        message_item("hello"),
        assistant_message_item("1", "assistant output"),
        message_item("second"),
    ]);

    client_session
        .prewarm_websocket(
            &prompt_one,
            &lite_model_info,
            &harness.session_telemetry,
            harness.effort.clone(),
            harness.summary,
            /*service_tier*/ None,
            &prewarm_metadata(&harness, /*turn_id*/ None),
        )
        .await
        .expect("Responses Lite websocket prewarm failed");
    stream_until_complete_with_model_info(
        &mut client_session,
        &harness,
        &prompt_one,
        &lite_model_info,
        "resp-1",
    )
    .await;
    stream_until_complete_with_model_info(
        &mut client_session,
        &harness,
        &prompt_two,
        &lite_model_info,
        "resp-2",
    )
    .await;

    assert_eq!(server.handshakes().len(), 1);
    let connection = server.single_connection();
    assert_eq!(connection.len(), 3);
    let warmup = connection
        .first()
        .expect("missing Responses Lite warmup request")
        .body_json();
    let first_generated = connection
        .get(1)
        .expect("missing first generated Responses Lite request")
        .body_json();
    let continuation = connection
        .get(2)
        .expect("missing Responses Lite continuation request")
        .body_json();

    assert_eq!(first_generated.get("previous_response_id"), None);
    assert_eq!(first_generated["input"], warmup["input"]);
    assert_eq!(first_generated["model"], warmup["model"]);
    assert_eq!(
        continuation["previous_response_id"].as_str(),
        Some("resp-1")
    );
    assert_eq!(
        continuation["input"],
        serde_json::to_value(&prompt_two.input[2..]).expect("serialize Lite continuation")
    );
    assert!(
        continuation["input"]
            .as_array()
            .is_some_and(|items| items.iter().all(|item| {
                item.get("type").and_then(serde_json::Value::as_str)
                    != Some("additional_tools")
            })),
        "ordinary continuation should not retransmit the full Lite manifest"
    );

    server.shutdown().await;
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn responses_lite_retries_full_first_turn_after_failed_generation() {
    skip_if_no_network!();

    let server = start_websocket_server(vec![
        vec![
            vec![ev_response_created("warm-1"), ev_completed("warm-1")],
            vec![json!({
                "type": "response.failed",
                "response": {
                    "error": {
                        "code": "invalid_prompt",
                        "message": "synthetic first-generation failure"
                    }
                }
            })],
        ],
        vec![vec![ev_response_created("resp-2"), ev_completed("resp-2")]],
    ])
    .await;

    let mut provider = websocket_provider(&server);
    provider.name = ModelProviderInfo::create_openai_provider(/*base_url*/ None).name;
    let harness = websocket_harness_with_provider_options(
        provider,
        /*runtime_metrics_enabled*/ true,
        /*concurrent_reasoning_summaries_enabled*/ true,
        /*enabled_features*/ &[],
    )
    .await;
    let mut lite_model_info = harness.model_info.clone();
    lite_model_info.use_responses_lite = true;
    let mut client_session = harness.client.new_session();
    let prompt = prompt_with_input(vec![message_item("hello")]);

    client_session
        .prewarm_websocket(
            &prompt,
            &lite_model_info,
            &harness.session_telemetry,
            harness.effort.clone(),
            harness.summary,
            /*service_tier*/ None,
            &prewarm_metadata(&harness, /*turn_id*/ None),
        )
        .await
        .expect("Responses Lite websocket prewarm failed");

    let responses_metadata = turn_metadata(&harness, /*turn_id*/ None);
    let mut failed_stream = client_session
        .stream(
            &prompt,
            &lite_model_info,
            &harness.session_telemetry,
            harness.effort.clone(),
            harness.summary,
            /*service_tier*/ None,
            &responses_metadata,
            &codex_rollout_trace::InferenceTraceContext::disabled(),
        )
        .await
        .expect("first generated websocket request should produce a stream");
    let mut saw_error = false;
    while let Some(event) = failed_stream.next().await {
        if event.is_err() {
            saw_error = true;
            break;
        }
    }
    assert!(saw_error, "expected first generated request to fail");

    stream_until_complete_with_model_info(
        &mut client_session,
        &harness,
        &prompt,
        &lite_model_info,
        "resp-2",
    )
    .await;

    assert_eq!(server.handshakes().len(), 2);
    let connections = server.connections();
    assert_eq!(connections.len(), 2);
    let first_connection = connections.first().expect("missing first connection");
    assert_eq!(first_connection.len(), 2);
    let warmup = first_connection
        .first()
        .expect("missing warmup request")
        .body_json();
    let failed_generated = first_connection
        .get(1)
        .expect("missing failed generated request")
        .body_json();
    let retry = connections
        .get(1)
        .and_then(|connection| connection.first())
        .expect("missing retried generated request")
        .body_json();

    assert_eq!(failed_generated.get("previous_response_id"), None);
    assert_eq!(failed_generated["input"], warmup["input"]);
    assert_eq!(retry.get("previous_response_id"), None);
    assert_eq!(retry["input"], failed_generated["input"]);
    assert_eq!(retry["model"], failed_generated["model"]);

    server.shutdown().await;
}

'''

replace_exact(
    CLIENT_WS_TESTS,
    """#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn responses_websocket_request_prewarm_uses_caller_supplied_metadata() {
""",
    client_tests
    + """#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn responses_websocket_request_prewarm_uses_caller_supplied_metadata() {
""",
    "Responses Lite client regression insertion",
)
