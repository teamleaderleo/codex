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

fn append_outcome_function_result(call_id: &str) -> ResponseItem {
    ResponseItem::FunctionCallOutput {
        id: None,
        call_id: call_id.to_string(),
        output: codex_protocol::models::FunctionCallOutputPayload::from_text("ok".to_string()),
        internal_chat_message_metadata_passthrough: None,
    }
}

async fn make_append_outcome_session() -> (Session, TurnContext, Arc<InMemoryThreadStore>) {
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

fn append_outcome_history_contains(items: &[RolloutItem], call_id: &str) -> bool {
    items.iter().any(|item| {
        matches!(
            item,
            RolloutItem::ResponseItem(ResponseItem::FunctionCallOutput {
                call_id: observed,
                ..
            }) if observed == call_id
        )
    })
}

#[tokio::test]
async fn append_outcome_ephemeral_history_is_authoritative() {
    let (session, turn_context) = crate::session::tests::make_session_and_context().await;
    let item = append_outcome_function_result("ephemeral");
    assert!(
        session
            .record_conversation_items(&turn_context, std::slice::from_ref(&item))
            .await
    );
}

#[tokio::test]
async fn append_outcome_reports_successful_live_append() {
    let (session, turn_context, store) = make_append_outcome_session().await;
    let item = append_outcome_function_result("persisted");
    assert!(
        session
            .record_conversation_items(&turn_context, std::slice::from_ref(&item))
            .await
    );
    assert_eq!(store.calls().await.append_items, 1);
    let history = session
        .services
        .live_thread
        .as_ref()
        .expect("live thread")
        .load_history(/*include_archived*/ true)
        .await
        .expect("load history");
    assert!(append_outcome_history_contains(&history.items, "persisted"));
}

#[tokio::test]
async fn append_outcome_reports_prewrite_failure() {
    let (session, turn_context, store) = make_append_outcome_session().await;
    store.fail_next_append_for_test("prewrite failure").await;
    let item = append_outcome_function_result("prewrite");
    assert!(
        !session
            .record_conversation_items(&turn_context, std::slice::from_ref(&item))
            .await
    );
    let history = session
        .services
        .live_thread
        .as_ref()
        .expect("live thread")
        .load_history(/*include_archived*/ true)
        .await
        .expect("load history");
    assert!(!append_outcome_history_contains(&history.items, "prewrite"));
}

#[tokio::test]
async fn append_outcome_reports_commit_then_error_as_failure() {
    let (session, turn_context, store) = make_append_outcome_session().await;
    store
        .fail_next_append_after_write_for_test("acknowledgement loss")
        .await;
    let item = append_outcome_function_result("commit-error");
    assert!(
        !session
            .record_conversation_items(&turn_context, std::slice::from_ref(&item))
            .await
    );
    let history = session
        .services
        .live_thread
        .as_ref()
        .expect("live thread")
        .load_history(/*include_archived*/ true)
        .await
        .expect("load history");
    assert!(append_outcome_history_contains(
        &history.items,
        "commit-error"
    ));
}
