from pathlib import Path

session = Path("codex-rs/core/src/session/mod.rs")
text = session.read_text(encoding="utf-8")

start = text.index("    pub(crate) async fn record_conversation_items(")
end = text.index("\n    pub(crate) async fn record_step_world_state_if_changed(", start)
replacement = """    pub(crate) async fn record_conversation_items(
    &self,
    turn_context: &TurnContext,
    items: &[ResponseItem],
) -> bool {
    let items = self.prepare_conversation_items_for_history(turn_context, items);
    let items = items.as_ref();
    {
        let mut state = self.state.lock().await;
        state.current_time_reminder.note_recorded_items(items);
        state.record_items(
            items.iter(),
            turn_context.model_info.truncation_policy.into(),
        );
    }
    let persisted = self.persist_rollout_response_items(items).await;
    self.send_raw_response_items(turn_context, items).await;
    persisted
}
"""
text = text[:start] + replacement + text[end:]

start = text.index("    async fn persist_rollout_response_items(")
end = text.index("\n    pub fn enabled(", start)
replacement = """    async fn persist_rollout_response_items(&self, items: &[ResponseItem]) -> bool {
    let rollout_items: Vec<RolloutItem> = items
        .iter()
        .cloned()
        .map(RolloutItem::ResponseItem)
        .collect();
    self.persist_rollout_items_checked(&rollout_items).await
}
"""
text = text[:start] + replacement + text[end:]

start = text.index("    pub(crate) async fn persist_rollout_items(")
end = text.index("\n    pub(crate) async fn clone_history(", start)
replacement = """    pub(crate) async fn persist_rollout_items(&self, items: &[RolloutItem]) {
    let _ = self.persist_rollout_items_checked(items).await;
}

async fn persist_rollout_items_checked(&self, items: &[RolloutItem]) -> bool {
    let Some(live_thread) = self.live_thread() else {
        return true;
    };
    if let Err(e) = live_thread.append_items(items).await {
        error!("failed to record rollout items: {e:#}");
        return false;
    }
    true
}
"""
text = text[:start] + replacement + text[end:]
session.write_text(text, encoding="utf-8")

tests = Path("codex-rs/core/src/session/turn_tests.rs")
text = tests.read_text(encoding="utf-8")
import_anchor = "use codex_protocol::items::AgentMessageContent;\n"
imports = """use codex_protocol::models::BaseInstructions;
use codex_protocol::protocol::RolloutItem;
use codex_protocol::protocol::SessionSource;
use codex_protocol::protocol::ThreadMemoryMode;
use codex_thread_store::CreateThreadParams;
use codex_thread_store::InMemoryThreadStore;
use codex_thread_store::LiveThread;
use codex_thread_store::ThreadPersistenceMetadata;
use codex_thread_store::ThreadStore;
use uuid::Uuid;
"""
if text.count(import_anchor) != 1:
    raise SystemExit("turn test import anchor changed")
text = text.replace(import_anchor, import_anchor + imports, 1)

if "append_outcome_ephemeral_history_is_authoritative" in text:
    raise SystemExit("append outcome tests already installed")
additions = """

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
    assert!(append_outcome_history_contains(&history.items, "commit-error"));
}
"""
tests.write_text(text + additions, encoding="utf-8")
