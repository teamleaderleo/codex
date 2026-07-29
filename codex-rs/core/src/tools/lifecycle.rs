use codex_extension_api::ToolCallOutcome;
use codex_extension_api::ToolCallSource as ExtensionToolCallSource;
use codex_extension_api::ToolFinishInput;
use codex_extension_api::ToolStartInput;
use codex_tools::ToolName;
use codex_tools::ToolOperationEffect;
use codex_tools::ToolOperationTerminalState;

use crate::session::session::Session;
use crate::session::turn_context::TurnContext;
use crate::tools::context::ToolCallSource;
use crate::tools::context::ToolInvocation;

pub(crate) async fn notify_tool_start(invocation: &ToolInvocation) {
    if let Some(turn_state) = matching_active_turn_state(
        invocation.session.as_ref(),
        invocation.turn.as_ref(),
    )
    .await
    {
        turn_state.lock().await.begin_tool_operation(
            invocation.call_id.clone(),
            ToolOperationEffect::PotentialMutation,
        );
    }

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
    )
    .await;
}

pub(crate) async fn notify_tool_aborted(
    session: &Session,
    turn: &TurnContext,
    call_id: &str,
    tool_name: &ToolName,
    source: ToolCallSource,
) {
    notify_tool_finish_parts(
        session,
        turn,
        call_id,
        tool_name,
        source,
        ToolCallOutcome::Aborted,
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
) {
    if let Some(turn_state) = matching_active_turn_state(session, turn).await {
        turn_state
            .lock()
            .await
            .record_tool_operation_terminal(call_id, receipt_terminal_state(outcome));
    }

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

async fn matching_active_turn_state(
    session: &Session,
    turn: &TurnContext,
) -> Option<std::sync::Arc<tokio::sync::Mutex<crate::state::TurnState>>> {
    let active_turn = session.active_turn.lock().await;
    active_turn.as_ref().and_then(|active_turn| {
        let task = active_turn.task.as_ref()?;
        (task.turn_context.sub_id == turn.sub_id).then(|| active_turn.turn_state.clone())
    })
}

fn receipt_terminal_state(outcome: ToolCallOutcome) -> ToolOperationTerminalState {
    match outcome {
        ToolCallOutcome::Completed { .. } => ToolOperationTerminalState::Completed,
        ToolCallOutcome::Blocked | ToolCallOutcome::Failed { .. } => {
            ToolOperationTerminalState::Failed
        }
        ToolCallOutcome::Aborted => ToolOperationTerminalState::Aborted,
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
    fn maps_blocked_and_failed_to_failed() {
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
        assert_eq!(
            receipt_terminal_state(ToolCallOutcome::Failed {
                handler_executed: true,
            }),
            ToolOperationTerminalState::Failed
        );
    }

    #[test]
    fn maps_cancellation_to_aborted() {
        assert_eq!(
            receipt_terminal_state(ToolCallOutcome::Aborted),
            ToolOperationTerminalState::Aborted
        );
    }
}
