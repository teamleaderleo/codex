from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 anchor, found {count}")
    return text.replace(old, new)


path = Path("codex-rs/app-server/tests/suite/v2/mcp_tool.rs")
text = path.read_text(encoding="utf-8")
text = replace_once(
    text,
    "use std::sync::Arc;\n",
    "use std::sync::Arc;\nuse std::sync::atomic::AtomicUsize;\nuse std::sync::atomic::Ordering;\n",
    "atomic imports",
)

test_anchor = '''#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn mcp_server_tool_call_returns_tool_result() -> Result<()> {
'''
test_block = '''#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn mcp_server_refresh_request_reconnects_ready_thread_clients() -> Result<()> {
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
    let initial_attempts = initialize_attempts.load(Ordering::SeqCst);
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

    mcp_server_handle.abort();
    let _ = mcp_server_handle.await;
    Ok(())
}

'''
text = replace_once(text, test_anchor, test_block + test_anchor, "app-server refresh test")

helper_anchor = '''pub(super) async fn start_mcp_server() -> Result<(String, JoinHandle<()>)> {
'''
helper = '''async fn start_counting_mcp_server() -> Result<(String, JoinHandle<()>, Arc<AtomicUsize>)> {
    let listener = TcpListener::bind("127.0.0.1:0").await?;
    let addr = listener.local_addr()?;
    let initialize_attempts = Arc::new(AtomicUsize::new(0));
    let attempts_for_service = Arc::clone(&initialize_attempts);
    let mcp_service = StreamableHttpService::new(
        move || {
            attempts_for_service.fetch_add(1, Ordering::SeqCst);
            Ok(ToolAppsMcpServer)
        },
        Arc::new(LocalSessionManager::default()),
        StreamableHttpServerConfig::default(),
    );
    let router = Router::new().nest_service("/mcp", mcp_service);

    let handle = tokio::spawn(async move {
        let _ = axum::serve(listener, router).await;
    });
    Ok((format!("http://{addr}/mcp"), handle, initialize_attempts))
}

'''
text = replace_once(text, helper_anchor, helper + helper_anchor, "counting MCP server helper")
path.write_text(text, encoding="utf-8")
