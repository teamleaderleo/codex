from pathlib import Path
from textwrap import dedent

path = Path("codex-rs/core/src/mcp_tool_call.rs")
text = path.read_text(encoding="utf-8")
old = dedent(
    '''\
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
    '''
)
new = dedent(
    '''\
    fn mcp_tool_execution_state(
        result: &std::result::Result<CallToolResult, anyhow::Error>,
    ) -> McpToolExecutionState {
        match result {
            Ok(_) => McpToolExecutionState::RemoteResultReceived,
            Err(error) => {
                mcp_tool_failure_execution_state(classify_mcp_tool_call_failure(error))
            }
        }
    }

    fn mcp_tool_failure_execution_state(
        failure_kind: McpToolCallFailureKind,
    ) -> McpToolExecutionState {
        match failure_kind {
            McpToolCallFailureKind::CallerDeadlineReachedOutcomeUnknown => {
                McpToolExecutionState::LocalTimeoutOutcomeUnknown
            }
            McpToolCallFailureKind::Other => McpToolExecutionState::LocalFailureUnclassified,
        }
    }
    '''
)
if text.count(old) != 1:
    raise SystemExit(f"execution-state mapping anchor mismatch: found {text.count(old)}")
text = text.replace(old, new, 1)

anchor = dedent(
    '''\
        #[test]
        fn mcp_tool_execution_state_marks_remote_result_received() {
    '''
)
addition = dedent(
    '''\
        #[test]
        fn typed_mcp_timeout_maps_to_local_outcome_unknown() {
            assert_eq!(
                mcp_tool_failure_execution_state(
                    McpToolCallFailureKind::CallerDeadlineReachedOutcomeUnknown,
                ),
                McpToolExecutionState::LocalTimeoutOutcomeUnknown
            );
        }

        #[test]
        fn mcp_tool_execution_state_marks_remote_result_received() {
    '''
)
if text.count(anchor) != 1:
    raise SystemExit(f"core timeout handoff test anchor mismatch: found {text.count(anchor)}")
path.write_text(text.replace(anchor, addition, 1), encoding="utf-8")
