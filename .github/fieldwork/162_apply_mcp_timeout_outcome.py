from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_exact(path: Path, old: str, new: str, label: str, expected: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"{label}: expected {expected} exact matches, found {count}")
    path.write_text(text.replace(old, new), encoding="utf-8")


rmcp_client = ROOT / "codex-rs/rmcp-client/src/rmcp_client.rs"
rmcp_lib = ROOT / "codex-rs/rmcp-client/src/lib.rs"
context = ROOT / "codex-rs/core/src/tools/context.rs"
context_tests = ROOT / "codex-rs/core/src/tools/context_tests.rs"
mcp_handler = ROOT / "codex-rs/core/src/tools/handlers/mcp.rs"
mcp_tool_call = ROOT / "codex-rs/core/src/mcp_tool_call.rs"

replace_exact(
    rmcp_client,
    "use anyhow::Result;\nuse anyhow::anyhow;\n",
    "use anyhow::Context;\nuse anyhow::Result;\nuse anyhow::anyhow;\n",
    "anyhow Context import",
)

replace_exact(
    rmcp_client,
    '''#[derive(Debug, thiserror::Error)]
enum ClientOperationError {
    #[error(transparent)]
    Service(#[from] rmcp::service::ServiceError),
    #[error("timed out awaiting {label} after {duration:.0?}")]
    Timeout { label: String, duration: Duration },
}
''',
    '''#[derive(Debug, thiserror::Error)]
enum ClientOperationError {
    #[error(transparent)]
    Service(#[from] rmcp::service::ServiceError),
    #[error("timed out awaiting {label} after {duration:.0?}")]
    Timeout { label: String, duration: Duration },
}

/// Internal classification for failures returned by MCP `tools/call`.
///
/// This deliberately says only what the local client knows. A caller deadline
/// does not prove that the server stopped or that a remote mutation did not
/// commit.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum McpToolCallFailureKind {
    CallerDeadlineReachedOutcomeUnknown,
    Other,
}

pub fn classify_mcp_tool_call_failure(error: &anyhow::Error) -> McpToolCallFailureKind {
    let caller_deadline_reached = error.chain().any(|source| {
        source
            .downcast_ref::<ClientOperationError>()
            .is_some_and(|operation_error| {
                matches!(
                    operation_error,
                    ClientOperationError::Timeout { label, .. } if label == "tools/call"
                )
            })
    });

    if caller_deadline_reached {
        McpToolCallFailureKind::CallerDeadlineReachedOutcomeUnknown
    } else {
        McpToolCallFailureKind::Other
    }
}
''',
    "typed MCP tool-call failure classification",
)

rmcp_text = rmcp_client.read_text(encoding="utf-8")
rmcp_test_anchor = "\n}\n"
insert_at = rmcp_text.rfind(rmcp_test_anchor)
if insert_at < 0:
    raise SystemExit("rmcp-client test module closing brace not found")
rmcp_tests = r'''

    #[test]
    fn mcp_tool_call_failure_classification_survives_anyhow_context() {
        let error = anyhow::Error::new(ClientOperationError::Timeout {
            label: "tools/call".to_string(),
            duration: Duration::from_secs(40),
        })
        .context("tool call failed for `server/tool`");

        assert_eq!(
            classify_mcp_tool_call_failure(&error),
            McpToolCallFailureKind::CallerDeadlineReachedOutcomeUnknown
        );
    }

    #[test]
    fn mcp_tool_call_failure_classification_ignores_other_timeouts_and_errors() {
        let list_timeout = anyhow::Error::new(ClientOperationError::Timeout {
            label: "tools/list".to_string(),
            duration: Duration::from_secs(10),
        });
        let generic = anyhow!("transport failed before classification");

        assert_eq!(
            classify_mcp_tool_call_failure(&list_timeout),
            McpToolCallFailureKind::Other
        );
        assert_eq!(
            classify_mcp_tool_call_failure(&generic),
            McpToolCallFailureKind::Other
        );
    }
'''
if "mcp_tool_call_failure_classification_survives_anyhow_context" in rmcp_text:
    raise SystemExit("rmcp-client classification tests already exist")
rmcp_client.write_text(
    rmcp_text[:insert_at] + rmcp_tests + rmcp_text[insert_at:],
    encoding="utf-8",
)

replace_exact(
    rmcp_lib,
    "pub use rmcp_client::ListToolsWithConnectorIdResult;\npub use rmcp_client::RmcpClient;\n",
    "pub use rmcp_client::ListToolsWithConnectorIdResult;\npub use rmcp_client::McpToolCallFailureKind;\npub use rmcp_client::RmcpClient;\npub use rmcp_client::classify_mcp_tool_call_failure;\n",
    "rmcp-client public failure classification exports",
)

replace_exact(
    context,
    '''#[derive(Clone, Debug)]
pub struct McpToolOutput {
    pub result: CallToolResult,
    pub tool_input: JsonValue,
    pub wall_time: Duration,
''',
    '''/// What Codex knows about execution after an MCP tool handler returns.
///
/// The state is internal evidence. It is intentionally not serialized into the
/// model-visible tool result or the public MCP tool-call item in this slice.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum McpToolExecutionState {
    NotDispatched,
    RemoteResultReceived,
    LocalFailureUnclassified,
    LocalTimeoutOutcomeUnknown,
}

#[derive(Clone, Debug)]
pub struct McpToolOutput {
    pub result: CallToolResult,
    pub tool_input: JsonValue,
    pub execution_state: McpToolExecutionState,
    pub wall_time: Duration,
''',
    "MCP tool output execution state",
)

replace_exact(
    context_tests,
    "        tool_input: json!({}),\n        wall_time:",
    "        tool_input: json!({}),\n        execution_state: McpToolExecutionState::RemoteResultReceived,\n        wall_time:",
    "existing MCP output test literals",
    expected=4,
)

context_test_addition = r'''

#[test]
fn mcp_execution_state_does_not_change_model_visible_output() {
    let build_output = |execution_state| McpToolOutput {
        result: CallToolResult {
            content: vec![serde_json::json!({
                "type": "text",
                "text": "timed out awaiting tools/call",
            })],
            structured_content: None,
            is_error: Some(true),
            meta: None,
        },
        tool_input: json!({}),
        execution_state,
        wall_time: std::time::Duration::from_millis(40),
        original_image_detail_supported: false,
        truncation_policy: TruncationPolicy::Bytes(1024),
    };
    let payload = ToolPayload::Function {
        arguments: "{}".to_string(),
    };
    let settled = build_output(McpToolExecutionState::LocalFailureUnclassified);
    let outcome_unknown = build_output(McpToolExecutionState::LocalTimeoutOutcomeUnknown);

    assert_eq!(
        settled.to_response_item("mcp-timeout", &payload),
        outcome_unknown.to_response_item("mcp-timeout", &payload)
    );
    assert_eq!(
        settled.code_mode_result(&payload),
        outcome_unknown.code_mode_result(&payload)
    );
    assert_eq!(
        outcome_unknown.execution_state,
        McpToolExecutionState::LocalTimeoutOutcomeUnknown
    );
}
'''
context_text = context_tests.read_text(encoding="utf-8")
if "mcp_execution_state_does_not_change_model_visible_output" in context_text:
    raise SystemExit("MCP output behavior-neutral test already exists")
context_tests.write_text(context_text + context_test_addition, encoding="utf-8")

replace_exact(
    mcp_handler,
    "use crate::tools::context::McpToolOutput;\n",
    "use crate::tools::context::McpToolExecutionState;\nuse crate::tools::context::McpToolOutput;\n",
    "MCP handler execution-state import",
)
replace_exact(
    mcp_handler,
    '''        Ok(boxed_tool_output(McpToolOutput {
            result: result.result,
            tool_input: result.tool_input,
            wall_time: started.elapsed(),
''',
    '''        Ok(boxed_tool_output(McpToolOutput {
            result: result.result,
            tool_input: result.tool_input,
            execution_state: result.execution_state,
            wall_time: started.elapsed(),
''',
    "MCP handler execution-state propagation",
)

replace_exact(
    mcp_tool_call,
    "use crate::tools::hook_names::HookToolName;\n",
    "use crate::tools::context::McpToolExecutionState;\nuse crate::tools::hook_names::HookToolName;\n",
    "core MCP execution-state import",
)
replace_exact(
    mcp_tool_call,
    "use codex_rmcp_client::ElicitationAction;\nuse codex_rmcp_client::ElicitationResponse;\n",
    "use codex_rmcp_client::ElicitationAction;\nuse codex_rmcp_client::ElicitationResponse;\nuse codex_rmcp_client::McpToolCallFailureKind;\nuse codex_rmcp_client::classify_mcp_tool_call_failure;\n",
    "rmcp failure-classification imports",
)

replace_exact(
    mcp_tool_call,
    '''                return HandledMcpToolCall {
                    result: CallToolResult::from_error_text(format!("err: {e}")),
                    tool_input: JsonValue::Object(serde_json::Map::new()),
                };
''',
    '''                return HandledMcpToolCall {
                    result: CallToolResult::from_error_text(format!("err: {e}")),
                    tool_input: JsonValue::Object(serde_json::Map::new()),
                    execution_state: McpToolExecutionState::NotDispatched,
                };
''',
    "invalid-argument pre-dispatch state",
)

replace_exact(
    mcp_tool_call,
    '''        return HandledMcpToolCall {
            result: CallToolResult::from_result(result),
            tool_input: arguments_value
                .unwrap_or_else(|| JsonValue::Object(serde_json::Map::new())),
        };
''',
    '''        return HandledMcpToolCall {
            result: CallToolResult::from_result(result),
            tool_input: arguments_value
                .unwrap_or_else(|| JsonValue::Object(serde_json::Map::new())),
            execution_state: McpToolExecutionState::NotDispatched,
        };
''',
    "pre-dispatch MCP result states",
    expected=3,
)

replace_exact(
    mcp_tool_call,
    '''pub(crate) struct HandledMcpToolCall {
    pub(crate) result: CallToolResult,
    pub(crate) tool_input: JsonValue,
}
''',
    '''pub(crate) struct HandledMcpToolCall {
    pub(crate) result: CallToolResult,
    pub(crate) tool_input: JsonValue,
    pub(crate) execution_state: McpToolExecutionState,
}
''',
    "handled MCP call execution state",
)

replace_exact(
    mcp_tool_call,
    '''    let result = async {
        let result = async {
            let result = prepared_call
''',
    '''    let mut execution_state = McpToolExecutionState::LocalFailureUnclassified;
    let result = async {
        let result = async {
            let call_result = prepared_call
''',
    "approved MCP call typed result capture",
)

replace_exact(
    mcp_tool_call,
    '''                })
                .await
                .map_err(|error| format!("tool call error: {error:?}"))?;
            let result = sanitize_mcp_tool_result_for_model(
''',
    '''                })
                .await;
            execution_state = mcp_tool_execution_state(&call_result);
            let result = call_result.map_err(|error| format!("tool call error: {error:?}"))?;
            let result = sanitize_mcp_tool_result_for_model(
''',
    "approved MCP call state classification",
)

replace_exact(
    mcp_tool_call,
    '''    HandledMcpToolCall {
        result: CallToolResult::from_result(result),
        tool_input,
    }
}
''',
    '''    HandledMcpToolCall {
        result: CallToolResult::from_result(result),
        tool_input,
        execution_state,
    }
}

fn mcp_tool_execution_state(
    result: &std::result::Result<CallToolResult, anyhow::Error>,
) -> McpToolExecutionState {
    match result {
        Ok(_) => McpToolExecutionState::RemoteResultReceived,
        Err(error) => match classify_mcp_tool_call_failure(error) {
            McpToolCallFailureKind::CallerDeadlineReachedOutcomeUnknown => {
                McpToolExecutionState::LocalTimeoutOutcomeUnknown
            }
            McpToolCallFailureKind::Other => McpToolExecutionState::LocalFailureUnclassified,
        },
    }
}
''',
    "approved MCP call final state and mapping helper",
)

mcp_tool_tests = r'''

#[cfg(test)]
mod mcp_tool_execution_state_tests {
    use super::*;

    #[test]
    fn mcp_tool_execution_state_marks_remote_result_received() {
        let result = Ok(CallToolResult::from_error_text("remote result"));

        assert_eq!(
            mcp_tool_execution_state(&result),
            McpToolExecutionState::RemoteResultReceived
        );
    }

    #[test]
    fn mcp_tool_execution_state_keeps_other_local_failure_unclassified() {
        let result = Err(anyhow::anyhow!("local failure"));

        assert_eq!(
            mcp_tool_execution_state(&result),
            McpToolExecutionState::LocalFailureUnclassified
        );
    }
}
'''
mcp_text = mcp_tool_call.read_text(encoding="utf-8")
if "mod mcp_tool_execution_state_tests" in mcp_text:
    raise SystemExit("MCP core execution-state tests already exist")
mcp_tool_call.write_text(mcp_text + mcp_tool_tests, encoding="utf-8")
