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

const TIMED_CALL_TIMEOUT: Duration = Duration::from_millis(40);
const HEALTHY_CALL_WORK: Duration = Duration::from_millis(120);
const HEALTHY_CALL_TIMEOUT: Duration = Duration::from_secs(1);
const SLOW_CALL_WORK: Duration = Duration::from_millis(300);

#[derive(Clone, Default)]
struct ConcurrentProbeState {
    timed_request_cancelled: Arc<AtomicBool>,
    healthy_request_completed: Arc<AtomicBool>,
}

#[derive(Clone)]
struct ConcurrentProbeServer {
    state: ConcurrentProbeState,
}

impl ServerHandler for ConcurrentProbeServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo::new(ServerCapabilities::builder().enable_tools().build())
    }

    async fn call_tool(
        &self,
        request: CallToolRequestParams,
        context: RequestContext<RoleServer>,
    ) -> Result<rmcp::model::CallToolResponse, McpError> {
        match request.name.as_ref() {
            "timed_request" => {
                tokio::select! {
                    () = context.ct.cancelled() => {
                        self.state
                            .timed_request_cancelled
                            .store(true, Ordering::SeqCst);
                    }
                    () = tokio::time::sleep(SLOW_CALL_WORK) => {}
                }
                Ok(CallToolResult::success(vec![ContentBlock::text("timed request ended")]).into())
            }
            "healthy_request" => {
                tokio::time::sleep(HEALTHY_CALL_WORK).await;
                self.state
                    .healthy_request_completed
                    .store(true, Ordering::SeqCst);
                Ok(CallToolResult::success(vec![ContentBlock::text("healthy result")]).into())
            }
            other => Err(McpError::invalid_params(
                format!("unknown probe tool: {other}"),
                None,
            )),
        }
    }
}

#[derive(Clone)]
struct ConcurrentProbeTransportFactory {
    server: ConcurrentProbeServer,
}

impl InProcessTransportFactory for ConcurrentProbeTransportFactory {
    fn open(&self) -> BoxFuture<'static, io::Result<DuplexStream>> {
        let server = self.server.clone();
        async move {
            let (client_stream, server_stream) = tokio::io::duplex(4096);
            tokio::spawn(async move {
                server
                    .serve(server_stream)
                    .await
                    .expect("serve concurrent timeout probe MCP server")
                    .waiting()
                    .await
                    .expect("concurrent timeout probe MCP server completes");
            });
            Ok(client_stream)
        }
        .boxed()
    }
}

fn init_params() -> InitializeRequestParams {
    InitializeRequestParams::new(
        ClientCapabilities::default(),
        Implementation::new("codex-concurrent-timeout-probe", "0.0.0-test"),
    )
    .with_protocol_version(ProtocolVersion::V_2025_06_18)
}

async fn initialized_client(state: ConcurrentProbeState) -> anyhow::Result<RmcpClient> {
    let client = RmcpClient::new_in_process_client(Arc::new(ConcurrentProbeTransportFactory {
        server: ConcurrentProbeServer { state },
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

#[tokio::test(flavor = "multi_thread", worker_threads = 4)]
async fn timing_out_one_request_does_not_abort_an_unrelated_concurrent_request()
-> anyhow::Result<()> {
    let state = ConcurrentProbeState::default();
    let client = initialized_client(state.clone()).await?;

    let (timed, healthy) = tokio::join!(
        client.call_tool(
            "timed_request".to_string(),
            Some(json!({})),
            /*meta*/ None,
            Some(TIMED_CALL_TIMEOUT),
        ),
        client.call_tool(
            "healthy_request".to_string(),
            Some(json!({})),
            /*meta*/ None,
            Some(HEALTHY_CALL_TIMEOUT),
        ),
    );

    let timed_error = timed.expect_err("the short request deadline should expire");
    assert!(
        timed_error
            .to_string()
            .contains("timed out awaiting tools/call")
            || timed_error.to_string().contains("request timeout"),
        "unexpected timeout error: {timed_error:#}"
    );
    let healthy = healthy?;
    assert_eq!(healthy.content.len(), 1);
    assert!(
        state.healthy_request_completed.load(Ordering::SeqCst),
        "the unrelated request should complete"
    );

    let expect_cancellation = std::env::var_os("FIELDWORK_EXPECT_MCP_CANCEL").is_some();
    assert_eq!(
        state.timed_request_cancelled.load(Ordering::SeqCst),
        expect_cancellation,
        "request-scoped cancellation did not match the selected implementation"
    );
    assert!(
        !client.is_closed().await,
        "successful request-scoped cancellation should keep the shared connection alive"
    );

    client.shutdown().await;
    Ok(())
}
