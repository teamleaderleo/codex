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

const CLIENT_TIMEOUT: Duration = Duration::from_millis(40);
const WORK_AFTER_CANCELLATION: Duration = Duration::from_millis(100);
const NATURAL_WORK: Duration = Duration::from_millis(160);

#[derive(Clone, Default)]
struct IgnoredCancellationState {
    cancellation_observed: Arc<AtomicBool>,
    side_effect_completed: Arc<AtomicBool>,
}

#[derive(Clone)]
struct IgnoredCancellationServer {
    state: IgnoredCancellationState,
}

impl ServerHandler for IgnoredCancellationServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo::new(ServerCapabilities::builder().enable_tools().build())
    }

    async fn call_tool(
        &self,
        request: CallToolRequestParams,
        context: RequestContext<RoleServer>,
    ) -> Result<rmcp::model::CallToolResponse, McpError> {
        if request.name.as_ref() != "ignores_cancel" {
            return Err(McpError::invalid_params(
                format!("unknown probe tool: {}", request.name),
                None,
            ));
        }

        tokio::select! {
            () = context.ct.cancelled() => {
                self.state
                    .cancellation_observed
                    .store(true, Ordering::SeqCst);
                // Deliberately ignore cooperative cancellation and commit later.
                tokio::time::sleep(WORK_AFTER_CANCELLATION).await;
            }
            () = tokio::time::sleep(NATURAL_WORK) => {}
        }

        self.state
            .side_effect_completed
            .store(true, Ordering::SeqCst);
        Ok(CallToolResult::success(vec![ContentBlock::text("effect committed")]).into())
    }
}

#[derive(Clone)]
struct IgnoredCancellationTransportFactory {
    server: IgnoredCancellationServer,
}

impl InProcessTransportFactory for IgnoredCancellationTransportFactory {
    fn open(&self) -> BoxFuture<'static, io::Result<DuplexStream>> {
        let server = self.server.clone();
        async move {
            let (client_stream, server_stream) = tokio::io::duplex(4096);
            tokio::spawn(async move {
                server
                    .serve(server_stream)
                    .await
                    .expect("serve ignored-cancellation probe MCP server")
                    .waiting()
                    .await
                    .expect("ignored-cancellation probe MCP server completes");
            });
            Ok(client_stream)
        }
        .boxed()
    }
}

fn init_params() -> InitializeRequestParams {
    InitializeRequestParams::new(
        ClientCapabilities::default(),
        Implementation::new("codex-ignored-cancel-probe", "0.0.0-test"),
    )
    .with_protocol_version(ProtocolVersion::V_2025_06_18)
}

async fn initialized_client(state: IgnoredCancellationState) -> anyhow::Result<RmcpClient> {
    let client = RmcpClient::new_in_process_client(Arc::new(
        IgnoredCancellationTransportFactory {
            server: IgnoredCancellationServer { state },
        },
    ))
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
async fn delivered_cancellation_does_not_prove_the_remote_effect_was_prevented()
-> anyhow::Result<()> {
    let state = IgnoredCancellationState::default();
    let client = initialized_client(state.clone()).await?;

    let error = client
        .call_tool(
            "ignores_cancel".to_string(),
            Some(json!({})),
            /*meta*/ None,
            Some(CLIENT_TIMEOUT),
        )
        .await
        .expect_err("the caller deadline should expire first");
    assert!(
        error.to_string().contains("timed out awaiting tools/call")
            || error.to_string().contains("request timeout"),
        "unexpected timeout error: {error:#}"
    );

    tokio::time::sleep(NATURAL_WORK + Duration::from_millis(80)).await;

    let expect_cancellation = std::env::var_os("FIELDWORK_EXPECT_MCP_CANCEL").is_some();
    assert_eq!(
        state.cancellation_observed.load(Ordering::SeqCst),
        expect_cancellation,
        "cancellation observation did not match the selected implementation"
    );
    assert!(
        state.side_effect_completed.load(Ordering::SeqCst),
        "the deliberately non-cooperative server should still commit its effect"
    );

    client.shutdown().await;
    Ok(())
}
