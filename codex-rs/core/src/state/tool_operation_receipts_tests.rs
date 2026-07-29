use super::*;
use codex_tools::ToolOperationResultState;

#[test]
fn potential_mutation_reconciles_after_terminal_and_result() {
    let mut receipts = ToolOperationReceipts::default();
    receipts.begin(
        "call-1".to_string(),
        ToolOperationEffect::PotentialMutation,
    );
    assert!(receipts.has_unreconciled_potential_mutation());

    receipts.record_terminal("call-1", ToolOperationTerminalState::Completed);
    assert!(receipts.has_unreconciled_potential_mutation());

    receipts.record_result_persisted("call-1");
    assert!(!receipts.has_unreconciled_potential_mutation());
}

#[test]
fn persistence_before_terminal_reconciles_when_terminal_arrives() {
    let mut receipts = ToolOperationReceipts::default();
    receipts.begin(
        "call-1".to_string(),
        ToolOperationEffect::PotentialMutation,
    );
    receipts.record_result_persisted("call-1");
    assert!(receipts.has_unreconciled_potential_mutation());

    receipts.record_terminal("call-1", ToolOperationTerminalState::Completed);
    assert!(!receipts.has_unreconciled_potential_mutation());
}

#[test]
fn duplicate_persistence_remains_ambiguous() {
    let mut receipts = ToolOperationReceipts::default();
    receipts.begin(
        "call-1".to_string(),
        ToolOperationEffect::PotentialMutation,
    );
    receipts.record_terminal("call-1", ToolOperationTerminalState::Completed);
    receipts.record_result_persisted("call-1");
    receipts.record_result_persisted("call-1");

    let receipt = receipts.receipt("call-1").expect("receipt should exist");
    assert_eq!(receipt.result_state, ToolOperationResultState::Ambiguous);
    assert!(receipts.has_unreconciled_potential_mutation());
}

#[test]
fn conflicting_terminal_outcomes_remain_ambiguous() {
    let mut receipts = ToolOperationReceipts::default();
    receipts.begin(
        "call-1".to_string(),
        ToolOperationEffect::PotentialMutation,
    );
    receipts.record_terminal("call-1", ToolOperationTerminalState::Completed);
    receipts.record_terminal("call-1", ToolOperationTerminalState::Aborted);
    receipts.record_result_persisted("call-1");

    let receipt = receipts.receipt("call-1").expect("receipt should exist");
    assert_eq!(
        receipt.terminal_state,
        ToolOperationTerminalState::Ambiguous
    );
    assert!(receipts.has_unreconciled_potential_mutation());
}

#[test]
fn repeated_begin_escalates_effect_and_marks_identity_ambiguous() {
    let mut receipts = ToolOperationReceipts::default();
    receipts.begin("call-1".to_string(), ToolOperationEffect::ReadOnly);
    receipts.begin(
        "call-1".to_string(),
        ToolOperationEffect::PotentialMutation,
    );

    let receipt = receipts.receipt("call-1").expect("receipt should exist");
    assert_eq!(receipt.effect, ToolOperationEffect::PotentialMutation);
    assert_eq!(
        receipt.terminal_state,
        ToolOperationTerminalState::Ambiguous
    );
    assert_eq!(receipt.result_state, ToolOperationResultState::Ambiguous);
    assert!(receipts.has_unreconciled_potential_mutation());
}

#[test]
fn late_observation_defaults_to_potential_mutation() {
    let mut receipts = ToolOperationReceipts::default();
    receipts.record_terminal("late-call", ToolOperationTerminalState::Completed);

    let receipt = receipts
        .receipt("late-call")
        .expect("late observation should create a conservative receipt");
    assert_eq!(receipt.effect, ToolOperationEffect::PotentialMutation);
    assert!(receipts.has_unreconciled_potential_mutation());
}

#[test]
fn read_only_receipt_does_not_block_mutation_preflight() {
    let mut receipts = ToolOperationReceipts::default();
    receipts.begin("read-1".to_string(), ToolOperationEffect::ReadOnly);
    assert!(!receipts.has_unreconciled_potential_mutation());
}

#[test]
fn explicit_persistence_failure_stays_ambiguous() {
    let mut receipts = ToolOperationReceipts::default();
    receipts.begin(
        "call-1".to_string(),
        ToolOperationEffect::PotentialMutation,
    );
    receipts.record_terminal("call-1", ToolOperationTerminalState::Completed);
    receipts.record_result_ambiguous("call-1");

    let receipt = receipts.receipt("call-1").expect("receipt should exist");
    assert_eq!(receipt.result_state, ToolOperationResultState::Ambiguous);
    assert!(receipts.has_unreconciled_potential_mutation());
}

#[test]
fn overflow_sets_coverage_lost_and_fails_closed_without_eviction() {
    let mut receipts = ToolOperationReceipts::default();
    for index in 0..MAX_RETAINED_TOOL_OPERATION_RECEIPTS {
        receipts.begin(
            format!("call-{index}"),
            ToolOperationEffect::PotentialMutation,
        );
    }

    receipts.begin(
        "overflow".to_string(),
        ToolOperationEffect::PotentialMutation,
    );

    assert!(receipts.coverage_lost());
    assert!(receipts.has_unreconciled_potential_mutation());
    assert!(receipts.receipt("call-0").is_some());
    assert!(receipts.receipt("overflow").is_none());
}
