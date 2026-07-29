use codex_tools::ToolOperationEffect;
use codex_tools::ToolOperationReceipt;
use codex_tools::ToolOperationTerminalState;

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
}
