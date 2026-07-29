use std::collections::HashMap;
use std::collections::hash_map::Entry;

use codex_tools::ToolOperationEffect;
use codex_tools::ToolOperationReceipt;
use codex_tools::ToolOperationTerminalState;

const MAX_RETAINED_TOOL_OPERATION_RECEIPTS: usize = 1024;

/// Session-scoped live owner for privacy-safe tool-operation receipts.
///
/// This owner survives ordinary turn boundaries. Durable rollout restoration and
/// compacted-checkpoint carry-forward are separate stages. The owner is bounded;
/// overflow records permanent coverage loss so compaction can later fail closed.
#[derive(Default)]
pub(crate) struct ToolOperationReceipts {
    receipts: HashMap<String, ToolOperationReceipt>,
    coverage_lost: bool,
}

impl ToolOperationReceipts {
    pub(crate) fn begin(&mut self, call_id: String, effect: ToolOperationEffect) {
        match self.receipts.entry(call_id) {
            Entry::Occupied(mut entry) => {
                let receipt = entry.get_mut();
                receipt.effect = ToolOperationEffect::PotentialMutation;
                receipt.record_terminal_outcome(ToolOperationTerminalState::Ambiguous);
                receipt.record_result_ambiguous();
            }
            Entry::Vacant(entry) => {
                if self.coverage_lost || self.receipts.len() >= MAX_RETAINED_TOOL_OPERATION_RECEIPTS {
                    self.coverage_lost = true;
                    return;
                }
                entry.insert(ToolOperationReceipt::pending(effect));
            }
        }
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

    pub(crate) fn has_unreconciled_potential_mutation(&self) -> bool {
        self.coverage_lost
            || self.receipts.values().any(|receipt| {
                receipt.effect == ToolOperationEffect::PotentialMutation
                    && !receipt.is_compaction_ready()
            })
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

#[cfg(test)]
#[path = "tool_operation_receipts_tests.rs"]
mod tests;
