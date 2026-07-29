from pathlib import Path


def replace_exact(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"anchor mismatch in {path}: expected one match, found {text.count(old)}")
    path.write_text(text.replace(old, new), encoding="utf-8")


source = Path("codex-rs/rmcp-client/src/rmcp_client.rs")
replace_exact(
    source,
    '''#[derive(Debug, thiserror::Error)]
enum ClientOperationError {
    #[error(transparent)]
    Service(#[from] rmcp::service::ServiceError),
    #[error("timed out awaiting {label} after {duration:.0?}")]
    Timeout { label: String, duration: Duration },
}
''',
    '''#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum McpCancellationRequestStatus {
    NotificationSent,
    NotificationSendFailed,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum McpRemoteExecutionStatus {
    MayStillRun,
}

#[derive(Debug, thiserror::Error)]
#[error("timed out awaiting tools/call after {duration:.0?}")]
pub struct McpToolCallTimeout {
    pub duration: Duration,
    pub cancellation_request: McpCancellationRequestStatus,
    pub remote_execution: McpRemoteExecutionStatus,
}

fn cancellation_request_status(
    result: &std::result::Result<(), rmcp::service::ServiceError>,
) -> McpCancellationRequestStatus {
    match result {
        Ok(()) => McpCancellationRequestStatus::NotificationSent,
        Err(_) => McpCancellationRequestStatus::NotificationSendFailed,
    }
}

#[derive(Debug, thiserror::Error)]
enum ClientOperationError {
    #[error(transparent)]
    Service(#[from] rmcp::service::ServiceError),
    #[error(transparent)]
    ToolCallTimeout(#[from] McpToolCallTimeout),
    #[error("timed out awaiting {label} after {duration:.0?}")]
    Timeout { label: String, duration: Duration },
}

impl ClientOperationError {
    fn into_anyhow(self) -> anyhow::Error {
        match self {
            Self::ToolCallTimeout(error) => anyhow::Error::new(error),
            other => anyhow::Error::new(other),
        }
    }
}
''',
)

replace_exact(
    source,
    '''        let mut rmcp_params = CallToolRequestParams::new(name);
        rmcp_params.arguments = arguments;
        let result = self
            .run_service_operation("tools/call", timeout, move |service| {
                let rmcp_params = rmcp_params.clone();
                let meta = meta.clone();
                async move {
                    let mut options = rmcp::service::PeerRequestOptions::no_options();
                    options.meta = meta;
                    let result = service
                        .peer()
                        .send_request_with_option(
                            ClientRequest::CallToolRequest(rmcp::model::CallToolRequest::new(
                                rmcp_params,
                            )),
                            options,
                        )
                        .await?
                        .await_response()
                        .await?;
                    match result {
                        ServerResult::CallToolResult(result) => Ok(result),
                        _ => Err(rmcp::service::ServiceError::UnexpectedResponse),
                    }
                }
                .boxed()
            })
            .await?;
        self.persist_oauth_tokens().await;
        Ok(result)
    }
''',
    '''        let mut rmcp_params = CallToolRequestParams::new(name);
        rmcp_params.arguments = arguments;
        let result = self
            .run_tool_call_operation(rmcp_params, meta, timeout)
            .await?;
        self.persist_oauth_tokens().await;
        Ok(result)
    }

    async fn run_tool_call_operation(
        &self,
        rmcp_params: CallToolRequestParams,
        meta: Option<rmcp::model::Meta>,
        timeout: Option<Duration>,
    ) -> Result<CallToolResult> {
        let service = self.service().await?;
        let result = match Self::run_tool_call_operation_once(
            Arc::clone(&service),
            rmcp_params.clone(),
            meta.clone(),
            timeout,
            self.elicitation_pause_state.clone(),
        )
        .await
        {
            Ok(result) => Ok(result),
            Err(error) if Self::is_session_expired_404(&error) => {
                self.reinitialize_after_session_expiry(&service).await?;
                let recovered_service = self.service().await?;
                Self::run_tool_call_operation_once(
                    recovered_service,
                    rmcp_params,
                    meta,
                    timeout,
                    self.elicitation_pause_state.clone(),
                )
                .await
            }
            Err(error) => Err(error),
        };
        result.map_err(ClientOperationError::into_anyhow)
    }

    async fn run_tool_call_operation_once(
        service: Arc<RunningService<RoleClient, ElicitationClientService>>,
        rmcp_params: CallToolRequestParams,
        meta: Option<rmcp::model::Meta>,
        timeout: Option<Duration>,
        pause_state: ElicitationPauseState,
    ) -> std::result::Result<CallToolResult, ClientOperationError> {
        let mut options = rmcp::service::PeerRequestOptions::no_options();
        options.meta = meta;
        let mut handle = service
            .peer()
            .send_request_with_option(
                ClientRequest::CallToolRequest(rmcp::model::CallToolRequest::new(rmcp_params)),
                options,
            )
            .await?;

        let result = match timeout {
            Some(duration) => {
                match active_time_timeout(duration, pause_state.subscribe(), &mut handle.rx).await {
                    Ok(response) => response
                        .map_err(|_| rmcp::service::ServiceError::TransportClosed)?
                        .map_err(ClientOperationError::from)?,
                    Err(()) => {
                        let cancellation_result = handle
                            .cancel(Some("request timeout".to_string()))
                            .await;
                        if let Err(error) = &cancellation_result {
                            warn!(error = %error, "failed to send MCP request cancellation after timeout");
                        }
                        return Err(McpToolCallTimeout {
                            duration,
                            cancellation_request: cancellation_request_status(&cancellation_result),
                            remote_execution: McpRemoteExecutionStatus::MayStillRun,
                        }
                        .into());
                    }
                }
            }
            None => handle.await_response().await?,
        };

        match result {
            ServerResult::CallToolResult(result) => Ok(result),
            _ => Err(rmcp::service::ServiceError::UnexpectedResponse.into()),
        }
    }
''',
)

replace_exact(
    source,
    '''mod tests {
    use std::time::Duration;

    use pretty_assertions::assert_eq;
    use tokio::time;

    use super::*;
''',
    '''mod tests {
    use std::sync::atomic::AtomicBool;
    use std::sync::atomic::Ordering;
    use std::time::Duration;

    use pretty_assertions::assert_eq;
    use rmcp::ServerHandler;
    use rmcp::ServiceExt;
    use rmcp::model::CallToolResponse;
    use rmcp::model::ContentBlock;
    use rmcp::model::ServerCapabilities;
    use rmcp::model::ServerInfo;
    use rmcp::service::RequestContext;
    use rmcp::service::RoleServer;
    use tokio::time;

    use super::*;
''',
)

replace_exact(
    source,
    '''        assert_eq!(Ok("done"), result);
    }
}
''',
    '''        assert_eq!(Ok("done"), result);
    }

    #[derive(Clone, Default)]
    struct ToolCallTimeoutState {
        handler_started: Arc<AtomicBool>,
        cancellation_observed: Arc<AtomicBool>,
        side_effect_completed: Arc<AtomicBool>,
    }

    #[derive(Clone)]
    struct SlowToolServer {
        state: ToolCallTimeoutState,
    }

    impl ServerHandler for SlowToolServer {
        fn get_info(&self) -> ServerInfo {
            ServerInfo::new(ServerCapabilities::builder().enable_tools().build())
        }

        async fn call_tool(
            &self,
            _request: CallToolRequestParams,
            context: RequestContext<RoleServer>,
        ) -> std::result::Result<CallToolResponse, rmcp::ErrorData> {
            self.state.handler_started.store(true, Ordering::SeqCst);
            tokio::select! {
                _ = context.ct.cancelled() => {
                    self.state.cancellation_observed.store(true, Ordering::SeqCst);
                    Ok(CallToolResult::success(vec![ContentBlock::text("cancelled")]).into())
                }
                _ = time::sleep(Duration::from_millis(250)) => {
                    self.state.side_effect_completed.store(true, Ordering::SeqCst);
                    Ok(CallToolResult::success(vec![ContentBlock::text("completed")]).into())
                }
            }
        }
    }

    #[derive(Clone)]
    struct SlowToolFactory {
        state: ToolCallTimeoutState,
    }

    impl InProcessTransportFactory for SlowToolFactory {
        fn open(&self) -> BoxFuture<'static, io::Result<tokio::io::DuplexStream>> {
            let state = self.state.clone();
            async move {
                let (server_transport, client_transport) = tokio::io::duplex(4096);
                tokio::spawn(async move {
                    let server = SlowToolServer { state };
                    let service = server
                        .serve(server_transport)
                        .await
                        .expect("start in-process MCP server");
                    let _ = service.waiting().await;
                });
                Ok(client_transport)
            }
            .boxed()
        }
    }

    async fn initialized_timeout_test_client(
        state: ToolCallTimeoutState,
    ) -> Result<RmcpClient> {
        let client = RmcpClient::new_in_process_client(Arc::new(SlowToolFactory { state })).await?;
        let params = InitializeRequestParams::new(
            rmcp::model::ClientCapabilities::default(),
            rmcp::model::Implementation::new("timeout-test-client", "0"),
        )
        .with_protocol_version(rmcp::model::ProtocolVersion::V_2025_06_18);
        let send_elicitation: SendElicitation = Box::new(|_, _| {
            async { Err(anyhow!("unexpected elicitation in timeout test")) }.boxed()
        });
        client.initialize(params, None, send_elicitation).await?;
        Ok(client)
    }

    async fn wait_for_handler_start(state: &ToolCallTimeoutState) -> Result<()> {
        time::timeout(Duration::from_secs(2), async {
            while !state.handler_started.load(Ordering::SeqCst) {
                time::sleep(Duration::from_millis(5)).await;
            }
        })
        .await
        .map_err(|_| anyhow!("server handler did not start"))?;
        Ok(())
    }

    #[test]
    fn cancellation_delivery_classification_is_typed() {
        assert_eq!(
            cancellation_request_status(&Ok(())),
            McpCancellationRequestStatus::NotificationSent
        );
        assert_eq!(
            cancellation_request_status(&Err(rmcp::service::ServiceError::TransportClosed)),
            McpCancellationRequestStatus::NotificationSendFailed
        );
    }

    #[tokio::test]
    async fn mcp_tool_call_timeout_sends_cancellation_and_remains_ambiguous() -> Result<()> {
        let state = ToolCallTimeoutState::default();
        let client = initialized_timeout_test_client(state.clone()).await?;

        let error = client
            .call_tool(
                "slow_side_effect".to_string(),
                None,
                None,
                Some(Duration::from_millis(50)),
            )
            .await
            .expect_err("tool call should time out");
        wait_for_handler_start(&state).await?;

        let timeout = error
            .downcast_ref::<McpToolCallTimeout>()
            .expect("typed MCP tool timeout");
        assert_eq!(timeout.duration, Duration::from_millis(50));
        assert_eq!(
            timeout.cancellation_request,
            McpCancellationRequestStatus::NotificationSent
        );
        assert_eq!(
            timeout.remote_execution,
            McpRemoteExecutionStatus::MayStillRun
        );

        time::sleep(Duration::from_millis(100)).await;
        assert!(state.cancellation_observed.load(Ordering::SeqCst));
        assert!(!state.side_effect_completed.load(Ordering::SeqCst));

        client
            .call_tool("slow_side_effect".to_string(), None, None, None)
            .await?;
        assert!(state.side_effect_completed.load(Ordering::SeqCst));
        client.shutdown().await;
        Ok(())
    }
}
''',
)

lib = Path("codex-rs/rmcp-client/src/lib.rs")
replace_exact(
    lib,
    '''pub use rmcp_client::ListToolsWithConnectorIdResult;
pub use rmcp_client::RmcpClient;
pub use rmcp_client::SendElicitation;
''',
    '''pub use rmcp_client::ListToolsWithConnectorIdResult;
pub use rmcp_client::McpCancellationRequestStatus;
pub use rmcp_client::McpRemoteExecutionStatus;
pub use rmcp_client::McpToolCallTimeout;
pub use rmcp_client::RmcpClient;
pub use rmcp_client::SendElicitation;
''',
)
