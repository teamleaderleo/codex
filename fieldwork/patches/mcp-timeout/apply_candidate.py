#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

TARGET = Path("codex-rs/rmcp-client/src/rmcp_client.rs")
START = "        let requested_modern = self.protocol_mode == McpProtocolMode::V20260728;\n"
PERSIST = "        self.persist_oauth_tokens().await;\n"
NEXT_METHOD = "    pub async fn send_custom_notification(\n"


def native_sdk_timeout(text: str) -> str:
    start = text.index(START)
    persist = text.index(PERSIST, start)
    old = text[start:persist]
    if 'run_service_operation("tools/call", timeout' not in old:
        raise SystemExit("native candidate anchor no longer matches legacy call path")
    new = old.replace(
        START,
        START + "        let operation_timeout = requested_modern.then_some(timeout).flatten();\n",
        1,
    ).replace(
        '.run_service_operation("tools/call", timeout, move |service| {',
        '.run_service_operation("tools/call", operation_timeout, move |service| {',
        1,
    ).replace(
        "                    options.meta = meta;\n",
        "                    options.meta = meta;\n                    options.timeout = timeout;\n",
        1,
    )
    return text[:start] + new + text[persist:]


def pause_aware_explicit_cancel(text: str) -> str:
    start = text.index(START)
    next_method = text.index(NEXT_METHOD, start)
    old = text[start:next_method]
    if 'run_service_operation("tools/call", timeout' not in old:
        raise SystemExit("pause-aware candidate anchor no longer matches legacy call path")

    new = '''        let requested_modern = self.protocol_mode == McpProtocolMode::V20260728;
        let result = self
            .run_tool_call_operation(rmcp_params, meta, timeout, requested_modern)
            .await?;
        self.persist_oauth_tokens().await;
        Ok(result)
    }

    async fn run_tool_call_operation(
        &self,
        rmcp_params: CallToolRequestParams,
        meta: Option<RequestMetaObject>,
        timeout: Option<Duration>,
        requested_modern: bool,
    ) -> Result<CallToolResult> {
        let service = self.service().await?;
        match Self::run_tool_call_once(
            Arc::clone(&service),
            rmcp_params.clone(),
            meta.clone(),
            timeout,
            requested_modern,
            self.elicitation_pause_state.clone(),
        )
        .await
        {
            Ok(result) => Ok(result),
            Err(error) if Self::is_session_expired_404(&error) => {
                self.reinitialize_after_session_expiry(&service).await?;
                let recovered_service = self.service().await?;
                Self::run_tool_call_once(
                    recovered_service,
                    rmcp_params,
                    meta,
                    timeout,
                    requested_modern,
                    self.elicitation_pause_state.clone(),
                )
                .await
                .map_err(Into::into)
            }
            Err(error) => Err(error.into()),
        }
    }

    async fn run_tool_call_once(
        service: Arc<RunningService<RoleClient, ElicitationClientService>>,
        mut rmcp_params: CallToolRequestParams,
        meta: Option<RequestMetaObject>,
        timeout: Option<Duration>,
        requested_modern: bool,
        pause_state: ElicitationPauseState,
    ) -> std::result::Result<CallToolResult, ClientOperationError> {
        let modern_session = requested_modern
            && service.peer().peer_info().is_some_and(|info| {
                info.protocol_version == ProtocolVersion::V_2026_07_28
            });
        if modern_session {
            rmcp_params.meta = meta;
            return match timeout {
                Some(duration) => active_time_timeout(
                    duration,
                    pause_state.subscribe(),
                    service.call_tool(rmcp_params),
                )
                .await
                .map_err(|_| ClientOperationError::Timeout {
                    label: "tools/call".to_string(),
                    duration,
                })?
                .map_err(ClientOperationError::from),
                None => service
                    .call_tool(rmcp_params)
                    .await
                    .map_err(ClientOperationError::from),
            };
        }

        let mut options = rmcp::service::PeerRequestOptions::no_options();
        options.meta = meta;
        let mut handle = service
            .peer()
            .send_request_with_option(
                ClientRequest::CallToolRequest(rmcp::model::CallToolRequest::new(rmcp_params)),
                options,
            )
            .await?;
        let response = match timeout {
            Some(duration) => match active_time_timeout(
                duration,
                pause_state.subscribe(),
                &mut handle.rx,
            )
            .await
            {
                Ok(response) => response
                    .map_err(|_| rmcp::service::ServiceError::TransportClosed)??,
                Err(()) => {
                    if let Err(error) = handle
                        .cancel(Some(format!(
                            "timed out awaiting tools/call after {duration:.0?}"
                        )))
                        .await
                    {
                        warn!(error = %error, "failed to cancel timed out MCP tools/call");
                    }
                    return Err(ClientOperationError::Timeout {
                        label: "tools/call".to_string(),
                        duration,
                    });
                }
            },
            None => handle.await_response().await?,
        };
        match response {
            ServerResult::CallToolResult(result) => Ok(result),
            _ => Err(ClientOperationError::Service(
                rmcp::service::ServiceError::UnexpectedResponse,
            )),
        }
    }

'''
    return text[:start] + new + text[next_method:]


def pause_aware_bounded_cancel(text: str) -> str:
    updated = pause_aware_explicit_cancel(text)
    old = '''                Err(()) => {
                    if let Err(error) = handle
                        .cancel(Some(format!(
                            "timed out awaiting tools/call after {duration:.0?}"
                        )))
                        .await
                    {
                        warn!(error = %error, "failed to cancel timed out MCP tools/call");
                    }
                    return Err(ClientOperationError::Timeout {
                        label: "tools/call".to_string(),
                        duration,
                    });
                }
'''
    new = '''                Err(()) => {
                    let service_cancellation = service.cancellation_token();
                    tokio::spawn(async move {
                        let cancellation = handle.cancel(Some(format!(
                            "timed out awaiting tools/call after {duration:.0?}"
                        )));
                        match tokio::time::timeout(Duration::from_millis(100), cancellation).await {
                            Ok(Ok(())) => {}
                            Ok(Err(error)) => {
                                warn!(
                                    error = %error,
                                    "failed to cancel timed out MCP tools/call; closing transport"
                                );
                                service_cancellation.cancel();
                            }
                            Err(_) => {
                                warn!(
                                    "timed out delivering MCP tools/call cancellation; closing transport"
                                );
                                service_cancellation.cancel();
                            }
                        }
                    });
                    return Err(ClientOperationError::Timeout {
                        label: "tools/call".to_string(),
                        duration,
                    });
                }
'''
    if old not in updated:
        raise SystemExit("bounded cancellation anchor no longer matches explicit candidate")
    return updated.replace(old, new, 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "candidate",
        choices=[
            "native-sdk-timeout",
            "pause-aware-explicit-cancel",
            "pause-aware-bounded-cancel",
        ],
    )
    args = parser.parse_args()

    text = TARGET.read_text(encoding="utf-8")
    if args.candidate == "native-sdk-timeout":
        updated = native_sdk_timeout(text)
    elif args.candidate == "pause-aware-explicit-cancel":
        updated = pause_aware_explicit_cancel(text)
    else:
        updated = pause_aware_bounded_cancel(text)
    TARGET.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
