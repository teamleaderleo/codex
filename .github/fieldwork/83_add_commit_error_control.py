from pathlib import Path
from textwrap import dedent


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one anchor, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


store_path = "codex-rs/thread-store/src/in_memory.rs"
replace_once(
    store_path,
    """    calls: InMemoryThreadStoreCalls,
    fail_next_append: Option<String>,
    created_threads: HashMap<ThreadId, CreateThreadParams>,
""",
    """    calls: InMemoryThreadStoreCalls,
    fail_next_append: Option<String>,
    fail_next_append_after_write: Option<String>,
    created_threads: HashMap<ThreadId, CreateThreadParams>,
""",
)
replace_once(
    store_path,
    """    #[doc(hidden)]
    pub async fn fail_next_append_for_test(&self, message: impl Into<String>) {
        self.state.lock().await.fail_next_append = Some(message.into());
    }

    async fn create_thread(&self, params: CreateThreadParams) -> ThreadStoreResult<()> {
""",
    """    #[doc(hidden)]
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
)
replace_once(
    store_path,
    """        state.calls.append_items += 1;
        if let Some(message) = state.fail_next_append.take() {
            return Err(ThreadStoreError::Internal { message });
        }
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
)

tests = Path("codex-rs/core/src/session/turn_tests.rs")
text = tests.read_text(encoding="utf-8")
test_name = "direct_tool_result_persistence_marks_commit_then_error_ambiguous"
if test_name in text:
    raise SystemExit(f"{test_name} already exists")
text += dedent(
    r'''

#[tokio::test]
async fn direct_tool_result_persistence_marks_commit_then_error_ambiguous() {
    let (session, turn_context, store) = make_session_with_in_memory_persistence().await;

    session
        .begin_tool_operation_receipt(
            "call-commit-error".to_string(),
            ToolOperationEffect::PotentialMutation,
        )
        .await;
    session
        .record_tool_operation_terminal(
            "call-commit-error",
            ToolOperationTerminalState::Completed,
        )
        .await;
    store
        .fail_next_append_after_write_for_test(
            "injected acknowledgement failure after durable append",
        )
        .await;

    record_direct_tool_result(
        &session,
        &turn_context,
        direct_function_result("call-commit-error"),
    )
    .await;

    let ambiguous_receipt = session
        .tool_operation_receipt("call-commit-error")
        .await
        .expect("ambiguous receipt should exist");
    assert_eq!(
        ambiguous_receipt.result_state,
        ToolOperationResultState::Ambiguous
    );
    assert!(session.has_unreconciled_potential_mutation().await);

    session
        .begin_tool_operation_receipt(
            "call-after-commit-error".to_string(),
            ToolOperationEffect::PotentialMutation,
        )
        .await;
    session
        .record_tool_operation_terminal(
            "call-after-commit-error",
            ToolOperationTerminalState::Completed,
        )
        .await;
    record_direct_tool_result(
        &session,
        &turn_context,
        direct_function_result("call-after-commit-error"),
    )
    .await;

    let ambiguous_receipt = session
        .tool_operation_receipt("call-commit-error")
        .await
        .expect("ambiguous receipt should remain");
    assert_eq!(
        ambiguous_receipt.result_state,
        ToolOperationResultState::Ambiguous
    );
    let recovered_receipt = session
        .tool_operation_receipt("call-after-commit-error")
        .await
        .expect("later receipt should exist");
    assert_eq!(
        recovered_receipt.result_state,
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

    let in_memory = session.clone_history().await;
    assert!(has_in_memory_function_result(
        in_memory.raw_items(),
        "call-commit-error",
    ));
    assert!(has_in_memory_function_result(
        in_memory.raw_items(),
        "call-after-commit-error",
    ));
}
'''
)
tests.write_text(text, encoding="utf-8")
