use super::TOOL_OPERATION_RECEIPT_VERSION;
use super::ToolOperationEffect;
use super::ToolOperationReceipt;
use super::ToolOperationResultState;
use super::ToolOperationTerminalState;

#[test]
fn pending_receipt_records_current_version_and_states() {
    let receipt = ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation);

    assert_eq!(
        receipt,
        ToolOperationReceipt {
            version: TOOL_OPERATION_RECEIPT_VERSION,
            effect: ToolOperationEffect::PotentialMutation,
            terminal_state: ToolOperationTerminalState::Pending,
            result_state: ToolOperationResultState::Pending,
        }
    );
}

#[test]
fn duplicate_result_becomes_ambiguous() {
    let mut receipt = ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation);
    receipt.record_terminal_outcome(ToolOperationTerminalState::Completed);
    receipt.record_result_persisted();

    receipt.record_result_persisted();

    assert_eq!(receipt.result_state, ToolOperationResultState::Ambiguous);
}

#[test]
fn conflicting_terminal_outcomes_become_ambiguous() {
    let mut receipt = ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation);
    receipt.record_terminal_outcome(ToolOperationTerminalState::Completed);

    receipt.record_terminal_outcome(ToolOperationTerminalState::Aborted);

    assert_eq!(
        receipt.terminal_state,
        ToolOperationTerminalState::Ambiguous
    );
}

#[test]
fn repeated_terminal_outcome_is_idempotent() {
    let mut receipt = ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation);

    receipt.record_terminal_outcome(ToolOperationTerminalState::Failed);
    receipt.record_terminal_outcome(ToolOperationTerminalState::Failed);

    assert_eq!(receipt.terminal_state, ToolOperationTerminalState::Failed);
}

#[test]
fn future_version_remains_visible_to_domain_validation() {
    let mut receipt = ToolOperationReceipt::pending(ToolOperationEffect::ReadOnly);
    receipt.version = 99;

    assert_eq!(receipt.version, 99);
    assert_ne!(receipt.version, TOOL_OPERATION_RECEIPT_VERSION);
}
