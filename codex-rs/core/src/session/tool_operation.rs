use codex_tools::ToolOperationEffect;
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

    pub(crate) async fn has_unreconciled_potential_mutation(&self) -> bool {
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
