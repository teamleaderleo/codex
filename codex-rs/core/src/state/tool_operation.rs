use std::collections::BTreeMap;
use std::collections::btree_map::Entry;

use codex_tools::ToolOperationEffect;
use codex_tools::ToolOperationReceipt;
use codex_tools::ToolOperationTerminalState;

/// Session-scoped owner for privacy-safe direct tool-operation receipts.
///
/// The ledger outlives the originating turn so later manual compaction can inspect
/// unresolved operations. Rollout persistence and nested code-mode ownership remain
/// separate follow-up boundaries.
#[derive(Default)]
pub(crate) struct ToolOperationReceipts {
    receipts: BTreeMap<String, ToolOperationReceipt>,
}

impl ToolOperationReceipts {
    pub(crate) fn start(&mut self, call_id: &str, effect: ToolOperationEffect) {
        match self.receipts.entry(call_id.to_string()) {
            Entry::Vacant(entry) => {
                entry.insert(ToolOperationReceipt::pending(effect));
            }
            Entry::Occupied(mut entry) => {
                let receipt = entry.get_mut();
                if effect == ToolOperationEffect::PotentialMutation {
                    receipt.effect = ToolOperationEffect::PotentialMutation;
                }
                receipt.record_terminal_outcome(ToolOperationTerminalState::Ambiguous);
                receipt.record_result_ambiguous();
            }
        }
    }

    pub(crate) fn record_terminal(
        &mut self,
        call_id: &str,
        terminal_state: ToolOperationTerminalState,
    ) {
        self.receipts
            .entry(call_id.to_string())
            .or_insert_with(|| {
                ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation)
            })
            .record_terminal_outcome(terminal_state);
    }

    pub(crate) fn record_result_persisted(&mut self, call_id: &str) {
        self.receipts
            .entry(call_id.to_string())
            .or_insert_with(|| {
                ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation)
            })
            .record_result_persisted();
    }

    pub(crate) fn record_result_ambiguous(&mut self, call_id: &str) {
        self.receipts
            .entry(call_id.to_string())
            .or_insert_with(|| {
                ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation)
            })
            .record_result_ambiguous();
    }

    pub(crate) fn snapshot(&self) -> BTreeMap<String, ToolOperationReceipt> {
        self.receipts.clone()
    }
}

#[cfg(test)]
#[path = "tool_operation_tests.rs"]
mod tests;
