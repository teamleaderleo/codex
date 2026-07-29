use super::TurnState;
use codex_tools::ToolOperationEffect;
use codex_tools::ToolOperationResultState;
use codex_tools::ToolOperationTerminalState;

#[test]
fn potential_mutation_is_unreconciled_until_terminal_and_result_are_recorded() {
    let mut state = TurnState::default();
    state.begin_tool_operation(
        "call-1".to_string(),
        ToolOperationEffect::PotentialMutation,
    );

    assert!(state.has_unreconciled_potential_mutation());

    state.record_tool_operation_terminal("call-1", ToolOperationTerminalState::Completed);
    assert!(state.has_unreconciled_potential_mutation());

    state.record_tool_operation_result_persisted("call-1");
    assert!(!state.has_unreconciled_potential_mutation());
}

#[test]
fn persistence_before_terminal_reconciles_after_terminal_arrives() {
    let mut state = TurnState::default();
    state.begin_tool_operation(
        "call-1".to_string(),
        ToolOperationEffect::PotentialMutation,
    );

    state.record_tool_operation_result_persisted("call-1");
    assert!(state.has_unreconciled_potential_mutation());

    state.record_tool_operation_terminal("call-1", ToolOperationTerminalState::Completed);
    assert!(!state.has_unreconciled_potential_mutation());
}

#[test]
fn duplicate_result_persistence_is_ambiguous_and_blocks_compaction() {
    let mut state = TurnState::default();
    state.begin_tool_operation(
        "call-1".to_string(),
        ToolOperationEffect::PotentialMutation,
    );
    state.record_tool_operation_terminal("call-1", ToolOperationTerminalState::Completed);
    state.record_tool_operation_result_persisted("call-1");
    state.record_tool_operation_result_persisted("call-1");

    let receipt = state
        .tool_operation_receipt("call-1")
        .expect("receipt should exist");
    assert_eq!(receipt.result_state, ToolOperationResultState::Ambiguous);
    assert!(state.has_unreconciled_potential_mutation());
}

#[test]
fn conflicting_terminal_outcomes_are_ambiguous() {
    let mut state = TurnState::default();
    state.begin_tool_operation(
        "call-1".to_string(),
        ToolOperationEffect::PotentialMutation,
    );
    state.record_tool_operation_terminal("call-1", ToolOperationTerminalState::Completed);
    state.record_tool_operation_terminal("call-1", ToolOperationTerminalState::Aborted);
    state.record_tool_operation_result_persisted("call-1");

    let receipt = state
        .tool_operation_receipt("call-1")
        .expect("receipt should exist");
    assert_eq!(
        receipt.terminal_state,
        ToolOperationTerminalState::Ambiguous
    );
    assert!(state.has_unreconciled_potential_mutation());
}

#[test]
fn repeated_begin_marks_call_identity_ambiguous() {
    let mut state = TurnState::default();
    state.begin_tool_operation(
        "call-1".to_string(),
        ToolOperationEffect::PotentialMutation,
    );
    state.begin_tool_operation(
        "call-1".to_string(),
        ToolOperationEffect::PotentialMutation,
    );

    let receipt = state
        .tool_operation_receipt("call-1")
        .expect("receipt should exist");
    assert_eq!(receipt.result_state, ToolOperationResultState::Ambiguous);
    assert!(state.has_unreconciled_potential_mutation());
}

#[test]
fn missing_begin_defaults_to_potential_mutation() {
    let mut state = TurnState::default();
    state.record_tool_operation_terminal("late-call", ToolOperationTerminalState::Completed);

    let receipt = state
        .tool_operation_receipt("late-call")
        .expect("receipt should be created conservatively");
    assert_eq!(receipt.effect, ToolOperationEffect::PotentialMutation);
    assert!(state.has_unreconciled_potential_mutation());
}
