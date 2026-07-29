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
    assert!(!receipts.coverage_lost());
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

#[test]
fn overflow_sets_coverage_lost_without_evicting_retained_receipts() {
    let mut receipts = ToolOperationReceipts::default();
    for index in 0..MAX_RETAINED_TOOL_OPERATION_RECEIPTS {
        receipts.start(
            &format!("call-{index}"),
            ToolOperationEffect::PotentialMutation,
        );
    }

    receipts.start("overflow", ToolOperationEffect::PotentialMutation);
    receipts.record_terminal(
        "unknown-after-overflow",
        ToolOperationTerminalState::Completed,
    );

    let snapshot = receipts.snapshot();
    assert_eq!(snapshot.len(), MAX_RETAINED_TOOL_OPERATION_RECEIPTS);
    assert!(!snapshot.contains_key("overflow"));
    assert!(!snapshot.contains_key("unknown-after-overflow"));
    assert!(receipts.coverage_lost());
}
