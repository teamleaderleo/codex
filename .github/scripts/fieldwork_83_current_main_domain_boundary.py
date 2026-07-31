from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one anchor in {path}, found {count}")
    file_path.write_text(text.replace(old, new, 1))


replace_once(
    "codex-rs/tools/src/tool_operation.rs",
    '''    /// Returns whether this receipt alone permits compaction.
    ///
    /// Read-only calls do not require a durable result to protect external state. Potential
    /// mutations require one unambiguous terminal outcome and one persisted result.
    pub fn is_compaction_ready(&self) -> bool {
        match self.effect {
            ToolOperationEffect::ReadOnly => true,
            ToolOperationEffect::PotentialMutation => {
                matches!(
                    self.terminal_state,
                    ToolOperationTerminalState::Completed
                        | ToolOperationTerminalState::Failed
                        | ToolOperationTerminalState::Aborted
                ) && self.result_state == ToolOperationResultState::Persisted
            }
        }
    }
''',
    "",
)

Path("codex-rs/tools/src/tool_operation_tests.rs").write_text(
    '''use super::TOOL_OPERATION_RECEIPT_VERSION;
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
'''
)

replace_once(
    "codex-rs/core/src/state/tool_operation_receipts.rs",
    '''use codex_tools::ToolOperationEffect;
use codex_tools::ToolOperationReceipt;
use codex_tools::ToolOperationTerminalState;
''',
    '''use codex_tools::TOOL_OPERATION_RECEIPT_VERSION;
use codex_tools::ToolOperationEffect;
use codex_tools::ToolOperationReceipt;
use codex_tools::ToolOperationResultState;
use codex_tools::ToolOperationTerminalState;
''',
)

replace_once(
    "codex-rs/core/src/state/tool_operation_receipts.rs",
    '''    pub(crate) fn has_unreconciled_potential_mutation(&self) -> bool {
        self.coverage_lost
            || self.receipts.values().any(|receipt| {
                receipt.effect == ToolOperationEffect::PotentialMutation
                    && !receipt.is_compaction_ready()
            })
    }
''',
    '''    pub(crate) fn has_unreconciled_potential_mutation(&self) -> bool {
        self.coverage_lost
            || self.receipts.values().any(|receipt| {
                receipt.version != TOOL_OPERATION_RECEIPT_VERSION
                    || (receipt.effect == ToolOperationEffect::PotentialMutation
                        && !potential_mutation_is_reconciled(receipt))
            })
    }
''',
)

replace_once(
    "codex-rs/core/src/state/tool_operation_receipts.rs",
    '''}

#[cfg(test)]
#[path = "tool_operation_receipts_tests.rs"]
mod tests;
''',
    '''}

fn potential_mutation_is_reconciled(receipt: &ToolOperationReceipt) -> bool {
    receipt.version == TOOL_OPERATION_RECEIPT_VERSION
        && matches!(
            receipt.terminal_state,
            ToolOperationTerminalState::Completed
                | ToolOperationTerminalState::Failed
                | ToolOperationTerminalState::Aborted
        )
        && receipt.result_state == ToolOperationResultState::Persisted
}

#[cfg(test)]
#[path = "tool_operation_receipts_tests.rs"]
mod tests;
''',
)

state_tests = Path("codex-rs/core/src/state/tool_operation_receipts_tests.rs")
state_tests.write_text(
    state_tests.read_text()
    + '''

#[test]
fn future_receipt_version_fails_closed() {
    let mut receipts = ToolOperationReceipts::default();
    receipts.begin("call-future".to_string(), ToolOperationEffect::ReadOnly);
    receipts
        .receipts
        .get_mut("call-future")
        .expect("receipt should exist")
        .version = 99;

    assert!(receipts.has_unreconciled_potential_mutation());
}
'''
)

replace_once(
    "codex-rs/core/src/session/tool_operation.rs",
    '''use codex_tools::ToolOperationEffect;
use codex_tools::ToolOperationReceipt;
use codex_tools::ToolOperationTerminalState;

use super::session::Session;
''',
    '''use codex_tools::ToolOperationEffect;
use codex_tools::ToolOperationReceipt;
use codex_tools::ToolOperationTerminalState;

use crate::context_manager::validate_compaction_call_output_identity;
use crate::state::SessionState;
use codex_protocol::error::CodexErrorDetails;
use codex_protocol::error::Result as CodexResult;

use super::session::Session;
''',
)

replace_once(
    "codex-rs/core/src/session/tool_operation.rs",
    '''    pub(crate) async fn has_unreconciled_potential_mutation(&self) -> bool {
        self.state
            .lock()
            .await
            .tool_operation_receipts
            .has_unreconciled_potential_mutation()
    }
}
''',
    '''    pub(crate) async fn has_unreconciled_potential_mutation(&self) -> bool {
        self.state
            .lock()
            .await
            .tool_operation_receipts
            .has_unreconciled_potential_mutation()
    }

    pub(crate) async fn validate_compaction_tool_operation_state(&self) -> CodexResult<()> {
        let state = self.state.lock().await;
        validate_compaction_tool_operation_state_locked(&state)
    }
}

pub(crate) fn validate_compaction_tool_operation_state_locked(
    state: &SessionState,
) -> CodexResult<()> {
    validate_compaction_call_output_identity(state.history.raw_items())?;
    if state
        .tool_operation_receipts
        .has_unreconciled_potential_mutation()
    {
        return Err(CodexErrorDetails::InvalidRequest(
            "compaction paused because tool operation receipt state is unresolved".to_string(),
        )
        .into());
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn compaction_precondition_accepts_empty_receipt_state() {
        let (session, _) = crate::session::tests::make_session_and_context().await;

        session
            .validate_compaction_tool_operation_state()
            .await
            .expect("empty state should be accepted");
    }

    #[tokio::test]
    async fn compaction_precondition_rejects_unreconciled_potential_mutation() {
        let (session, _) = crate::session::tests::make_session_and_context().await;
        session
            .begin_tool_operation_receipt(
                "call-pending".to_string(),
                ToolOperationEffect::PotentialMutation,
            )
            .await;

        let error = session
            .validate_compaction_tool_operation_state()
            .await
            .expect_err("pending mutation should block compaction");

        assert!(error.to_string().contains("receipt state"));
    }

    #[tokio::test]
    async fn compaction_precondition_accepts_reconciled_potential_mutation() {
        let (session, _) = crate::session::tests::make_session_and_context().await;
        session
            .begin_tool_operation_receipt(
                "call-complete".to_string(),
                ToolOperationEffect::PotentialMutation,
            )
            .await;
        session
            .record_tool_operation_terminal(
                "call-complete",
                ToolOperationTerminalState::Completed,
            )
            .await;
        session
            .record_tool_operation_result_persisted("call-complete")
            .await;

        session
            .validate_compaction_tool_operation_state()
            .await
            .expect("reconciled mutation should be accepted");
    }
}
''',
)

expected = {
    "codex-rs/tools/src/tool_operation.rs",
    "codex-rs/tools/src/tool_operation_tests.rs",
    "codex-rs/core/src/state/tool_operation_receipts.rs",
    "codex-rs/core/src/state/tool_operation_receipts_tests.rs",
    "codex-rs/core/src/session/tool_operation.rs",
}
print("FIELDWORK_EXPECTED_FILES=" + ",".join(sorted(expected)))
