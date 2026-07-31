from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str, label: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    file_path.write_text(text.replace(old, new), encoding="utf-8")


replace_once(
    "codex-rs/core/src/session/mod.rs",
    "mod token_budget;\npub(crate) mod turn;\n",
    "mod token_budget;\nmod tool_operation;\npub(crate) mod turn;\n",
    "session tool operation module",
)

replace_once(
    "codex-rs/core/src/state/mod.rs",
    "mod session;\nmod turn;\n",
    "mod session;\nmod tool_operation_receipts;\nmod turn;\n",
    "state ledger module",
)
replace_once(
    "codex-rs/core/src/state/mod.rs",
    "pub(crate) use session::SessionState;\npub(crate) use turn::ActiveTurn;\n",
    "pub(crate) use session::SessionState;\npub(crate) use tool_operation_receipts::ToolOperationReceiptLedger;\npub(crate) use turn::ActiveTurn;\n",
    "state ledger export",
)

replace_once(
    "codex-rs/core/src/state/session.rs",
    "use super::AdditionalContextStore;\n",
    "use super::AdditionalContextStore;\nuse super::ToolOperationReceiptLedger;\n",
    "session ledger import",
)
replace_once(
    "codex-rs/core/src/state/session.rs",
    "    pub(crate) history: ContextManager,\n",
    "    pub(crate) history: ContextManager,\n    pub(crate) tool_operation_receipts: ToolOperationReceiptLedger,\n",
    "session ledger field",
)
replace_once(
    "codex-rs/core/src/state/session.rs",
    "            history,\n            latest_rate_limits: None,\n",
    "            history,\n            tool_operation_receipts: ToolOperationReceiptLedger::default(),\n            latest_rate_limits: None,\n",
    "session ledger initialization",
)

Path("codex-rs/core/src/session/tool_operation.rs").write_text(
    r'''use codex_protocol::tool_operation::ToolOperationEffect;
use codex_protocol::tool_operation::ToolOperationId;
use codex_protocol::tool_operation::ToolOperationReceipt;
use codex_protocol::tool_operation::ToolOperationTerminalState;

use super::session::Session;

impl Session {
    pub(crate) async fn begin_tool_operation_receipt(
        &self,
        operation_id: ToolOperationId,
        effect: ToolOperationEffect,
    ) {
        self.state
            .lock()
            .await
            .tool_operation_receipts
            .begin(operation_id, effect);
    }

    pub(crate) async fn record_tool_operation_terminal(
        &self,
        operation_id: &ToolOperationId,
        terminal_state: ToolOperationTerminalState,
    ) {
        self.state
            .lock()
            .await
            .tool_operation_receipts
            .record_terminal(operation_id, terminal_state);
    }

    pub(crate) async fn record_tool_operation_result_persisted(
        &self,
        operation_id: &ToolOperationId,
    ) {
        self.state
            .lock()
            .await
            .tool_operation_receipts
            .record_result_persisted(operation_id);
    }

    pub(crate) async fn record_tool_operation_result_ambiguous(
        &self,
        operation_id: &ToolOperationId,
    ) {
        self.state
            .lock()
            .await
            .tool_operation_receipts
            .record_result_ambiguous(operation_id);
    }

    pub(crate) async fn tool_operation_receipt(
        &self,
        operation_id: &ToolOperationId,
    ) -> Option<ToolOperationReceipt> {
        self.state
            .lock()
            .await
            .tool_operation_receipts
            .receipt(operation_id)
    }

    pub(crate) async fn has_unreconciled_potential_mutation(&self) -> bool {
        self.state
            .lock()
            .await
            .tool_operation_receipts
            .has_unreconciled_potential_mutation()
    }

    pub(crate) async fn tool_operation_receipt_coverage_lost(&self) -> bool {
        self.state
            .lock()
            .await
            .tool_operation_receipts
            .coverage_lost()
    }
}
''',
    encoding="utf-8",
)

Path("codex-rs/core/src/state/tool_operation_receipts.rs").write_text(
    r'''use std::collections::HashMap;

use codex_protocol::tool_operation::ToolOperationEffect;
use codex_protocol::tool_operation::ToolOperationId;
use codex_protocol::tool_operation::ToolOperationReceipt;
use codex_protocol::tool_operation::ToolOperationTerminalState;

const MAX_RETAINED_TOOL_OPERATION_RECEIPTS: usize = 1024;
const MAX_TOOL_OPERATION_ID_COMPONENT_BYTES: usize = 512;

/// Bounded session-scoped owner for privacy-safe tool-operation receipts.
///
/// This owner survives ordinary turn boundaries. Durable rollout restoration,
/// compacted checkpoints, dispatch wiring, and retry policy are separate stages.
#[derive(Clone, Debug, Default)]
pub(crate) struct ToolOperationReceiptLedger {
    receipts: HashMap<ToolOperationId, ToolOperationReceipt>,
    coverage_lost: bool,
}

impl ToolOperationReceiptLedger {
    pub(crate) fn begin(
        &mut self,
        operation_id: ToolOperationId,
        effect: ToolOperationEffect,
    ) {
        if !operation_id_is_valid(&operation_id) {
            self.coverage_lost = true;
            return;
        }

        if let Some(receipt) = self.receipts.get_mut(&operation_id) {
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
            .insert(operation_id, ToolOperationReceipt::pending(effect));
    }

    pub(crate) fn record_terminal(
        &mut self,
        operation_id: &ToolOperationId,
        terminal_state: ToolOperationTerminalState,
    ) {
        let Some(receipt) = self.receipt_or_insert_conservative(operation_id) else {
            return;
        };
        receipt.record_terminal_outcome(terminal_state);
    }

    pub(crate) fn record_result_persisted(&mut self, operation_id: &ToolOperationId) {
        let Some(receipt) = self.receipt_or_insert_conservative(operation_id) else {
            return;
        };
        receipt.record_result_persisted();
    }

    pub(crate) fn record_result_ambiguous(&mut self, operation_id: &ToolOperationId) {
        let Some(receipt) = self.receipt_or_insert_conservative(operation_id) else {
            return;
        };
        receipt.record_result_ambiguous();
    }

    pub(crate) fn receipt(
        &self,
        operation_id: &ToolOperationId,
    ) -> Option<ToolOperationReceipt> {
        self.receipts.get(operation_id).copied()
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
        operation_id: &ToolOperationId,
    ) -> Option<&mut ToolOperationReceipt> {
        if !operation_id_is_valid(operation_id) {
            self.coverage_lost = true;
            return None;
        }

        if !self.receipts.contains_key(operation_id) {
            if self.coverage_lost || self.receipts.len() >= MAX_RETAINED_TOOL_OPERATION_RECEIPTS {
                self.coverage_lost = true;
                return None;
            }
            self.receipts.insert(
                operation_id.clone(),
                ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation),
            );
        }
        self.receipts.get_mut(operation_id)
    }
}

fn operation_id_is_valid(operation_id: &ToolOperationId) -> bool {
    fn component_is_valid(value: &str) -> bool {
        !value.is_empty() && value.len() <= MAX_TOOL_OPERATION_ID_COMPONENT_BYTES
    }

    match operation_id {
        ToolOperationId::Direct { call_id } => component_is_valid(call_id),
        ToolOperationId::CodeMode {
            cell_id,
            runtime_tool_call_id,
        } => component_is_valid(cell_id) && component_is_valid(runtime_tool_call_id),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use codex_protocol::tool_operation::ToolOperationResultState;

    #[test]
    fn potential_mutation_reconciles_after_terminal_and_result() {
        let mut ledger = ToolOperationReceiptLedger::default();
        let operation_id = ToolOperationId::direct("call-1");
        ledger.begin(
            operation_id.clone(),
            ToolOperationEffect::PotentialMutation,
        );
        assert!(ledger.has_unreconciled_potential_mutation());

        ledger.record_terminal(&operation_id, ToolOperationTerminalState::Completed);
        assert!(ledger.has_unreconciled_potential_mutation());

        ledger.record_result_persisted(&operation_id);
        assert!(!ledger.has_unreconciled_potential_mutation());
    }

    #[test]
    fn direct_and_code_mode_identities_coexist() {
        let mut ledger = ToolOperationReceiptLedger::default();
        let direct = ToolOperationId::direct("call-1");
        let nested = ToolOperationId::code_mode("cell-1", "runtime-1");
        ledger.begin(direct.clone(), ToolOperationEffect::ReadOnly);
        ledger.begin(nested.clone(), ToolOperationEffect::PotentialMutation);

        assert!(ledger.receipt(&direct).is_some());
        assert!(ledger.receipt(&nested).is_some());
        assert_ne!(direct, nested);
    }

    #[test]
    fn duplicate_persistence_remains_ambiguous() {
        let mut ledger = ToolOperationReceiptLedger::default();
        let operation_id = ToolOperationId::direct("call-1");
        ledger.begin(
            operation_id.clone(),
            ToolOperationEffect::PotentialMutation,
        );
        ledger.record_terminal(&operation_id, ToolOperationTerminalState::Completed);
        ledger.record_result_persisted(&operation_id);
        ledger.record_result_persisted(&operation_id);

        let receipt = ledger
            .receipt(&operation_id)
            .expect("receipt should exist");
        assert_eq!(receipt.result_state, ToolOperationResultState::Ambiguous);
        assert!(ledger.has_unreconciled_potential_mutation());
    }

    #[test]
    fn conflicting_terminal_outcomes_remain_ambiguous() {
        let mut ledger = ToolOperationReceiptLedger::default();
        let operation_id = ToolOperationId::direct("call-1");
        ledger.begin(
            operation_id.clone(),
            ToolOperationEffect::PotentialMutation,
        );
        ledger.record_terminal(&operation_id, ToolOperationTerminalState::Completed);
        ledger.record_terminal(&operation_id, ToolOperationTerminalState::Aborted);
        ledger.record_result_persisted(&operation_id);

        let receipt = ledger
            .receipt(&operation_id)
            .expect("receipt should exist");
        assert_eq!(
            receipt.terminal_state,
            ToolOperationTerminalState::Ambiguous
        );
        assert!(ledger.has_unreconciled_potential_mutation());
    }

    #[test]
    fn repeated_begin_escalates_identity_to_ambiguous_mutation() {
        let mut ledger = ToolOperationReceiptLedger::default();
        let operation_id = ToolOperationId::direct("call-1");
        ledger.begin(operation_id.clone(), ToolOperationEffect::ReadOnly);
        ledger.begin(
            operation_id.clone(),
            ToolOperationEffect::PotentialMutation,
        );

        let receipt = ledger
            .receipt(&operation_id)
            .expect("receipt should exist");
        assert_eq!(receipt.effect, ToolOperationEffect::PotentialMutation);
        assert_eq!(
            receipt.terminal_state,
            ToolOperationTerminalState::Ambiguous
        );
        assert_eq!(receipt.result_state, ToolOperationResultState::Ambiguous);
    }

    #[test]
    fn late_observation_defaults_to_potential_mutation() {
        let mut ledger = ToolOperationReceiptLedger::default();
        let operation_id = ToolOperationId::direct("late-call");
        ledger.record_terminal(&operation_id, ToolOperationTerminalState::Completed);

        let receipt = ledger
            .receipt(&operation_id)
            .expect("late observation should create a receipt");
        assert_eq!(receipt.effect, ToolOperationEffect::PotentialMutation);
        assert!(ledger.has_unreconciled_potential_mutation());
    }

    #[test]
    fn read_only_receipt_does_not_block_mutation_preflight() {
        let mut ledger = ToolOperationReceiptLedger::default();
        ledger.begin(
            ToolOperationId::direct("read-1"),
            ToolOperationEffect::ReadOnly,
        );
        assert!(!ledger.has_unreconciled_potential_mutation());
    }

    #[test]
    fn overflow_sets_coverage_lost_without_eviction() {
        let mut ledger = ToolOperationReceiptLedger::default();
        for index in 0..MAX_RETAINED_TOOL_OPERATION_RECEIPTS {
            ledger.begin(
                ToolOperationId::direct(format!("call-{index}")),
                ToolOperationEffect::PotentialMutation,
            );
        }

        let first = ToolOperationId::direct("call-0");
        let overflow = ToolOperationId::direct("overflow");
        ledger.begin(overflow.clone(), ToolOperationEffect::PotentialMutation);

        assert!(ledger.coverage_lost());
        assert!(ledger.has_unreconciled_potential_mutation());
        assert!(ledger.receipt(&first).is_some());
        assert!(ledger.receipt(&overflow).is_none());
    }

    #[test]
    fn invalid_identity_sets_coverage_lost() {
        let mut ledger = ToolOperationReceiptLedger::default();
        ledger.begin(
            ToolOperationId::code_mode("", "runtime-1"),
            ToolOperationEffect::PotentialMutation,
        );

        assert!(ledger.coverage_lost());
        assert!(ledger.has_unreconciled_potential_mutation());
    }
}
''',
    encoding="utf-8",
)
