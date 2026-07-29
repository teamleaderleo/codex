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
use rmcp::elicit_safe;
use rmcp::model::CallToolRequestParams;
use rmcp::model::CallToolResult;
use rmcp::model::ClientCapabilities;
use rmcp::model::ContentBlock;
use rmcp::model::ElicitationCapability;
use rmcp::model::FormElicitationCapability;
use rmcp::model::Implementation;
use rmcp::model::InitializeRequestParams;
use rmcp::model::ProtocolVersion;
use rmcp::model::ServerCapabilities;
use rmcp::model::ServerInfo;
use rmcp::schemars::JsonSchema;
use rmcp::service::RequestContext;
use rmcp::service::RoleServer;
use serde::Deserialize;
use serde::Serialize;
use serde_json::json;
use tokio::io::DuplexStream;

const TOOL_TIMEOUT: Duration = Duration::from_millis(100);
const USER_RESPONSE_DELAY: Duration = Duration::from_millis(250);

#[derive(Debug, Deserialize, Serialize, JsonSchema)]
struct ProbeApproval {
    approved: bool,
}

elicit_safe!(ProbeApproval);

#[derive(Clone, Default)]
struct ElicitationProbeState {
    cancellation_observed: Arc<AtomicBool>,
    side_effect_completed: Arc<AtomicBool>,
}

#[derive(Clone)]
struct ElicitationProbeServer {
    state: ElicitationProbeState,
}

impl ServerHandler for ElicitationProbeServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo::new(ServerCapabilities::builder().enable_tools().build())
    }

    async fn call_tool(
        &self,
        request: CallToolRequestParams,
        context: RequestContext<RoleServer>,
    ) -> Result<rmcp::model::CallToolResponse, McpError> {
        if request.name.as_ref() != "eliciting_mutation" {
            return Err(McpError::invalid_params(
                format!("unknown probe tool: {}", request.name),
                None,
            ));
        }

        let elicitation = context
            .peer
            .elicit::<ProbeApproval>("Approve the delayed mutation".to_string());
        tokio::pin!(elicitation);

        tokio::select! {
            () = context.ct.cancelled() => {
                self.state
                    .cancellation_observed
                    .store(true, Ordering::SeqCst);
                Ok(CallToolResult::success(vec![ContentBlock::text("cancelled")]).into())
            }
            response = &mut elicitation => {
                let response = response.map_err(|error| {
                    McpError::internal_error(format!("elicitation failed: {error}"), None)
                })?;
                if response.is_none_or(|approval| approval.approved) {
                    self.state
                        .side_effect_completed
                        .store(true, Ordering::SeqCst);
                }
                Ok(CallToolResult::success(vec![ContentBlock::text("approved")]).into())
            }
        }
    }
}

#[derive(Clone)]
struct ElicitationProbeTransportFactory {
    server: ElicitationProbeServer,
}

impl InProcessTransportFactory for ElicitationProbeTransportFactory {
    fn open(&self) -> BoxFuture<'static, io::Result<DuplexStream>> {
        let server = self.server.clone();
        async move {
            let (client_stream, server_stream) = tokio::io::duplex(4096);
            tokio::spawn(async move {
                server
                    .serve(server_stream)
                    .await
                    .expect("serve elicitation probe MCP server")
                    .waiting()
                    .await
                    .expect("elicitation probe MCP server completes");
            });
            Ok(client_stream)
        }
        .boxed()
    }
}

fn init_params() -> InitializeRequestParams {
    let mut capabilities = ClientCapabilities::default();
    capabilities.elicitation =
        Some(ElicitationCapability::new().with_form(FormElicitationCapability::new()));
    InitializeRequestParams::new(
        capabilities,
        Implementation::new("codex-elicitation-timeout-probe", "0.0.0-test"),
    )
    .with_protocol_version(ProtocolVersion::V_2025_06_18)
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn tool_timeout_elicitation_pause_probe() -> anyhow::Result<()> {
    let state = ElicitationProbeState::default();
    let client = RmcpClient::new_in_process_client(Arc::new(ElicitationProbeTransportFactory {
        server: ElicitationProbeServer {
            state: state.clone(),
        },
    }))
    .await?;

    client
        .initialize(
            init_params(),
            Some(Duration::from_secs(2)),
            Box::new(|_, _| {
                async {
                    tokio::time::sleep(USER_RESPONSE_DELAY).await;
                    Ok(ElicitationResponse {
                        action: ElicitationAction::Accept,
                        content: Some(json!({ "approved": true })),
                        meta: None,
                    })
                }
                .boxed()
            }),
        )
        .await?;

    let result = client
        .call_tool(
            "eliciting_mutation".to_string(),
            Some(json!({})),
            /*meta*/ None,
            Some(TOOL_TIMEOUT),
        )
        .await;

    let expect_elicitation_timeout =
        std::env::var_os("FIELDWORK_EXPECT_ELICITATION_TIMEOUT").is_some();
    if expect_elicitation_timeout {
        let error = result.expect_err("the SDK-native deadline should include elicitation time");
        assert!(
            error.to_string().contains("request timeout")
                || error.to_string().contains("timed out awaiting tools/call"),
            "unexpected timeout error: {error:#}"
        );
        tokio::time::sleep(USER_RESPONSE_DELAY + Duration::from_millis(40)).await;
    } else {
        let result = result?;
        assert_eq!(result.content.len(), 1);
    }

    assert_eq!(
        state.cancellation_observed.load(Ordering::SeqCst),
        expect_elicitation_timeout,
        "cancellation observation did not match the selected timeout design"
    );
    assert_eq!(
        state.side_effect_completed.load(Ordering::SeqCst),
        !expect_elicitation_timeout,
        "approved side-effect completion did not match the selected timeout design"
    );

    client.shutdown().await;
    Ok(())
}
