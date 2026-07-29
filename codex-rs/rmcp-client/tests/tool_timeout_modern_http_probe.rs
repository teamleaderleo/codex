use std::convert::Infallible;
use std::pin::Pin;
use std::sync::Arc;
use std::sync::atomic::AtomicBool;
use std::sync::atomic::Ordering;
use std::task::Context;
use std::task::Poll;
use std::time::Duration;

use axum::Json;
use axum::Router;
use axum::body::Body;
use axum::extract::State;
use axum::http::Response;
use axum::http::header::CONTENT_TYPE;
use axum::routing::post;
use bytes::Bytes;
use codex_config::types::AuthKeyringBackendKind;
use codex_config::types::OAuthCredentialsStoreMode;
use codex_exec_server::Environment;
use codex_rmcp_client::ElicitationAction;
use codex_rmcp_client::ElicitationResponse;
use codex_rmcp_client::McpProtocolMode;
use codex_rmcp_client::RmcpClient;
use futures::FutureExt as _;
use futures::Stream;
use rmcp::model::ClientCapabilities;
use rmcp::model::Implementation;
use rmcp::model::InitializeRequestParams;
use rmcp::model::ProtocolVersion;
use serde_json::Value;
use serde_json::json;
use tokio::net::TcpListener;
use tokio::sync::Notify;

const CLIENT_TIMEOUT: Duration = Duration::from_millis(40);
const MODERN_VERSION: &str = "2026-07-28";

#[derive(Clone, Default)]
struct ModernHttpProbeState {
    slow_request_seen: Arc<Notify>,
    slow_stream_dropped: Arc<AtomicBool>,
}

struct PendingSseBody {
    dropped: Arc<AtomicBool>,
}

impl Stream for PendingSseBody {
    type Item = Result<Bytes, Infallible>;

    fn poll_next(self: Pin<&mut Self>, _cx: &mut Context<'_>) -> Poll<Option<Self::Item>> {
        Poll::Pending
    }
}

impl Drop for PendingSseBody {
    fn drop(&mut self) {
        self.dropped.store(true, Ordering::SeqCst);
    }
}

fn sse_response(message: Value) -> Response<Body> {
    Response::builder()
        .status(200)
        .header(CONTENT_TYPE, "text/event-stream")
        .body(Body::from(format!("event: message\ndata: {message}\n\n")))
        .expect("valid SSE response")
}

fn pending_sse_response(dropped: Arc<AtomicBool>) -> Response<Body> {
    Response::builder()
        .status(200)
        .header(CONTENT_TYPE, "text/event-stream")
        .body(Body::from_stream(PendingSseBody { dropped }))
        .expect("valid pending SSE response")
}

async fn mcp_handler(
    State(state): State<ModernHttpProbeState>,
    Json(message): Json<Value>,
) -> Response<Body> {
    let method = message["method"].as_str().expect("JSON-RPC method");
    match method {
        "server/discover" => sse_response(json!({
            "jsonrpc": "2.0",
            "id": message["id"],
            "result": {
                "resultType": "complete",
                "supportedVersions": [MODERN_VERSION],
                "capabilities": {"tools": {}},
                "_meta": {
                    "io.modelcontextprotocol/serverInfo": {
                        "name": "modern-timeout-probe",
                        "version": "1.0.0"
                    }
                },
                "ttlMs": 0,
                "cacheScope": "private"
            }
        })),
        "tools/call" => {
            let tool = message["params"]["name"]
                .as_str()
                .expect("tools/call name");
            match tool {
                "slow_mutation" => {
                    state.slow_request_seen.notify_one();
                    pending_sse_response(Arc::clone(&state.slow_stream_dropped))
                }
                "ping" => sse_response(json!({
                    "jsonrpc": "2.0",
                    "id": message["id"],
                    "result": {
                        "resultType": "complete",
                        "content": [{"type": "text", "text": "pong"}]
                    }
                })),
                other => sse_response(json!({
                    "jsonrpc": "2.0",
                    "id": message["id"],
                    "error": {"code": -32602, "message": format!("unknown tool: {other}")}
                })),
            }
        }
        other => sse_response(json!({
            "jsonrpc": "2.0",
            "id": message.get("id").cloned().unwrap_or(Value::Null),
            "error": {"code": -32601, "message": format!("unexpected method: {other}")}
        })),
    }
}

async fn initialized_client(url: &str) -> anyhow::Result<RmcpClient> {
    let client = RmcpClient::new_streamable_http_client_with_protocol_mode(
        "modern-timeout-probe",
        url,
        /*bearer_token*/ None,
        /*http_headers*/ None,
        /*env_http_headers*/ None,
        OAuthCredentialsStoreMode::File,
        AuthKeyringBackendKind::default(),
        Environment::default_for_tests().get_http_client(),
        /*auth_provider*/ None,
        McpProtocolMode::V20260728,
    )
    .await?;

    client
        .initialize(
            InitializeRequestParams::new(
                ClientCapabilities::default(),
                Implementation::new("codex-modern-timeout-probe", "0.0.0-test"),
            )
            .with_protocol_version(ProtocolVersion::V_2025_06_18),
            Some(Duration::from_secs(2)),
            Box::new(|_, _| {
                async {
                    Ok(ElicitationResponse {
                        action: ElicitationAction::Decline,
                        content: Some(json!({})),
                        meta: None,
                    })
                }
                .boxed()
            }),
        )
        .await?;

    Ok(client)
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn modern_http_timeout_stream_closure_probe() -> anyhow::Result<()> {
    let state = ModernHttpProbeState::default();
    let listener = TcpListener::bind("127.0.0.1:0").await?;
    let address = listener.local_addr()?;
    let app = Router::new()
        .route("/mcp", post(mcp_handler))
        .with_state(state.clone());
    let server = tokio::spawn(async move { axum::serve(listener, app).await });

    let client = initialized_client(&format!("http://{address}/mcp")).await?;
    let error = client
        .call_tool(
            "slow_mutation".to_string(),
            Some(json!({})),
            /*meta*/ None,
            Some(CLIENT_TIMEOUT),
        )
        .await
        .expect_err("the configured timeout should expire first");
    assert!(
        error.to_string().contains("timed out awaiting tools/call")
            || error.to_string().contains("request timeout"),
        "unexpected timeout error: {error:#}"
    );

    tokio::time::timeout(Duration::from_secs(1), state.slow_request_seen.notified()).await?;
    tokio::time::sleep(Duration::from_millis(100)).await;

    let expect_stream_close =
        std::env::var_os("FIELDWORK_EXPECT_MODERN_STREAM_CLOSE").is_some();
    assert_eq!(
        state.slow_stream_dropped.load(Ordering::SeqCst),
        expect_stream_close,
        "modern request-stream closure did not match the selected implementation"
    );

    let follow_up = client
        .call_tool(
            "ping".to_string(),
            Some(json!({})),
            /*meta*/ None,
            Some(Duration::from_secs(1)),
        )
        .await?;
    assert_eq!(follow_up.content.len(), 1);

    client.shutdown().await;
    server.abort();
    let _ = server.await;
    Ok(())
}
