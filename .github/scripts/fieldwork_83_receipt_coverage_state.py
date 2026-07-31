from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one anchor in {path}, found {count}")
    file_path.write_text(text.replace(old, new, 1), encoding="utf-8")


Path("codex-rs/core/src/state/tool_operation_receipts.rs").write_text(
    '''use std::collections::HashMap;

use codex_tools::TOOL_OPERATION_RECEIPT_VERSION;
use codex_tools::ToolOperationEffect;
use codex_tools::ToolOperationReceipt;
use codex_tools::ToolOperationResultState;
use codex_tools::ToolOperationTerminalState;

const MAX_RETAINED_TOOL_OPERATION_RECEIPTS: usize = 1024;

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
enum ToolOperationReceiptCoverage {
    #[default]
    Unknown,
    Complete,
}

/// Session-scoped live owner for privacy-safe tool-operation receipts.
///
/// This owner survives ordinary turn boundaries. Durable rollout restoration and
/// compacted-checkpoint carry-forward are separate stages. Coverage begins unknown
/// and is marked complete only for a confirmed fresh empty history. The owner is
/// bounded; overflow records permanent coverage loss so later decisions fail closed.
#[derive(Default)]
pub(crate) struct ToolOperationReceipts {
    pub(super) receipts: HashMap<String, ToolOperationReceipt>,
    coverage: ToolOperationReceiptCoverage,
    coverage_lost: bool,
}

impl ToolOperationReceipts {
    pub(crate) fn establish_fresh_history_coverage(&mut self) {
        if self.receipts.is_empty() && !self.coverage_lost {
            self.coverage = ToolOperationReceiptCoverage::Complete;
        }
    }

    pub(crate) fn begin(&mut self, call_id: String, effect: ToolOperationEffect) {
        if let Some(receipt) = self.receipts.get_mut(&call_id) {
            receipt.effect = ToolOperationEffect::PotentialMutation;
            receipt.record_terminal_outcome(ToolOperationTerminalState::Ambiguous);
            receipt.record_result_ambiguous();
            return;
        }

        if self.coverage_lost || self.receipts.len() >= MAX_RETAINED_TOOL_OPERATION_RECEIPTS {
            self.coverage_lost = true;
            return;
        }

        self.receipts
            .insert(call_id, ToolOperationReceipt::pending(effect));
    }

    pub(crate) fn record_terminal(
        &mut self,
        call_id: &str,
        terminal_state: ToolOperationTerminalState,
    ) {
        let Some(receipt) = self.receipt_or_insert_conservative(call_id) else {
            return;
        };
        receipt.record_terminal_outcome(terminal_state);
    }

    pub(crate) fn record_result_persisted(&mut self, call_id: &str) {
        let Some(receipt) = self.receipt_or_insert_conservative(call_id) else {
            return;
        };
        receipt.record_result_persisted();
    }

    pub(crate) fn record_result_ambiguous(&mut self, call_id: &str) {
        let Some(receipt) = self.receipt_or_insert_conservative(call_id) else {
            return;
        };
        receipt.record_result_ambiguous();
    }

    pub(crate) fn receipt(&self, call_id: &str) -> Option<ToolOperationReceipt> {
        self.receipts.get(call_id).copied()
    }

    pub(crate) fn has_unresolved_state(&self) -> bool {
        self.coverage != ToolOperationReceiptCoverage::Complete
            || self.coverage_lost
            || self.receipts.values().any(|receipt| {
                receipt.version != TOOL_OPERATION_RECEIPT_VERSION
                    || (receipt.effect == ToolOperationEffect::PotentialMutation
                        && !potential_mutation_is_reconciled(receipt))
            })
    }

    pub(crate) fn coverage_is_complete(&self) -> bool {
        self.coverage == ToolOperationReceiptCoverage::Complete && !self.coverage_lost
    }

    pub(crate) fn coverage_lost(&self) -> bool {
        self.coverage_lost
    }

    fn receipt_or_insert_conservative(
        &mut self,
        call_id: &str,
    ) -> Option<&mut ToolOperationReceipt> {
        if !self.receipts.contains_key(call_id) {
            if self.coverage_lost || self.receipts.len() >= MAX_RETAINED_TOOL_OPERATION_RECEIPTS {
                self.coverage_lost = true;
                return None;
            }
            self.receipts.insert(
                call_id.to_string(),
                ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation),
            );
        }
        self.receipts.get_mut(call_id)
    }
}

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
    encoding="utf-8",
)

Path("codex-rs/core/src/state/tool_operation_receipts_tests.rs").write_text(
    '''use super::*;
use codex_tools::ToolOperationResultState;

fn fresh_receipts() -> ToolOperationReceipts {
    let mut receipts = ToolOperationReceipts::default();
    receipts.establish_fresh_history_coverage();
    receipts
}

#[test]
fn unknown_coverage_fails_closed() {
    let receipts = ToolOperationReceipts::default();

    assert!(!receipts.coverage_is_complete());
    assert!(receipts.has_unresolved_state());
}

#[test]
fn fresh_empty_history_establishes_complete_coverage() {
    let receipts = fresh_receipts();

    assert!(receipts.coverage_is_complete());
    assert!(!receipts.has_unresolved_state());
}

#[test]
fn fresh_coverage_cannot_be_claimed_after_an_observation() {
    let mut receipts = ToolOperationReceipts::default();
    receipts.begin("call-before-coverage".to_string(), ToolOperationEffect::ReadOnly);

    receipts.establish_fresh_history_coverage();

    assert!(!receipts.coverage_is_complete());
    assert!(receipts.has_unresolved_state());
}

#[test]
fn potential_mutation_reconciles_after_terminal_and_result() {
    let mut receipts = fresh_receipts();
    receipts.begin("call-1".to_string(), ToolOperationEffect::PotentialMutation);
    assert!(receipts.has_unresolved_state());

    receipts.record_terminal("call-1", ToolOperationTerminalState::Completed);
    assert!(receipts.has_unresolved_state());

    receipts.record_result_persisted("call-1");
    assert!(!receipts.has_unresolved_state());
}

#[test]
fn persistence_before_terminal_reconciles_when_terminal_arrives() {
    let mut receipts = fresh_receipts();
    receipts.begin("call-1".to_string(), ToolOperationEffect::PotentialMutation);
    receipts.record_result_persisted("call-1");
    assert!(receipts.has_unresolved_state());

    receipts.record_terminal("call-1", ToolOperationTerminalState::Completed);
    assert!(!receipts.has_unresolved_state());
}

#[test]
fn duplicate_persistence_remains_ambiguous() {
    let mut receipts = fresh_receipts();
    receipts.begin("call-1".to_string(), ToolOperationEffect::PotentialMutation);
    receipts.record_terminal("call-1", ToolOperationTerminalState::Completed);
    receipts.record_result_persisted("call-1");
    receipts.record_result_persisted("call-1");

    let receipt = receipts.receipt("call-1").expect("receipt should exist");
    assert_eq!(receipt.result_state, ToolOperationResultState::Ambiguous);
    assert!(receipts.has_unresolved_state());
}

#[test]
fn conflicting_terminal_outcomes_remain_ambiguous() {
    let mut receipts = fresh_receipts();
    receipts.begin("call-1".to_string(), ToolOperationEffect::PotentialMutation);
    receipts.record_terminal("call-1", ToolOperationTerminalState::Completed);
    receipts.record_terminal("call-1", ToolOperationTerminalState::Aborted);
    receipts.record_result_persisted("call-1");

    let receipt = receipts.receipt("call-1").expect("receipt should exist");
    assert_eq!(
        receipt.terminal_state,
        ToolOperationTerminalState::Ambiguous
    );
    assert!(receipts.has_unresolved_state());
}

#[test]
fn repeated_begin_escalates_effect_and_marks_identity_ambiguous() {
    let mut receipts = fresh_receipts();
    receipts.begin("call-1".to_string(), ToolOperationEffect::ReadOnly);
    receipts.begin("call-1".to_string(), ToolOperationEffect::PotentialMutation);

    let receipt = receipts.receipt("call-1").expect("receipt should exist");
    assert_eq!(receipt.effect, ToolOperationEffect::PotentialMutation);
    assert_eq!(
        receipt.terminal_state,
        ToolOperationTerminalState::Ambiguous
    );
    assert_eq!(receipt.result_state, ToolOperationResultState::Ambiguous);
    assert!(receipts.has_unresolved_state());
}

#[test]
fn late_observation_defaults_to_potential_mutation() {
    let mut receipts = fresh_receipts();
    receipts.record_terminal("late-call", ToolOperationTerminalState::Completed);

    let receipt = receipts
        .receipt("late-call")
        .expect("late observation should create a conservative receipt");
    assert_eq!(receipt.effect, ToolOperationEffect::PotentialMutation);
    assert!(receipts.has_unresolved_state());
}

#[test]
fn read_only_receipt_does_not_block_complete_coverage() {
    let mut receipts = fresh_receipts();
    receipts.begin("read-1".to_string(), ToolOperationEffect::ReadOnly);
    assert!(!receipts.has_unresolved_state());
}

#[test]
fn explicit_persistence_failure_stays_ambiguous() {
    let mut receipts = fresh_receipts();
    receipts.begin("call-1".to_string(), ToolOperationEffect::PotentialMutation);
    receipts.record_terminal("call-1", ToolOperationTerminalState::Completed);
    receipts.record_result_ambiguous("call-1");

    let receipt = receipts.receipt("call-1").expect("receipt should exist");
    assert_eq!(receipt.result_state, ToolOperationResultState::Ambiguous);
    assert!(receipts.has_unresolved_state());
}

#[test]
fn overflow_sets_coverage_lost_and_fails_closed_without_eviction() {
    let mut receipts = fresh_receipts();
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
    assert!(!receipts.coverage_is_complete());
    assert!(receipts.has_unresolved_state());
    assert!(receipts.receipt("call-0").is_some());
    assert!(receipts.receipt("overflow").is_none());
}

#[test]
fn future_receipt_version_fails_closed() {
    let mut receipts = fresh_receipts();
    receipts.begin("call-future".to_string(), ToolOperationEffect::ReadOnly);
    receipts
        .receipts
        .get_mut("call-future")
        .expect("receipt should exist")
        .version = 99;

    assert!(receipts.has_unresolved_state());
}
''',
    encoding="utf-8",
)

replace_once(
    "codex-rs/core/src/state/session.rs",
    '''    pub(crate) fn new(session_configuration: SessionConfiguration) -> Self {
        Self::new_with_auto_compact_window_ids(
            session_configuration,
            AutoCompactWindowIds::new_initial(),
        )
    }
''',
    '''    pub(crate) fn new(session_configuration: SessionConfiguration) -> Self {
        let mut state = Self::new_with_auto_compact_window_ids(
            session_configuration,
            AutoCompactWindowIds::new_initial(),
        );
        state
            .tool_operation_receipts
            .establish_fresh_history_coverage();
        state
    }
''',
)

replace_once(
    "codex-rs/core/src/session/mod.rs",
    '''        let has_prior_user_turns = initial_history_has_prior_user_turns(&conversation_history);
        {
            let mut state = self.state.lock().await;
            state.set_next_turn_is_first(!has_prior_user_turns);
        }
        match conversation_history {
''',
    '''        let has_prior_user_turns = initial_history_has_prior_user_turns(&conversation_history);
        {
            let mut state = self.state.lock().await;
            state.set_next_turn_is_first(!has_prior_user_turns);
            if matches!(
                &conversation_history,
                InitialHistory::New | InitialHistory::Cleared
            ) {
                state
                    .tool_operation_receipts
                    .establish_fresh_history_coverage();
            }
        }
        match conversation_history {
''',
)

Path("codex-rs/core/src/session/tool_operation.rs").write_text(
    '''use codex_tools::ToolOperationEffect;
use codex_tools::ToolOperationReceipt;
use codex_tools::ToolOperationTerminalState;

use crate::context_manager::validate_compaction_call_output_identity;
use crate::state::SessionState;
use codex_protocol::error::CodexErrorDetails;
use codex_protocol::error::Result as CodexResult;

use super::session::Session;

impl Session {
    pub(crate) async fn begin_tool_operation_receipt(
        &self,
        call_id: String,
        effect: ToolOperationEffect,
    ) {
        self.state
            .lock()
            .await
            .tool_operation_receipts
            .begin(call_id, effect);
    }

    pub(crate) async fn record_tool_operation_terminal(
        &self,
        call_id: &str,
        terminal_state: ToolOperationTerminalState,
    ) {
        self.state
            .lock()
            .await
            .tool_operation_receipts
            .record_terminal(call_id, terminal_state);
    }

    pub(crate) async fn record_tool_operation_result_persisted(&self, call_id: &str) {
        self.state
            .lock()
            .await
            .tool_operation_receipts
            .record_result_persisted(call_id);
    }

    pub(crate) async fn record_tool_operation_result_ambiguous(&self, call_id: &str) {
        self.state
            .lock()
            .await
            .tool_operation_receipts
            .record_result_ambiguous(call_id);
    }

    pub(crate) async fn tool_operation_receipt(
        &self,
        call_id: &str,
    ) -> Option<ToolOperationReceipt> {
        self.state
            .lock()
            .await
            .tool_operation_receipts
            .receipt(call_id)
    }

    pub(crate) async fn has_unresolved_tool_operation_state(&self) -> bool {
        self.state
            .lock()
            .await
            .tool_operation_receipts
            .has_unresolved_state()
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
    if state.tool_operation_receipts.has_unresolved_state() {
        return Err(CodexErrorDetails::InvalidRequest(
            "compaction paused because tool operation receipt coverage or state is unresolved"
                .to_string(),
        )
        .into());
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn compaction_precondition_accepts_fresh_empty_receipt_state() {
        let (session, _) = crate::session::tests::make_session_and_context().await;

        session
            .validate_compaction_tool_operation_state()
            .await
            .expect("fresh empty state should be accepted");
    }

    #[tokio::test]
    async fn compaction_precondition_rejects_valid_history_without_receipt_coverage() {
        let (session, _) = crate::session::tests::make_session_and_context().await;
        let call_id = "call-resumed-without-receipt";
        {
            let mut state = session.state.lock().await;
            state.tool_operation_receipts = Default::default();
            state.replace_history(
                vec![
                    codex_protocol::models::ResponseItem::FunctionCall {
                        id: None,
                        name: "set_marker".to_string(),
                        namespace: None,
                        arguments: "{}".to_string(),
                        call_id: call_id.to_string(),
                        internal_chat_message_metadata_passthrough: None,
                    },
                    codex_protocol::models::ResponseItem::FunctionCallOutput {
                        id: None,
                        call_id: call_id.to_string(),
                        output: codex_protocol::models::FunctionCallOutputPayload::from_text(
                            "ok".to_string(),
                        ),
                        internal_chat_message_metadata_passthrough: None,
                    },
                ],
                None,
            );
        }

        assert!(session.tool_operation_receipt(call_id).await.is_none());
        let error = session
            .validate_compaction_tool_operation_state()
            .await
            .expect_err("missing receipt coverage should block compaction");

        assert!(error.to_string().contains("coverage or state"));
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

        assert!(error.to_string().contains("coverage or state"));
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
            .record_tool_operation_terminal("call-complete", ToolOperationTerminalState::Completed)
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
    encoding="utf-8",
)

expected = {
    "codex-rs/core/src/session/mod.rs",
    "codex-rs/core/src/session/tool_operation.rs",
    "codex-rs/core/src/state/session.rs",
    "codex-rs/core/src/state/tool_operation_receipts.rs",
    "codex-rs/core/src/state/tool_operation_receipts_tests.rs",
}
print("FIELDWORK_EXPECTED_FILES=" + ",".join(sorted(expected)))
