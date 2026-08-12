from pathlib import Path

SESSION = Path('codex-rs/core/src/session/mod.rs')
TESTS = Path('codex-rs/core/src/session/turn_tests.rs')
STORE = Path('codex-rs/thread-store/src/in_memory.rs')

session = SESSION.read_text()

old = '''    pub(crate) async fn record_conversation_items(
        &self,
        turn_context: &TurnContext,
        items: &[ResponseItem],
    ) {
'''
new = '''    pub(crate) async fn record_conversation_items(
        &self,
        turn_context: &TurnContext,
        items: &[ResponseItem],
    ) -> bool {
'''
assert session.count(old) == 1, session.count(old)
session = session.replace(old, new, 1)

old = '''        self.persist_rollout_response_items(items).await;
        self.send_raw_response_items(turn_context, items).await;
    }
'''
new = '''        let persisted = self.persist_rollout_response_items(items).await;
        self.send_raw_response_items(turn_context, items).await;
        persisted
    }
'''
assert session.count(old) == 1, session.count(old)
session = session.replace(old, new, 1)

old = '''    async fn persist_rollout_response_items(&self, items: &[ResponseItem]) {
        let rollout_items: Vec<RolloutItem> = items
            .iter()
            .cloned()
            .map(ResponseItemEnvelope::new)
            .map(RolloutItem::ResponseItem)
            .collect();
        self.persist_rollout_items(&rollout_items).await;
    }
'''
new = '''    async fn persist_rollout_response_items(&self, items: &[ResponseItem]) -> bool {
        let rollout_items: Vec<RolloutItem> = items
            .iter()
            .cloned()
            .map(ResponseItemEnvelope::new)
            .map(RolloutItem::ResponseItem)
            .collect();
        self.persist_rollout_items_checked(&rollout_items).await
    }
'''
assert session.count(old) == 1, session.count(old)
session = session.replace(old, new, 1)

old = '''    #[tracing::instrument(level = "trace", skip_all, fields(item_count = items.len()))]
    pub(crate) async fn persist_rollout_items(&self, items: &[RolloutItem]) {
        if let Some(live_thread) = self.live_thread()
            && let Err(e) = live_thread.append_items(items).await
        {
            error!("failed to record rollout items: {e:#}");
        }
    }
'''
new = '''    #[tracing::instrument(level = "trace", skip_all, fields(item_count = items.len()))]
    pub(crate) async fn persist_rollout_items(&self, items: &[RolloutItem]) {
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
'''
assert session.count(old) == 1, session.count(old)
session = session.replace(old, new, 1)
SESSION.write_text(session)

store = STORE.read_text()
old = '''struct InMemoryThreadStoreState {
    calls: InMemoryThreadStoreCalls,
    created_threads: HashMap<ThreadId, CreateThreadParams>,
'''
new = '''struct InMemoryThreadStoreState {
    calls: InMemoryThreadStoreCalls,
    fail_next_append: Option<String>,
    fail_next_append_after_write: Option<String>,
    created_threads: HashMap<ThreadId, CreateThreadParams>,
'''
assert store.count(old) == 1, store.count(old)
store = store.replace(old, new, 1)

old = '''    pub async fn calls(&self) -> InMemoryThreadStoreCalls {
        self.state.lock().await.calls.clone()
    }

    async fn create_thread(&self, params: CreateThreadParams) -> ThreadStoreResult<()> {
'''
new = '''    pub async fn calls(&self) -> InMemoryThreadStoreCalls {
        self.state.lock().await.calls.clone()
    }

    /// Causes the next non-empty persisted append to fail before writing.
    #[doc(hidden)]
    pub async fn fail_next_append_for_test(&self, message: impl Into<String>) {
        self.state.lock().await.fail_next_append = Some(message.into());
    }

    /// Causes the next non-empty append to persist and then return an error once.
    #[doc(hidden)]
    pub async fn fail_next_append_after_write_for_test(&self, message: impl Into<String>) {
        self.state.lock().await.fail_next_append_after_write = Some(message.into());
    }

    async fn create_thread(&self, params: CreateThreadParams) -> ThreadStoreResult<()> {
'''
assert store.count(old) == 1, store.count(old)
store = store.replace(old, new, 1)

old = '''        state.calls.append_items += 1;
        state
            .histories
            .entry(params.thread_id)
            .or_default()
            .extend(persisted_items);
        Ok(())
'''
new = '''        state.calls.append_items += 1;
        if let Some(message) = state.fail_next_append.take() {
            return Err(ThreadStoreError::Internal { message });
        }
        let fail_after_write = state.fail_next_append_after_write.take();
        state
            .histories
            .entry(params.thread_id)
            .or_default()
            .extend(persisted_items);
        if let Some(message) = fail_after_write {
            return Err(ThreadStoreError::Internal { message });
        }
        Ok(())
'''
assert store.count(old) == 1, store.count(old)
store = store.replace(old, new, 1)
STORE.write_text(store)

tests = TESTS.read_text()
imports = '''use codex_protocol::items::AgentMessageContent;
use pretty_assertions::assert_eq;
use std::sync::Arc;
'''
imports_new = '''use codex_protocol::items::AgentMessageContent;
use codex_protocol::models::BaseInstructions;
use codex_protocol::protocol::SessionSource;
use codex_protocol::protocol::ThreadMemoryMode;
use codex_rollout::RolloutItem;
use codex_thread_store::CreateThreadParams;
use codex_thread_store::InMemoryThreadStore;
use codex_thread_store::LiveThread;
use codex_thread_store::ThreadPersistenceMetadata;
use codex_thread_store::ThreadStore;
use pretty_assertions::assert_eq;
use std::sync::Arc;
use uuid::Uuid;
'''
assert tests.count(imports) == 1, tests.count(imports)
tests = tests.replace(imports, imports_new, 1)

extra = r'''

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
    items.iter().any(|item| match item {
        RolloutItem::ResponseItem(envelope) => matches!(
            &envelope.item,
            ResponseItem::FunctionCallOutput { call_id: observed, .. } if observed == call_id
        ),
        _ => false,
    })
}

#[tokio::test]
async fn append_outcome_ephemeral_history_is_authoritative() {
    let (session, turn_context) = crate::session::tests::make_session_and_context().await;
    let item = append_outcome_function_result("ephemeral");
    assert!(session.record_conversation_items(&turn_context, std::slice::from_ref(&item)).await);
}

#[tokio::test]
async fn append_outcome_reports_successful_live_append() {
    let (session, turn_context, store) = make_append_outcome_session().await;
    let item = append_outcome_function_result("persisted");
    assert!(session.record_conversation_items(&turn_context, std::slice::from_ref(&item)).await);
    assert_eq!(store.calls().await.append_items, 1);
    let history = session.services.live_thread.as_ref().expect("live thread")
        .load_history(true).await.expect("load history");
    assert!(append_outcome_history_contains(&history.items, "persisted"));
}

#[tokio::test]
async fn append_outcome_reports_prewrite_failure() {
    let (session, turn_context, store) = make_append_outcome_session().await;
    store.fail_next_append_for_test("prewrite failure").await;
    let item = append_outcome_function_result("prewrite");
    assert!(!session.record_conversation_items(&turn_context, std::slice::from_ref(&item)).await);
    let history = session.services.live_thread.as_ref().expect("live thread")
        .load_history(true).await.expect("load history");
    assert!(!append_outcome_history_contains(&history.items, "prewrite"));
}

#[tokio::test]
async fn append_outcome_reports_commit_then_error_as_failure() {
    let (session, turn_context, store) = make_append_outcome_session().await;
    store.fail_next_append_after_write_for_test("acknowledgement loss").await;
    let item = append_outcome_function_result("commit-error");
    assert!(!session.record_conversation_items(&turn_context, std::slice::from_ref(&item)).await);
    let history = session.services.live_thread.as_ref().expect("live thread")
        .load_history(true).await.expect("load history");
    assert!(append_outcome_history_contains(&history.items, "commit-error"));
}
'''
assert 'append_outcome_reports_prewrite_failure' not in tests
tests = tests.rstrip() + extra + '\n'
TESTS.write_text(tests)
