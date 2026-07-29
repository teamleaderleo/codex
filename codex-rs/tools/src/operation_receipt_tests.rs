use super::ToolOperationEffect;
use super::ToolOperationReceipt;
use super::ToolOperationReceiptError;
use super::ToolOperationTerminalOutcome;

#[test]
fn unclassified_operations_default_to_potential_mutation() {
    assert_eq!(
        ToolOperationEffect::default(),
        ToolOperationEffect::PotentialMutation
    );
}

#[test]
fn receipt_starts_pending_and_without_a_persisted_result() {
    let receipt = ToolOperationReceipt::new(ToolOperationEffect::ReadOnly);

    assert_eq!(receipt.effect(), ToolOperationEffect::ReadOnly);
    assert_eq!(receipt.terminal_outcome(), None);
    assert!(!receipt.result_persisted());
    assert!(!receipt.is_reconciled());
}

#[test]
fn terminal_outcome_does_not_imply_result_persistence() {
    let mut receipt = ToolOperationReceipt::new(ToolOperationEffect::PotentialMutation);

    receipt
        .record_terminal_outcome(ToolOperationTerminalOutcome::Completed { success: true })
        .expect("first terminal outcome should be accepted");

    assert_eq!(
        receipt.terminal_outcome(),
        Some(ToolOperationTerminalOutcome::Completed { success: true })
    );
    assert!(!receipt.result_persisted());
    assert!(!receipt.is_reconciled());
}

#[test]
fn receipt_is_reconciled_after_terminal_outcome_and_result_persistence() {
    let mut receipt = ToolOperationReceipt::new(ToolOperationEffect::PotentialMutation);

    receipt
        .record_terminal_outcome(ToolOperationTerminalOutcome::Aborted)
        .expect("first terminal outcome should be accepted");
    receipt
        .record_result_persisted()
        .expect("first result persistence should be accepted");

    assert!(receipt.is_reconciled());
}

#[test]
fn duplicate_terminal_outcomes_are_rejected() {
    let mut receipt = ToolOperationReceipt::new(ToolOperationEffect::PotentialMutation);
    receipt
        .record_terminal_outcome(ToolOperationTerminalOutcome::Blocked)
        .expect("first terminal outcome should be accepted");

    assert_eq!(
        receipt.record_terminal_outcome(ToolOperationTerminalOutcome::Failed {
            handler_executed: false,
        }),
        Err(ToolOperationReceiptError::TerminalOutcomeAlreadyRecorded)
    );
}

#[test]
fn duplicate_result_persistence_is_rejected() {
    let mut receipt = ToolOperationReceipt::new(ToolOperationEffect::PotentialMutation);
    receipt
        .record_result_persisted()
        .expect("first result persistence should be accepted");

    assert_eq!(
        receipt.record_result_persisted(),
        Err(ToolOperationReceiptError::ResultAlreadyPersisted)
    );
}
