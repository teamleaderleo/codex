use super::*;
use codex_tools::ToolOperationResultState;

#[test]
fn complete_potential_mutation_receipt_is_retained() {
    let mut receipts = ToolOperationReceipts::default();
    receipts.start("call-1", ToolOperationEffect::PotentialMutation);
    receipts.record_terminal("call-1", ToolOperationTerminalState::Completed);
    receipts.record_result_persisted("call-1");

    assert_eq!(
        receipts.snapshot(),
        BTreeMap::from([(
            "call-1".to_string(),
            ToolOperationReceipt {
                version: 1,
                effect: ToolOperationEffect::PotentialMutation,
                terminal_state: ToolOperationTerminalState::Completed,
                result_state: ToolOperationResultState::Persisted,
            },
        )])
    );
}

#[test]
fn duplicate_start_marks_receipt_ambiguous_and_escalates_effect() {
    let mut receipts = ToolOperationReceipts::default();
    receipts.start("call-1", ToolOperationEffect::ReadOnly);
    receipts.start("call-1", ToolOperationEffect::PotentialMutation);

    assert_eq!(
        receipts.snapshot()["call-1"],
        ToolOperationReceipt {
            version: 1,
            effect: ToolOperationEffect::PotentialMutation,
            terminal_state: ToolOperationTerminalState::Ambiguous,
            result_state: ToolOperationResultState::Ambiguous,
        }
    );
}

#[test]
fn terminal_or_result_without_start_stays_conservative() {
    let mut receipts = ToolOperationReceipts::default();
    receipts.record_terminal("terminal-first", ToolOperationTerminalState::Failed);
    receipts.record_result_persisted("result-first");

    assert_eq!(
        receipts.snapshot(),
        BTreeMap::from([
            (
                "result-first".to_string(),
                ToolOperationReceipt {
                    version: 1,
                    effect: ToolOperationEffect::PotentialMutation,
                    terminal_state: ToolOperationTerminalState::Pending,
                    result_state: ToolOperationResultState::Persisted,
                },
            ),
            (
                "terminal-first".to_string(),
                ToolOperationReceipt {
                    version: 1,
                    effect: ToolOperationEffect::PotentialMutation,
                    terminal_state: ToolOperationTerminalState::Failed,
                    result_state: ToolOperationResultState::Pending,
                },
            ),
        ])
    );
}

#[test]
fn failed_persistence_marks_result_ambiguous() {
    let mut receipts = ToolOperationReceipts::default();
    receipts.start("call-1", ToolOperationEffect::PotentialMutation);
    receipts.record_terminal("call-1", ToolOperationTerminalState::Completed);
    receipts.record_result_ambiguous("call-1");

    assert_eq!(
        receipts.snapshot()["call-1"].result_state,
        ToolOperationResultState::Ambiguous
    );
    assert!(!receipts.snapshot()["call-1"].is_compaction_ready());
}
