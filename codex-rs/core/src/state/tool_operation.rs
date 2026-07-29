use std::collections::BTreeMap;

use codex_tools::ToolOperationEffect;
use codex_tools::ToolOperationReceipt;
use codex_tools::ToolOperationTerminalState;

const MAX_RETAINED_TOOL_OPERATION_RECEIPTS: usize = 1024;

/// Session-scoped owner for privacy-safe direct tool-operation receipts.
///
/// The ledger outlives the originating turn so later manual compaction can inspect
/// unresolved operations. Rollout persistence and nested code-mode ownership remain
/// separate follow-up boundaries.
///
/// The owner is deliberately bounded. If the bound is exceeded, `coverage_lost`
/// remains set so later compaction preflight can fail closed rather than assume the
/// retained map is complete.
pub(crate) struct ToolOperationReceipts {
    receipts: BTreeMap<String, ToolOperationReceipt>,
    coverage_lost: bool,
}

impl Default for ToolOperationReceipts {
    fn default() -> Self {
        Self {
            receipts: BTreeMap::new(),
            coverage_lost: false,
        }
    }
}

impl ToolOperationReceipts {
    pub(crate) fn start(&mut self, call_id: &str, effect: ToolOperationEffect) {
        if let Some(receipt) = self.receipts.get_mut(call_id) {
            if effect == ToolOperationEffect::PotentialMutation {
                receipt.effect = ToolOperationEffect::PotentialMutation;
            }
            receipt.record_terminal_outcome(ToolOperationTerminalState::Ambiguous);
            receipt.record_result_ambiguous();
            return;
        }

        if self.receipts.len() >= MAX_RETAINED_TOOL_OPERATION_RECEIPTS {
            self.coverage_lost = true;
            return;
        }

        self.receipts
            .insert(call_id.to_string(), ToolOperationReceipt::pending(effect));
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

    pub(crate) fn snapshot(&self) -> BTreeMap<String, ToolOperationReceipt> {
        self.receipts.clone()
    }

    pub(crate) fn coverage_lost(&self) -> bool {
        self.coverage_lost
    }

    fn receipt_or_insert_conservative(
        &mut self,
        call_id: &str,
    ) -> Option<&mut ToolOperationReceipt> {
        if !self.receipts.contains_key(call_id) {
            if self.receipts.len() >= MAX_RETAINED_TOOL_OPERATION_RECEIPTS {
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

#[cfg(test)]
#[path = "tool_operation_tests.rs"]
mod tests;
