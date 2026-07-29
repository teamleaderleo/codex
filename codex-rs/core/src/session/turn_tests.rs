use super::*;
use codex_extension_api::ExtensionData;
use codex_extension_api::TurnItemContributor;
use codex_protocol::ResponseItemId;
use codex_protocol::items::AgentMessageContent;
use codex_tools::ToolOperationEffect;
use codex_tools::ToolOperationResultState;
use codex_tools::ToolOperationTerminalState;
use pretty_assertions::assert_eq;
use std::sync::Arc;
use tracing_subscriber::prelude::*;

struct RewriteAgentMessageContributor;

impl TurnItemContributor for RewriteAgentMessageContributor {
    fn contribute<'a>(
        &'a self,
        _thread_store: &'a ExtensionData,
        _turn_store: &'a ExtensionData,
        item: &'a mut TurnItem,
    ) -> codex_extension_api::ExtensionFuture<'a, Result<(), String>> {
        Box::pin(async move {
            if let TurnItem::AgentMessage(agent_message) = item {
                agent_message.content = vec![AgentMessageContent::Text {
                    text: "plan contributed assistant text".to_string(),
                }];
            }
            Ok(())
        })
    }
}

fn assistant_output_text(text: &str) -> ResponseItem {
    ResponseItem::Message {
        id: Some(ResponseItemId::with_suffix("msg", "1")),
        role: "assistant".to_string(),
        content: vec![ContentItem::OutputText {
            text: text.to_string(),
        }],
        phase: None,
        internal_chat_message_metadata_passthrough: None,
    }
}

#[test]
fn post_sampling_token_estimate_is_disabled_by_always_on_sinks() {
    let feedback = codex_feedback::CodexFeedback::new();
    let subscriber = tracing_subscriber::registry()
        .with(feedback.logger_layer())
        .with(tracing_subscriber::fmt::layer().with_filter(codex_state::log_db::default_filter()));

    tracing::subscriber::with_default(subscriber, || {
        assert!(!tracing::event_enabled!(
            target: POST_SAMPLING_TOKEN_ESTIMATE_TARGET,
            tracing::Level::TRACE,
            turn_id,
            estimated_token_count,
            message
        ));
    });
}

#[tokio::test]
async fn plan_mode_uses_contributed_turn_item_for_last_agent_message() {
    let (mut session, turn_context) = crate::session::tests::make_session_and_context().await;
    let mut builder = codex_extension_api::ExtensionRegistryBuilder::new();
    builder.turn_item_contributor(Arc::new(RewriteAgentMessageContributor));
    session.services.extensions = Arc::new(builder.build());
    let turn_store = ExtensionData::new(turn_context.sub_id.clone());
    let mut state = PlanModeStreamState::new(&turn_context.sub_id);
    let mut last_agent_message = None;
    let item = assistant_output_text("original assistant text");

    let handled = handle_assistant_item_done_in_plan_mode(
        &session,
        &turn_context,
        &turn_store,
        &item,
        &mut state,
        /*previously_active_item*/ None,
        &mut last_agent_message,
    )
    .await;

    assert!(handled);
    assert_eq!(
        last_agent_message.as_deref(),
        Some("plan contributed assistant text")
    );
}

#[test]
fn response_input_tool_call_id_tracks_direct_tool_results() {
    let function = ResponseInputItem::FunctionCallOutput {
        call_id: "function-call".to_string(),
        output: codex_protocol::models::FunctionCallOutputPayload::from_text("ok".to_string()),
    };
    let custom = ResponseInputItem::CustomToolCallOutput {
        call_id: "custom-call".to_string(),
        name: Some("custom".to_string()),
        output: codex_protocol::models::FunctionCallOutputPayload::from_text("ok".to_string()),
    };
    let client_search = ResponseInputItem::ToolSearchOutput {
        call_id: "search-call".to_string(),
        status: "completed".to_string(),
        execution: "client".to_string(),
        tools: Vec::new(),
    };
    let server_search = ResponseInputItem::ToolSearchOutput {
        call_id: "server-search".to_string(),
        status: "completed".to_string(),
        execution: "server".to_string(),
        tools: Vec::new(),
    };
    let message = ResponseInputItem::Message {
        role: "assistant".to_string(),
        content: Vec::new(),
        phase: None,
    };

    assert_eq!(
        response_input_tool_call_id(&function),
        Some("function-call")
    );
    assert_eq!(response_input_tool_call_id(&custom), Some("custom-call"));
    assert_eq!(
        response_input_tool_call_id(&client_search),
        Some("search-call")
    );
    assert_eq!(response_input_tool_call_id(&server_search), None);
    assert_eq!(response_input_tool_call_id(&message), None);
}

fn direct_function_result(call_id: &str) -> ResponseInputItem {
    ResponseInputItem::FunctionCallOutput {
        call_id: call_id.to_string(),
        output: codex_protocol::models::FunctionCallOutputPayload::from_text("ok".to_string()),
    }
}

#[tokio::test]
async fn direct_tool_result_persistence_marks_success_after_authoritative_append() {
    let (session, _) = crate::session::tests::make_session_and_context().await;
    session
        .begin_tool_operation_receipt(
            "call-success".to_string(),
            ToolOperationEffect::PotentialMutation,
        )
        .await;
    session
        .record_tool_operation_terminal("call-success", ToolOperationTerminalState::Completed)
        .await;
    let result = direct_function_result("call-success");

    record_direct_tool_result_persistence(&session, response_input_tool_call_id(&result), true)
        .await;

    let receipt = session
        .tool_operation_receipt("call-success")
        .await
        .expect("receipt should exist");
    assert_eq!(receipt.result_state, ToolOperationResultState::Persisted);
    assert!(!session.has_unreconciled_potential_mutation().await);
}

#[tokio::test]
async fn direct_tool_result_persistence_marks_append_failure_ambiguous() {
    let (session, _) = crate::session::tests::make_session_and_context().await;
    session
        .begin_tool_operation_receipt(
            "call-failure".to_string(),
            ToolOperationEffect::PotentialMutation,
        )
        .await;
    session
        .record_tool_operation_terminal("call-failure", ToolOperationTerminalState::Completed)
        .await;
    let result = direct_function_result("call-failure");

    record_direct_tool_result_persistence(&session, response_input_tool_call_id(&result), false)
        .await;

    let receipt = session
        .tool_operation_receipt("call-failure")
        .await
        .expect("receipt should exist");
    assert_eq!(receipt.result_state, ToolOperationResultState::Ambiguous);
    assert!(session.has_unreconciled_potential_mutation().await);
}

#[tokio::test]
async fn direct_tool_result_persistence_marks_duplicate_observation_ambiguous() {
    let (session, _) = crate::session::tests::make_session_and_context().await;
    session
        .begin_tool_operation_receipt(
            "call-duplicate".to_string(),
            ToolOperationEffect::PotentialMutation,
        )
        .await;
    session
        .record_tool_operation_terminal("call-duplicate", ToolOperationTerminalState::Completed)
        .await;
    let result = direct_function_result("call-duplicate");
    let call_id = response_input_tool_call_id(&result);

    record_direct_tool_result_persistence(&session, call_id, true).await;
    record_direct_tool_result_persistence(&session, call_id, true).await;

    let receipt = session
        .tool_operation_receipt("call-duplicate")
        .await
        .expect("receipt should exist");
    assert_eq!(receipt.result_state, ToolOperationResultState::Ambiguous);
    assert!(session.has_unreconciled_potential_mutation().await);
}

#[tokio::test]
async fn direct_tool_result_persistence_without_begin_stays_unreconciled() {
    let (session, _) = crate::session::tests::make_session_and_context().await;
    let result = direct_function_result("call-missing-begin");

    record_direct_tool_result_persistence(&session, response_input_tool_call_id(&result), true)
        .await;

    let receipt = session
        .tool_operation_receipt("call-missing-begin")
        .await
        .expect("late result should create a conservative receipt");
    assert_eq!(receipt.effect, ToolOperationEffect::PotentialMutation);
    assert_eq!(receipt.terminal_state, ToolOperationTerminalState::Pending);
    assert_eq!(receipt.result_state, ToolOperationResultState::Persisted);
    assert!(session.has_unreconciled_potential_mutation().await);
}
