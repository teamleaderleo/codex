use std::io;
use std::sync::Arc;
use std::time::Duration;

use codex_rmcp_client::ElicitationAction;
use codex_rmcp_client::ElicitationResponse;
use codex_rmcp_client::InProcessTransportFactory;
use codex_rmcp_client::RmcpClient;
use futures::FutureExt as _;
use futures::future::BoxFuture;
use rmcp::model::ClientCapabilities;
use rmcp::model::Implementation;
use rmcp::model::InitializeRequestParams;
use rmcp::model::ProtocolVersion;
use serde_json::Value;
use serde_json::json;
use tokio::io::AsyncBufReadExt as _;
use tokio::io::AsyncWriteExt as _;
use tokio::io::BufReader;
use tokio::io::DuplexStream;
use tokio::sync::Notify;

const CLIENT_TIMEOUT: Duration = Duration::from_millis(40);
const RETURN_BOUND: Duration = Duration::from_millis(400);
const CONNECTION_CLOSE_BOUND: Duration = Duration::from_secs(1);

#[derive(Clone, Default)]
struct StalledCancelState {
    tool_seen: Arc<Notify>,
}

#[derive(Clone)]
struct StalledCancelTransportFactory {
    state: StalledCancelState,
}

impl InProcessTransportFactory for StalledCancelTransportFactory {
    fn open(&self) -> BoxFuture<'static, io::Result<DuplexStream>> {
        let state = self.state.clone();
        async move {
            // A tiny duplex buffer makes the cancellation write block once the raw
            // server deliberately stops reading after tools/call.
            let (client_stream, server_stream) = tokio::io::duplex(64);
            tokio::spawn(async move {
                raw_server_that_stops_reading(server_stream, state)
                    .await
                    .expect("run stalled-cancellation probe server");
            });
            Ok(client_stream)
        }
        .boxed()
    }
}

async fn write_json_line<W>(writer: &mut W, value: &Value) -> io::Result<()>
where
    W: tokio::io::AsyncWrite + Unpin,
{
    let encoded = serde_json::to_vec(value).map_err(io::Error::other)?;
    writer.write_all(&encoded).await?;
    writer.write_all(b"\n").await?;
    writer.flush().await
}

async fn raw_server_that_stops_reading(
    stream: DuplexStream,
    state: StalledCancelState,
) -> io::Result<()> {
    let (reader, mut writer) = tokio::io::split(stream);
    let mut lines = BufReader::new(reader).lines();

    while let Some(line) = lines.next_line().await? {
        let message: Value = serde_json::from_str(&line).map_err(io::Error::other)?;
        match message.get("method").and_then(Value::as_str) {
            Some("initialize") => {
                write_json_line(
                    &mut writer,
                    &json!({
                        "jsonrpc": "2.0",
                        "id": message["id"],
                        "result": {
                            "protocolVersion": "2025-06-18",
                            "capabilities": {"tools": {}},
                            "serverInfo": {"name": "stalled-cancel-probe", "version": "1.0.0"}
                        }
                    }),
                )
                .await?;
            }
            Some("notifications/initialized") => {}
            Some("tools/call") => {
                state.tool_seen.notify_one();
                // Keep the server half alive while refusing to drain any further
                // client bytes. A cancellation notification larger than the 64-byte
                // buffer cannot finish writing.
                std::future::pending::<()>().await;
            }
            Some(other) => {
                return Err(io::Error::other(format!(
                    "unexpected method in stalled-cancel probe: {other}"
                )));
            }
            None => {
                return Err(io::Error::other(
                    "unexpected response in stalled-cancel probe",
                ));
            }
        }
    }

    Ok(())
}

fn init_params() -> InitializeRequestParams {
    InitializeRequestParams::new(
        ClientCapabilities::default(),
        Implementation::new("codex-stalled-cancel-probe", "0.0.0-test"),
    )
    .with_protocol_version(ProtocolVersion::V_2025_06_18)
}

async fn initialized_client(state: StalledCancelState) -> anyhow::Result<RmcpClient> {
    let client = RmcpClient::new_in_process_client(Arc::new(StalledCancelTransportFactory {
        state,
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
async fn cancellation_delivery_stall_does_not_silently_extend_the_tool_deadline()
-> anyhow::Result<()> {
    let state = StalledCancelState::default();
    let client = initialized_client(state.clone()).await?;

    let call = client.call_tool(
        "slow_mutation".to_string(),
        Some(json!({})),
        /*meta*/ None,
        Some(CLIENT_TIMEOUT),
    );
    tokio::pin!(call);

    tokio::time::timeout(Duration::from_secs(1), state.tool_seen.notified()).await?;
    let observed = tokio::time::timeout(RETURN_BOUND, &mut call).await;

    let expect_call_stall = std::env::var_os("FIELDWORK_EXPECT_CANCEL_SEND_STALL").is_some();
    let expect_bounded_cancel = std::env::var_os("FIELDWORK_EXPECT_BOUNDED_CANCEL").is_some();

    if expect_call_stall {
        assert!(
            observed.is_err(),
            "candidate unexpectedly returned while cancellation delivery was blocked"
        );
    } else {
        let result = observed.expect("tool timeout should remain caller-bounded");
        let error = result.expect_err("the tool call should report a timeout");
        assert!(
            error.to_string().contains("timed out awaiting tools/call")
                || error.to_string().contains("request timeout"),
            "unexpected timeout error: {error:#}"
        );
    }

    if expect_bounded_cancel {
        tokio::time::timeout(CONNECTION_CLOSE_BOUND, async {
            while !client.is_closed().await {
                tokio::time::sleep(Duration::from_millis(10)).await;
            }
        })
        .await?;
    } else if !expect_call_stall {
        assert!(
            !client.is_closed().await,
            "the current outer timeout should not close the shared connection"
        );
    }

    client.shutdown().await;
    Ok(())
}
