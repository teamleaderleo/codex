#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from textwrap import dedent


def replace_once(path: str, old: str, new: str, label: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


STORE = "codex-rs/thread-store/src/in_memory.rs"
replace_once(
    STORE,
    """struct InMemoryThreadStoreState {
    calls: InMemoryThreadStoreCalls,
    created_threads: HashMap<ThreadId, CreateThreadParams>,
""",
    """struct InMemoryThreadStoreState {
    calls: InMemoryThreadStoreCalls,
    fail_next_append: Option<String>,
    fail_next_append_after_write: Option<String>,
    created_threads: HashMap<ThreadId, CreateThreadParams>,
""",
    "in-memory state fields",
)
replace_once(
    STORE,
    """    pub async fn calls(&self) -> InMemoryThreadStoreCalls {
        self.state.lock().await.calls.clone()
    }

    async fn create_thread(&self, params: CreateThreadParams) -> ThreadStoreResult<()> {
""",
    """    pub async fn calls(&self) -> InMemoryThreadStoreCalls {
        self.state.lock().await.calls.clone()
    }

    /// Causes the next non-empty persisted append to fail before writing.
    ///
    /// This test/debug-only hook exercises production persistence error handling
    /// without replacing `LiveThread`.
    #[doc(hidden)]
    pub async fn fail_next_append_for_test(&self, message: impl Into<String>) {
        self.state.lock().await.fail_next_append = Some(message.into());
    }

    /// Causes the next non-empty append to persist and then return an error once.
    ///
    /// This test/debug-only hook models acknowledgement loss after the write became
    /// authoritative. Callers must treat the append outcome as ambiguous.
    #[doc(hidden)]
    pub async fn fail_next_append_after_write_for_test(
        &self,
        message: impl Into<String>,
    ) {
        self.state.lock().await.fail_next_append_after_write = Some(message.into());
    }

    async fn create_thread(&self, params: CreateThreadParams) -> ThreadStoreResult<()> {
""",
    "in-memory failure hooks",
)
replace_once(
    STORE,
    """        state.calls.append_items += 1;
        state
            .histories
            .entry(params.thread_id)
            .or_default()
            .extend(persisted_items);
        Ok(())
""",
    """        state.calls.append_items += 1;
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
""",
    "in-memory append fault modes",
)

TURN = Path("codex-rs/core/src/session/turn.rs")
text = TURN.read_text(encoding="utf-8")
function_start = text.index("async fn drain_in_flight(")
arm_start = text.index("            Ok(response_input) => {\n", function_start)
arm_end = text.index("            Err(err) => {\n", arm_start)
new_arm = """            Ok(response_input) => {
                record_direct_tool_result(
                    sess.as_ref(),
                    turn_context.as_ref(),
                    response_input,
                )
                .await;
            }
"""
text = text[:arm_start] + new_arm + text[arm_end:]
helper_anchor = "fn response_input_tool_call_id(item: &ResponseInputItem) -> Option<&str> {"
if text.count(helper_anchor) != 1:
    raise SystemExit("direct result helper anchor changed")
helper = """async fn record_direct_tool_result(
    sess: &Session,
    turn_context: &TurnContext,
    response_input: ResponseInputItem,
) {
    let call_id = response_input_tool_call_id(&response_input).map(str::to_string);
    let response_item = response_input.into();
    let result_persisted = sess
        .record_conversation_items(turn_context, std::slice::from_ref(&response_item))
        .await;
    record_direct_tool_result_persistence(sess, call_id.as_deref(), result_persisted).await;
    mark_thread_memory_mode_polluted_if_external_context(sess, turn_context, &response_item).await;
}

"""
TURN.write_text(text.replace(helper_anchor, helper + helper_anchor, 1), encoding="utf-8")

TESTS = Path("codex-rs/core/src/session/turn_tests.rs")
text = TESTS.read_text(encoding="utf-8")
text = text.replace(
    """use codex_protocol::ResponseItemId;
use codex_protocol::items::AgentMessageContent;
""",
    """use codex_protocol::ResponseItemId;
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
""",
    1,
)
text = text.replace(
    """use std::sync::Arc;
use tracing_subscriber::prelude::*;
""",
    """use std::sync::Arc;
use tracing_subscriber::prelude::*;
use uuid::Uuid;
""",
    1,
)
tail_start = text.index("fn direct_function_result(call_id: &str) -> ResponseInputItem {")
new_tail = dedent(
    r'''
    fn direct_function_result(call_id: &str) -> ResponseInputItem {
        ResponseInputItem::FunctionCallOutput {
            call_id: call_id.to_string(),
            output: codex_protocol::models::FunctionCallOutputPayload::from_text("ok".to_string()),
        }
    }

    async fn make_session_with_in_memory_persistence(
    ) -> (Session, TurnContext, Arc<InMemoryThreadStore>) {
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
            .record_tool_operation_terminal(
                "call-ephemeral",
                ToolOperationTerminalState::Completed,
            )
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
            .record_tool_operation_terminal(
                "call-success",
                ToolOperationTerminalState::Completed,
            )
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
        assert!(has_persisted_function_result(&persisted.items, "call-success"));
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
            .record_tool_operation_terminal(
                "call-failure",
                ToolOperationTerminalState::Completed,
            )
            .await;
        store.fail_next_append_for_test("injected append failure").await;
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
        assert!(!has_persisted_function_result(&persisted.items, "call-failure"));
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
            .record_tool_operation_terminal(
                "call-duplicate",
                ToolOperationTerminalState::Completed,
            )
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
        record_direct_tool_result_persistence(
            &session,
            response_input_tool_call_id(&result),
            true,
        )
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
    '''
)
TESTS.write_text(text[:tail_start] + new_tail, encoding="utf-8")
