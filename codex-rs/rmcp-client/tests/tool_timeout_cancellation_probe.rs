use std::io;
use std::sync::Arc;
use std::sync::atomic::AtomicBool;
use std::sync::atomic::Ordering;
use std::time::Duration;

use codex_rmcp_client::ElicitationAction;
use codex_rmcp_client::ElicitationResponse;
use codex_rmcp_client::InProcessTransportFactory;
use codex_rmcp_client::RmcpClient;
use futures::FutureExt as _;
use futures::future::BoxFuture;
use rmcp::ErrorData as McpError;
use rmcp::ServerHandler;
use rmcp::ServiceExt;
use rmcp::model::CallToolRequestParams;
use rmcp::model::CallToolResult;
use rmcp::model::ClientCapabilities;
use rmcp::model::ContentBlock;
use rmcp::model::Implementation;
use rmcp::model::InitializeRequestParams;
use rmcp::model::ProtocolVersion;
use rmcp::model::ServerCapabilities;
use rmcp::model::ServerInfo;
use rmcp::service::RequestContext;
use rmcp::service::RoleServer;
use serde_json::json;
use tokio::io::DuplexStream;
use tokio::sync::Notify;

const CLIENT_TIMEOUT: Duration = Duration::from_millis(40);
const SERVER_WORK: Duration = Duration::from_millis(160);

#[derive(Clone, Default)]
struct ProbeState {
    started: Arc<Notify>,
    cancellation_observed: Arc<AtomicBool>,
    side_effect_completed: Arc<AtomicBool>,
}

#[derive(Clone)]
struct TimeoutProbeServer {
    state: ProbeState,
}

impl ServerHandler for TimeoutProbeServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo::new(ServerCapabilities::builder().enable_tools().build())
    }

    async fn call_tool(
        &self,
        request: CallToolRequestParams,
        context: RequestContext<RoleServer>,
    ) -> Result<rmcp::model::CallToolResponse, McpError> {
        match request.name.as_ref() {
            "slow_mutation" => {
                self.state.started.notify_one();
                tokio::select! {
                    () = context.ct.cancelled() => {
                        self.state
                            .cancellation_observed
                            .store(true, Ordering::SeqCst);
                        Ok(CallToolResult::success(vec![ContentBlock::text("cancelled")]).into())
                    }
                    () = tokio::time::sleep(SERVER_WORK) => {
                        self.state
                            .side_effect_completed
                            .store(true, Ordering::SeqCst);
                        Ok(CallToolResult::success(vec![ContentBlock::text("mutation completed")]).into())
                    }
                }
            }
            "ping" => Ok(CallToolResult::success(vec![ContentBlock::text("pong")]).into()),
            other => Err(McpError::invalid_params(
                format!("unknown probe tool: {other}"),
                None,
            )),
        }
    }
}

#[derive(Clone)]
struct TimeoutProbeTransportFactory {
    server: TimeoutProbeServer,
}

impl InProcessTransportFactory for TimeoutProbeTransportFactory {
    fn open(&self) -> BoxFuture<'static, io::Result<DuplexStream>> {
        let server = self.server.clone();
        async move {
            let (client_stream, server_stream) = tokio::io::duplex(4096);
            tokio::spawn(async move {
                server
                    .serve(server_stream)
                    .await
                    .expect("serve timeout probe MCP server")
                    .waiting()
                    .await
                    .expect("timeout probe MCP server completes");
            });
            Ok(client_stream)
        }
        .boxed()
    }
}

fn init_params() -> InitializeRequestParams {
    InitializeRequestParams::new(
        ClientCapabilities::default(),
        Implementation::new("codex-timeout-probe", "0.0.0-test"),
    )
    .with_protocol_version(ProtocolVersion::V_2025_06_18)
}

async fn initialized_client(state: ProbeState) -> anyhow::Result<RmcpClient> {
    let client = RmcpClient::new_in_process_client(Arc::new(TimeoutProbeTransportFactory {
        server: TimeoutProbeServer { state },
    }))
    .await?;

    client
        .initialize(
            init_params(),
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
async fn codex_timeout_drops_the_wait_but_does_not_cancel_the_legacy_request() -> anyhow::Result<()> {
    let state = ProbeState::default();
    let client = initialized_client(state.clone()).await?;

    let error = client
        .call_tool(
            "slow_mutation".to_string(),
            Some(json!({})),
            /*meta*/ None,
            Some(CLIENT_TIMEOUT),
        )
        .await
        .expect_err("the Codex-owned timeout should expire first");

    assert!(
        error.to_string().contains("timed out awaiting tools/call"),
        "unexpected timeout error: {error:#}"
    );

    tokio::time::timeout(Duration::from_secs(1), state.started.notified()).await?;
    tokio::time::sleep(SERVER_WORK + Duration::from_millis(40)).await;

    assert!(
        !state.cancellation_observed.load(Ordering::SeqCst),
        "current Codex timeout unexpectedly sent MCP cancellation"
    );
    assert!(
        state.side_effect_completed.load(Ordering::SeqCst),
        "the server-side operation should continue after the caller timeout"
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
    Ok(())
}
