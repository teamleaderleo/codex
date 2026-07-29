use super::TOOL_OPERATION_RECEIPT_VERSION;
use super::ToolOperationEffect;
use super::ToolOperationReceipt;
use super::ToolOperationResultState;
use super::ToolOperationTerminalState;

#[test]
fn potential_mutation_becomes_compaction_ready_after_terminal_result_persistence() {
    let mut receipt = ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation);

    receipt.record_terminal_outcome(ToolOperationTerminalState::Completed);
    receipt.record_result_persisted();

    assert!(receipt.is_compaction_ready());
    assert_eq!(
        receipt,
        ToolOperationReceipt {
            version: TOOL_OPERATION_RECEIPT_VERSION,
            effect: ToolOperationEffect::PotentialMutation,
            terminal_state: ToolOperationTerminalState::Completed,
            result_state: ToolOperationResultState::Persisted,
        }
    );
}

#[test]
fn duplicate_result_blocks_potential_mutation_compaction() {
    let mut receipt = ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation);
    receipt.record_terminal_outcome(ToolOperationTerminalState::Completed);
    receipt.record_result_persisted();

    receipt.record_result_persisted();

    assert!(!receipt.is_compaction_ready());
    assert_eq!(receipt.result_state, ToolOperationResultState::Ambiguous);
}

#[test]
fn conflicting_terminal_outcomes_block_potential_mutation_compaction() {
    let mut receipt = ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation);
    receipt.record_terminal_outcome(ToolOperationTerminalState::Completed);

    receipt.record_terminal_outcome(ToolOperationTerminalState::Aborted);
    receipt.record_result_persisted();

    assert!(!receipt.is_compaction_ready());
    assert_eq!(receipt.terminal_state, ToolOperationTerminalState::Ambiguous);
}

#[test]
fn repeated_terminal_outcome_is_idempotent() {
    let mut receipt = ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation);

    receipt.record_terminal_outcome(ToolOperationTerminalState::Failed);
    receipt.record_terminal_outcome(ToolOperationTerminalState::Failed);
    receipt.record_result_persisted();

    assert!(receipt.is_compaction_ready());
}

#[test]
fn read_only_operation_does_not_require_result_persistence_for_compaction() {
    let receipt = ToolOperationReceipt::pending(ToolOperationEffect::ReadOnly);

    assert!(receipt.is_compaction_ready());
}
