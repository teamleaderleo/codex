use super::*;
use codex_extension_api::ExtensionData;
use codex_extension_api::TurnItemContributor;
use codex_protocol::ResponseItemId;
use codex_protocol::items::AgentMessageContent;
use codex_protocol::models::BaseInstructions;
use codex_protocol::protocol::RolloutItem;
use codex_protocol::protocol::SessionSource;
use codex_protocol::protocol::ThreadMemoryMode;
use codex_thread_store::CreateThreadParams;
use codex_thread_store::InMemoryThreadStore;
use codex_thread_store::LiveThread;
use codex_thread_store::ThreadPersistenceMetadata;
use codex_thread_store::ThreadStore;
use codex_tools::ToolOperationEffect;
use codex_tools::ToolOperationResultState;
use codex_tools::ToolOperationTerminalState;
use pretty_assertions::assert_eq;
use std::sync::Arc;
use tracing_subscriber::prelude::*;
use uuid::Uuid;

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

async fn make_session_with_in_memory_persistence()
-> (Session, TurnContext, Arc<InMemoryThreadStore>) {
    let (mut session, turn_context) = crate::session::tests::make_session_and_context().await;
    let store = Arc::new(InMemoryThreadStore::default());
    let thread_store: Arc<dyn ThreadStore> = store.clone();
    let config = session.get_config().await;
    let live_thread = LiveThread::create(
        Arc::clone(&thread_store),
        CreateThreadParams {
            session_id: session.session_id(),
            thread_id: session.thread_id(),
            extra_config: None,
            forked_from_id: None,
            parent_thread_id: None,
            source: SessionSource::Exec,
            thread_source: None,
            originator: "test_originator".to_string(),
            base_instructions: BaseInstructions::default(),
            dynamic_tools: Vec::new(),
            selected_capability_roots: Vec::new(),
            multi_agent_version: None,
            history_mode: Default::default(),
            history_base: None,
            subagent_history_start_ordinal: None,
            initial_window_id: Uuid::now_v7().to_string(),
            metadata: ThreadPersistenceMetadata {
                cwd: Some(config.cwd.to_path_buf()),
                model_provider: config.model_provider_id.clone(),
                memory_mode: ThreadMemoryMode::Enabled,
            },
        },
    )
    .await
    .expect("create in-memory thread persistence");
    session.services.thread_store = thread_store;
    session.services.live_thread = Some(live_thread);
    (session, turn_context, store)
}

fn has_persisted_function_result(items: &[RolloutItem], call_id: &str) -> bool {
    items.iter().any(|item| {
        matches!(
            item,
            RolloutItem::ResponseItem(ResponseItem::FunctionCallOutput {
                call_id: persisted_call_id,
                ..
            }) if persisted_call_id == call_id
        )
    })
}

fn has_in_memory_function_result(items: &[ResponseItem], call_id: &str) -> bool {
    items.iter().any(|item| {
        matches!(
            item,
            ResponseItem::FunctionCallOutput {
                call_id: observed_call_id,
                ..
            } if observed_call_id == call_id
        )
    })
}

#[tokio::test]
async fn direct_tool_result_persistence_treats_ephemeral_history_as_authoritative() {
    let (session, turn_context) = crate::session::tests::make_session_and_context().await;
    session
        .begin_tool_operation_receipt(
            "call-ephemeral".to_string(),
            ToolOperationEffect::PotentialMutation,
        )
        .await;
    session
        .record_tool_operation_terminal("call-ephemeral", ToolOperationTerminalState::Completed)
        .await;
    record_direct_tool_result(
        &session,
        &turn_context,
        direct_function_result("call-ephemeral"),
    )
    .await;
    let receipt = session
        .tool_operation_receipt("call-ephemeral")
        .await
        .expect("receipt should exist");
    assert_eq!(receipt.result_state, ToolOperationResultState::Persisted);
    assert!(!session.has_unreconciled_potential_mutation().await);
    assert!(has_in_memory_function_result(
        session.clone_history().await.raw_items(),
        "call-ephemeral",
    ));
}

#[tokio::test]
async fn direct_tool_result_persistence_uses_successful_authoritative_append() {
    let (session, turn_context, store) = make_session_with_in_memory_persistence().await;
    session
        .begin_tool_operation_receipt(
            "call-success".to_string(),
            ToolOperationEffect::PotentialMutation,
        )
        .await;
    session
        .record_tool_operation_terminal("call-success", ToolOperationTerminalState::Completed)
        .await;
    record_direct_tool_result(
        &session,
        &turn_context,
        direct_function_result("call-success"),
    )
    .await;
    let receipt = session
        .tool_operation_receipt("call-success")
        .await
        .expect("receipt should exist");
    assert_eq!(receipt.result_state, ToolOperationResultState::Persisted);
    assert!(!session.has_unreconciled_potential_mutation().await);
    assert_eq!(store.calls().await.append_items, 1);
    let persisted = session
        .services
        .live_thread
        .as_ref()
        .expect("live thread")
        .load_history(/*include_archived*/ true)
        .await
        .expect("load persisted history");
    assert!(has_persisted_function_result(
        &persisted.items,
        "call-success"
    ));
    assert!(has_in_memory_function_result(
        session.clone_history().await.raw_items(),
        "call-success",
    ));
}

#[tokio::test]
async fn direct_tool_result_persistence_marks_real_append_failure_ambiguous() {
    let (session, turn_context, store) = make_session_with_in_memory_persistence().await;
    session
        .begin_tool_operation_receipt(
            "call-failure".to_string(),
            ToolOperationEffect::PotentialMutation,
        )
        .await;
    session
        .record_tool_operation_terminal("call-failure", ToolOperationTerminalState::Completed)
        .await;
    store
        .fail_next_append_for_test("injected append failure")
        .await;
    record_direct_tool_result(
        &session,
        &turn_context,
        direct_function_result("call-failure"),
    )
    .await;
    let receipt = session
        .tool_operation_receipt("call-failure")
        .await
        .expect("receipt should exist");
    assert_eq!(receipt.result_state, ToolOperationResultState::Ambiguous);
    assert!(session.has_unreconciled_potential_mutation().await);
    assert_eq!(store.calls().await.append_items, 1);
    let persisted = session
        .services
        .live_thread
        .as_ref()
        .expect("live thread")
        .load_history(/*include_archived*/ true)
        .await
        .expect("load persisted history");
    assert!(!has_persisted_function_result(
        &persisted.items,
        "call-failure"
    ));
    assert!(has_in_memory_function_result(
        session.clone_history().await.raw_items(),
        "call-failure",
    ));
}

#[tokio::test]
async fn direct_tool_result_persistence_recovers_after_one_shot_append_failure() {
    let (session, turn_context, store) = make_session_with_in_memory_persistence().await;
    for call_id in ["call-first-failure", "call-after-failure"] {
        session
            .begin_tool_operation_receipt(
                call_id.to_string(),
                ToolOperationEffect::PotentialMutation,
            )
            .await;
        session
            .record_tool_operation_terminal(call_id, ToolOperationTerminalState::Completed)
            .await;
        if call_id == "call-first-failure" {
            store
                .fail_next_append_for_test("injected one-shot append failure")
                .await;
        }
        record_direct_tool_result(&session, &turn_context, direct_function_result(call_id)).await;
    }
    assert_eq!(
        session
            .tool_operation_receipt("call-first-failure")
            .await
            .expect("first receipt")
            .result_state,
        ToolOperationResultState::Ambiguous
    );
    assert_eq!(
        session
            .tool_operation_receipt("call-after-failure")
            .await
            .expect("second receipt")
            .result_state,
        ToolOperationResultState::Persisted
    );
    assert!(session.has_unreconciled_potential_mutation().await);
    assert_eq!(store.calls().await.append_items, 2);
    let persisted = session
        .services
        .live_thread
        .as_ref()
        .expect("live thread")
        .load_history(/*include_archived*/ true)
        .await
        .expect("load persisted history");
    assert!(!has_persisted_function_result(
        &persisted.items,
        "call-first-failure",
    ));
    assert!(has_persisted_function_result(
        &persisted.items,
        "call-after-failure",
    ));
}

#[tokio::test]
async fn direct_tool_result_persistence_marks_commit_then_error_ambiguous() {
    let (session, turn_context, store) = make_session_with_in_memory_persistence().await;
    for call_id in ["call-commit-error", "call-after-commit-error"] {
        session
            .begin_tool_operation_receipt(
                call_id.to_string(),
                ToolOperationEffect::PotentialMutation,
            )
            .await;
        session
            .record_tool_operation_terminal(call_id, ToolOperationTerminalState::Completed)
            .await;
        if call_id == "call-commit-error" {
            store
                .fail_next_append_after_write_for_test(
                    "injected acknowledgement failure after durable append",
                )
                .await;
        }
        record_direct_tool_result(&session, &turn_context, direct_function_result(call_id)).await;
    }
    assert_eq!(
        session
            .tool_operation_receipt("call-commit-error")
            .await
            .expect("ambiguous receipt")
            .result_state,
        ToolOperationResultState::Ambiguous
    );
    assert_eq!(
        session
            .tool_operation_receipt("call-after-commit-error")
            .await
            .expect("later receipt")
            .result_state,
        ToolOperationResultState::Persisted
    );
    assert!(session.has_unreconciled_potential_mutation().await);
    assert_eq!(store.calls().await.append_items, 2);
    let persisted = session
        .services
        .live_thread
        .as_ref()
        .expect("live thread")
        .load_history(/*include_archived*/ true)
        .await
        .expect("load persisted history");
    assert!(has_persisted_function_result(
        &persisted.items,
        "call-commit-error",
    ));
    assert!(has_persisted_function_result(
        &persisted.items,
        "call-after-commit-error",
    ));
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
