use codex_extension_api::ToolCallOutcome;
use codex_extension_api::ToolCallSource as ExtensionToolCallSource;
use codex_extension_api::ToolFinishInput;
use codex_extension_api::ToolStartInput;
use codex_tools::ToolName;
use codex_tools::ToolOperationTerminalState;

use crate::session::session::Session;
use crate::session::turn_context::TurnContext;
use crate::tools::context::ToolCallSource;
use crate::tools::context::ToolInvocation;

pub(crate) async fn notify_tool_start(invocation: &ToolInvocation) {
    for contributor in invocation
        .session
        .services
        .extensions
        .tool_lifecycle_contributors()
    {
        contributor
            .on_tool_start(ToolStartInput {
                session_store: &invocation.session.services.session_extension_data,
                thread_store: &invocation.session.services.thread_extension_data,
                turn_store: invocation.turn.extension_data.as_ref(),
                turn_id: invocation.turn.sub_id.as_str(),
                call_id: invocation.call_id.as_str(),
                tool_name: &invocation.tool_name,
                source: extension_tool_call_source(invocation.source.clone()),
            })
            .await;
    }
}

pub(crate) async fn notify_tool_finish(invocation: &ToolInvocation, outcome: ToolCallOutcome) {
    notify_tool_finish_parts(
        invocation.session.as_ref(),
        invocation.turn.as_ref(),
        invocation.call_id.as_str(),
        &invocation.tool_name,
        invocation.source.clone(),
        outcome,
        None,
    )
    .await;
}

pub(crate) async fn notify_tool_aborted(
    session: &Session,
    turn: &TurnContext,
    call_id: &str,
    tool_name: &ToolName,
    source: ToolCallSource,
    execution_started: bool,
) {
    let terminal_state = if execution_started {
        ToolOperationTerminalState::Ambiguous
    } else {
        ToolOperationTerminalState::NotStarted
    };
    notify_tool_finish_parts(
        session,
        turn,
        call_id,
        tool_name,
        source,
        ToolCallOutcome::Aborted,
        Some(terminal_state),
    )
    .await;
}

async fn notify_tool_finish_parts(
    session: &Session,
    turn: &TurnContext,
    call_id: &str,
    tool_name: &ToolName,
    source: ToolCallSource,
    outcome: ToolCallOutcome,
    terminal_state_override: Option<ToolOperationTerminalState>,
) {
    session
        .record_tool_operation_terminal(
            call_id,
            terminal_state_override.unwrap_or_else(|| receipt_terminal_state(outcome)),
        )
        .await;

    for contributor in session.services.extensions.tool_lifecycle_contributors() {
        contributor
            .on_tool_finish(ToolFinishInput {
                session_store: &session.services.session_extension_data,
                thread_store: &session.services.thread_extension_data,
                turn_store: turn.extension_data.as_ref(),
                turn_id: turn.sub_id.as_str(),
                call_id,
                tool_name,
                source: extension_tool_call_source(source.clone()),
                outcome,
            })
            .await;
    }
}

fn receipt_terminal_state(outcome: ToolCallOutcome) -> ToolOperationTerminalState {
    match outcome {
        ToolCallOutcome::Completed { .. } => ToolOperationTerminalState::Completed,
        ToolCallOutcome::Blocked
        | ToolCallOutcome::Failed {
            handler_executed: false,
        } => ToolOperationTerminalState::Failed,
        ToolCallOutcome::Failed {
            handler_executed: true,
        }
        | ToolCallOutcome::Aborted => ToolOperationTerminalState::Ambiguous,
    }
}

fn extension_tool_call_source(source: ToolCallSource) -> ExtensionToolCallSource {
    match source {
        ToolCallSource::Direct => ExtensionToolCallSource::Direct,
        ToolCallSource::CodeMode {
            cell_id,
            runtime_tool_call_id,
        } => ExtensionToolCallSource::CodeMode {
            cell_id,
            runtime_tool_call_id,
        },
    }
}

#[cfg(test)]
mod tests {
    use super::receipt_terminal_state;
    use codex_extension_api::ToolCallOutcome;
    use codex_tools::ToolOperationTerminalState;

    #[test]
    fn maps_normal_output_to_completed_even_when_tool_reports_failure() {
        assert_eq!(
            receipt_terminal_state(ToolCallOutcome::Completed { success: false }),
            ToolOperationTerminalState::Completed
        );
    }

    #[test]
    fn maps_blocked_and_pre_execution_failure_to_failed() {
        assert_eq!(
            receipt_terminal_state(ToolCallOutcome::Blocked),
            ToolOperationTerminalState::Failed
        );
        assert_eq!(
            receipt_terminal_state(ToolCallOutcome::Failed {
                handler_executed: false,
            }),
            ToolOperationTerminalState::Failed
        );
    }

    #[test]
    fn maps_handler_executed_failure_to_ambiguous() {
        assert_eq!(
            receipt_terminal_state(ToolCallOutcome::Failed {
                handler_executed: true,
            }),
            ToolOperationTerminalState::Ambiguous
        );
    }

    #[test]
    fn maps_unqualified_cancellation_to_ambiguous() {
        assert_eq!(
            receipt_terminal_state(ToolCallOutcome::Aborted),
            ToolOperationTerminalState::Ambiguous
        );
    }
}
