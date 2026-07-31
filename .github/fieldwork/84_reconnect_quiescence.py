from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 anchor, found {count}")
    return text.replace(old, new)


path = Path("codex-rs/app-server/tests/suite/v2/mcp_tool.rs")
text = path.read_text(encoding="utf-8")

old_route_assertions = '''    let initial_attempts = initialize_attempts.load(Ordering::SeqCst);
    assert!(initial_attempts > 0);

    let refresh_id = mcp
        .send_raw_request("config/mcpServer/reload", None)
        .await?;
    let response: serde_json::Value =
        timeout(DEFAULT_READ_TIMEOUT, mcp.read_response(refresh_id)).await??;
    assert_eq!(response, json!({}));

    let final_attempts = timeout(DEFAULT_READ_TIMEOUT, async {
        loop {
            let attempts = initialize_attempts.load(Ordering::SeqCst);
            if attempts > initial_attempts {
                break attempts;
            }
            tokio::time::sleep(Duration::from_millis(10)).await;
        }
    })
    .await?;
    assert_eq!(final_attempts, initial_attempts + 1);
'''
new_route_assertions = '''    tokio::time::sleep(Duration::from_millis(250)).await;
    let initial_attempts = initialize_attempts.load(Ordering::SeqCst);
    assert_eq!(initial_attempts, 1, "ready client should initialize exactly once");

    let refresh_id = mcp
        .send_raw_request("config/mcpServer/reload", None)
        .await?;
    let response: serde_json::Value =
        timeout(DEFAULT_READ_TIMEOUT, mcp.read_response(refresh_id)).await??;
    assert_eq!(response, json!({}));

    let expected_attempts = initial_attempts + 1;
    timeout(DEFAULT_READ_TIMEOUT, async {
        loop {
            let attempts = initialize_attempts.load(Ordering::SeqCst);
            assert!(
                attempts <= expected_attempts,
                "reload initialized more than one replacement client: {attempts}"
            );
            if attempts == expected_attempts {
                break;
            }
            tokio::time::sleep(Duration::from_millis(10)).await;
        }
    })
    .await?;
    tokio::time::sleep(Duration::from_millis(250)).await;
    assert_eq!(
        initialize_attempts.load(Ordering::SeqCst),
        expected_attempts,
        "reload should settle after exactly one replacement initialization"
    );
'''
text = replace_once(
    text,
    old_route_assertions,
    new_route_assertions,
    "route quiescence assertions",
)

next_test_anchor = '''#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn mcp_server_tool_call_returns_tool_result() -> Result<()> {
'''
negative_test = '''#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn mcp_server_reload_config_failure_does_not_reconnect_ready_thread_clients() -> Result<()> {
    let responses_server = responses::start_mock_server().await;
    let (mcp_server_url, mcp_server_handle, initialize_attempts) =
        start_counting_mcp_server().await?;
    let codex_home = TempDir::new()?;
    mcp_tool_config(&responses_server.uri(), &mcp_server_url, AUTO_COMPACT_LIMIT)
        .write(codex_home.path())?;

    let mut mcp = TestAppServer::builder()
        .with_codex_home(codex_home.path())
        .build_initialized()
        .await?;
    let ThreadStartResponse { thread, .. } = mcp
        .start_thread(ThreadStartParams {
            model: Some("mock-model".to_string()),
            ..Default::default()
        })
        .await?;

    let _: McpServerToolCallResponse = mcp
        .request(|request_id| ClientRequest::McpServerToolCall {
            request_id,
            params: McpServerToolCallParams {
                thread_id: thread.id,
                server: TEST_SERVER_NAME.to_string(),
                tool: TEST_TOOL_NAME.to_string(),
                arguments: Some(json!({"message": "prime ready client"})),
                meta: None,
            },
        })
        .await?;
    tokio::time::sleep(Duration::from_millis(250)).await;
    assert_eq!(
        initialize_attempts.load(Ordering::SeqCst),
        1,
        "ready client should initialize exactly once before failed reload"
    );

    std::fs::write(codex_home.path().join("config.toml"), "[mcp_servers.invalid\n")?;
    let reload_id = mcp
        .send_raw_request("config/mcpServer/reload", None)
        .await?;
    let error = timeout(
        DEFAULT_READ_TIMEOUT,
        mcp.read_stream_until_error_message(RequestId::Integer(reload_id)),
    )
    .await??;
    assert!(!error.error.message.is_empty());

    tokio::time::sleep(Duration::from_millis(250)).await;
    assert_eq!(
        initialize_attempts.load(Ordering::SeqCst),
        1,
        "failed reload planning must not reconnect the ready client"
    );

    mcp_server_handle.abort();
    let _ = mcp_server_handle.await;
    Ok(())
}

'''
text = replace_once(
    text,
    next_test_anchor,
    negative_test + next_test_anchor,
    "failed reload negative control",
)

path.write_text(text, encoding="utf-8")
