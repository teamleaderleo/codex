#!/usr/bin/env python3
from __future__ import annotations

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
                    // Responses Lite carries its tool manifest in the input prefix. The first
                    // generated turn must transmit that prefix directly instead of relying on a
                    // generate=false prewarm response to retain capability state.
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
async fn websocket_first_responses_lite_turn_sends_full_manifest_after_startup_prewarm() -> Result<()>
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
    let turn = connection
        .get(1)
        .expect("missing Responses Lite turn request")
        .body_json();

    assert_eq!(warmup["generate"].as_bool(), Some(false));
    assert_eq!(warmup["input"][0]["type"].as_str(), Some("additional_tools"));
    assert!(
        warmup["input"][0]["tools"]
            .as_array()
            .is_some_and(|tools| !tools.is_empty()),
        "prewarm should carry a nonempty Responses Lite tool manifest"
    );

    assert_eq!(turn.get("previous_response_id"), None);
    assert_eq!(turn.get("tools"), None);
    assert_eq!(turn["input"][0]["type"].as_str(), Some("additional_tools"));
    assert!(
        turn["input"][0]["tools"]
            .as_array()
            .is_some_and(|tools| !tools.is_empty()),
        "first generated Responses Lite turn should retransmit the tool manifest"
    );

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

client_reuse_test = r'''
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
    let first_generated = connection
        .get(1)
        .expect("missing first generated Responses Lite request")
        .body_json();
    let continuation = connection
        .get(2)
        .expect("missing Responses Lite continuation request")
        .body_json();

    assert_eq!(first_generated.get("previous_response_id"), None);
    assert_eq!(
        first_generated["input"][0]["type"].as_str(),
        Some("additional_tools")
    );
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

'''

replace_exact(
    CLIENT_WS_TESTS,
    """#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn responses_websocket_request_prewarm_uses_caller_supplied_metadata() {
""",
    client_reuse_test
    + """#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn responses_websocket_request_prewarm_uses_caller_supplied_metadata() {
""",
    "Responses Lite generated-response reuse regression insertion",
)
