from pathlib import Path

path = Path("codex-rs/core/src/session/turn_tests.rs")
text = path.read_text(encoding="utf-8")
test_name = "direct_tool_result_persistence_recovers_after_one_shot_append_failure"

if test_name in text:
    raise SystemExit(f"{test_name} already exists")

addition = r'''

#[tokio::test]
async fn direct_tool_result_persistence_recovers_after_one_shot_append_failure() {
    let (session, turn_context, store) = make_session_with_in_memory_persistence().await;

    session
        .begin_tool_operation_receipt(
            "call-first-failure".to_string(),
            ToolOperationEffect::PotentialMutation,
        )
        .await;
    session
        .record_tool_operation_terminal(
            "call-first-failure",
            ToolOperationTerminalState::Completed,
        )
        .await;
    store
        .fail_next_append_for_test("injected one-shot append failure")
        .await;

    record_direct_tool_result(
        &session,
        &turn_context,
        direct_function_result("call-first-failure"),
    )
    .await;

    session
        .begin_tool_operation_receipt(
            "call-after-failure".to_string(),
            ToolOperationEffect::PotentialMutation,
        )
        .await;
    session
        .record_tool_operation_terminal(
            "call-after-failure",
            ToolOperationTerminalState::Completed,
        )
        .await;

    record_direct_tool_result(
        &session,
        &turn_context,
        direct_function_result("call-after-failure"),
    )
    .await;

    let failed_receipt = session
        .tool_operation_receipt("call-first-failure")
        .await
        .expect("failed receipt should exist");
    assert_eq!(
        failed_receipt.result_state,
        ToolOperationResultState::Ambiguous
    );

    let recovered_receipt = session
        .tool_operation_receipt("call-after-failure")
        .await
        .expect("recovered receipt should exist");
    assert_eq!(
        recovered_receipt.result_state,
        ToolOperationResultState::Persisted
    );

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
'''

path.write_text(text + addition, encoding="utf-8")
