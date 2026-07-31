use schemars::JsonSchema;
use serde::Deserialize;
use serde::Serialize;
use ts_rs::TS;

/// Current wire version for durable tool-operation receipt records.
pub const TOOL_OPERATION_RECEIPT_VERSION: u8 = 1;

/// Declares whether one logical tool operation can change state outside the transcript.
#[derive(Clone, Copy, Debug, Default, Deserialize, Eq, JsonSchema, PartialEq, Serialize, TS)]
#[serde(rename_all = "snake_case")]
pub enum ToolOperationEffect {
    ReadOnly,
    #[default]
    PotentialMutation,
}

/// Records the terminal state reported by the selected tool runtime.
#[derive(Clone, Copy, Debug, Default, Deserialize, Eq, JsonSchema, PartialEq, Serialize, TS)]
#[serde(rename_all = "snake_case")]
pub enum ToolOperationTerminalState {
    #[default]
    Pending,
    Completed,
    Failed,
    Aborted,
    Ambiguous,
}

/// Records whether one durable result is known to exist for the operation.
#[derive(Clone, Copy, Debug, Default, Deserialize, Eq, JsonSchema, PartialEq, Serialize, TS)]
#[serde(rename_all = "snake_case")]
pub enum ToolOperationResultState {
    #[default]
    Pending,
    Persisted,
    Ambiguous,
}

/// Privacy-safe state for one logical tool operation.
///
/// This record contains no tool name, arguments, output, credential, resource name, or provider
/// payload. The owning envelope supplies the logical operation identity and receipt epoch.
#[derive(Clone, Copy, Debug, Deserialize, Eq, JsonSchema, PartialEq, Serialize, TS)]
pub struct ToolOperationReceipt {
    pub effect: ToolOperationEffect,
    pub terminal_state: ToolOperationTerminalState,
    pub result_state: ToolOperationResultState,
}

impl ToolOperationReceipt {
    pub fn pending(effect: ToolOperationEffect) -> Self {
        Self {
            effect,
            terminal_state: ToolOperationTerminalState::Pending,
            result_state: ToolOperationResultState::Pending,
        }
    }

    /// Records one terminal runtime outcome.
    ///
    /// Repeating one outcome is idempotent. Conflicting or invalid transitions become ambiguous.
    pub fn record_terminal_outcome(&mut self, outcome: ToolOperationTerminalState) {
        self.terminal_state = match (self.terminal_state, outcome) {
            (
                ToolOperationTerminalState::Pending,
                ToolOperationTerminalState::Completed
                | ToolOperationTerminalState::Failed
                | ToolOperationTerminalState::Aborted,
            ) => outcome,
            (current, repeated) if current == repeated => current,
            _ => ToolOperationTerminalState::Ambiguous,
        };
    }

    /// Records one successful durable result observation.
    ///
    /// A second observation is ambiguous until result identity is reconciled.
    pub fn record_result_persisted(&mut self) {
        self.result_state = match self.result_state {
            ToolOperationResultState::Pending => ToolOperationResultState::Persisted,
            ToolOperationResultState::Persisted | ToolOperationResultState::Ambiguous => {
                ToolOperationResultState::Ambiguous
            }
        };
    }

    pub fn record_result_ambiguous(&mut self) {
        self.result_state = ToolOperationResultState::Ambiguous;
    }
}

/// Stable identity for one logical tool operation.
///
/// Direct calls use the Responses call id. Nested Code Mode calls use the runtime identity scoped
/// to one cell and deliberately exclude Codex's synthetic host call id.
#[derive(Clone, Debug, Deserialize, Eq, Hash, JsonSchema, PartialEq, Serialize, TS)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum ToolOperationId {
    Direct {
        call_id: String,
    },
    CodeMode {
        cell_id: String,
        runtime_tool_call_id: String,
    },
}

impl ToolOperationId {
    pub fn direct(call_id: impl Into<String>) -> Self {
        Self::Direct {
            call_id: call_id.into(),
        }
    }

    pub fn code_mode(cell_id: impl Into<String>, runtime_tool_call_id: impl Into<String>) -> Self {
        Self::CodeMode {
            cell_id: cell_id.into(),
            runtime_tool_call_id: runtime_tool_call_id.into(),
        }
    }
}

/// Starts one durable receipt epoch.
///
/// Replay must reject updates before activation and reset prior live state when a newer epoch is
/// authoritatively installed.
#[derive(Clone, Debug, Deserialize, Eq, JsonSchema, PartialEq, Serialize, TS)]
pub struct ToolOperationReceiptActivation {
    pub version: u8,
    pub epoch_id: String,
}

impl ToolOperationReceiptActivation {
    pub fn v1(epoch_id: impl Into<String>) -> Self {
        Self {
            version: TOOL_OPERATION_RECEIPT_VERSION,
            epoch_id: epoch_id.into(),
        }
    }
}

/// Ordered full-state update for one operation in a receipt epoch.
///
/// `sequence` is epoch-local. Replay may accept an identical duplicate sequence idempotently and
/// must fail closed on gaps, regressions, or conflicting duplicates.
#[derive(Clone, Debug, Deserialize, Eq, JsonSchema, PartialEq, Serialize, TS)]
pub struct ToolOperationReceiptUpdate {
    pub version: u8,
    pub epoch_id: String,
    pub sequence: u64,
    pub operation_id: ToolOperationId,
    pub receipt: ToolOperationReceipt,
}

impl ToolOperationReceiptUpdate {
    pub fn v1(
        epoch_id: impl Into<String>,
        sequence: u64,
        operation_id: ToolOperationId,
        receipt: ToolOperationReceipt,
    ) -> Self {
        Self {
            version: TOOL_OPERATION_RECEIPT_VERSION,
            epoch_id: epoch_id.into(),
            sequence,
            operation_id,
            receipt,
        }
    }
}

/// One operation entry carried by a compacted receipt checkpoint.
#[derive(Clone, Debug, Deserialize, Eq, JsonSchema, PartialEq, Serialize, TS)]
pub struct ToolOperationReceiptCheckpointEntry {
    pub operation_id: ToolOperationId,
    pub receipt: ToolOperationReceipt,
}

/// Bounded receipt state carried across compaction, resume, and fork.
///
/// `next_sequence` is the first sequence number available after checkpoint installation.
/// `coverage_lost` permanently fails closed for potentially mutating continuation.
#[derive(Clone, Debug, Deserialize, Eq, JsonSchema, PartialEq, Serialize, TS)]
pub struct ToolOperationReceiptCheckpoint {
    pub version: u8,
    pub epoch_id: String,
    pub next_sequence: u64,
    pub coverage_lost: bool,
    pub receipts: Vec<ToolOperationReceiptCheckpointEntry>,
}

impl ToolOperationReceiptCheckpoint {
    pub fn v1(
        epoch_id: impl Into<String>,
        next_sequence: u64,
        coverage_lost: bool,
        receipts: Vec<ToolOperationReceiptCheckpointEntry>,
    ) -> Self {
        Self {
            version: TOOL_OPERATION_RECEIPT_VERSION,
            epoch_id: epoch_id.into(),
            next_sequence,
            coverage_lost,
            receipts,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use anyhow::Result;
    use pretty_assertions::assert_eq;
    use serde_json::json;

    #[test]
    fn potential_mutation_records_terminal_and_persisted_result() {
        let mut receipt = ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation);
        assert_eq!(receipt.terminal_state, ToolOperationTerminalState::Pending);
        assert_eq!(receipt.result_state, ToolOperationResultState::Pending);

        receipt.record_terminal_outcome(ToolOperationTerminalState::Completed);
        assert_eq!(
            receipt.terminal_state,
            ToolOperationTerminalState::Completed
        );

        receipt.record_result_persisted();
        assert_eq!(receipt.result_state, ToolOperationResultState::Persisted);
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
    fn wire_dto_preserves_unvalidated_state_for_domain_validation() -> Result<()> {
        let receipt = serde_json::from_value::<ToolOperationReceipt>(json!({
            "effect": "read_only",
            "terminal_state": "pending",
            "result_state": "pending",
        }))?;

        assert_eq!(receipt.effect, ToolOperationEffect::ReadOnly);
        assert_eq!(receipt.terminal_state, ToolOperationTerminalState::Pending);
        assert_eq!(receipt.result_state, ToolOperationResultState::Pending);
        Ok(())
    }

    #[test]
    fn code_mode_identity_excludes_synthetic_host_call_id() -> Result<()> {
        let update = ToolOperationReceiptUpdate::v1(
            "epoch-1",
            7,
            ToolOperationId::code_mode("cell-2", "runtime-9"),
            ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation),
        );

        assert_eq!(
            serde_json::to_value(update)?,
            json!({
                "version": 1,
                "epoch_id": "epoch-1",
                "sequence": 7,
                "operation_id": {
                    "kind": "code_mode",
                    "cell_id": "cell-2",
                    "runtime_tool_call_id": "runtime-9",
                },
                "receipt": {
                    "effect": "potential_mutation",
                    "terminal_state": "pending",
                    "result_state": "pending",
                },
            })
        );
        Ok(())
    }

    #[test]
    fn checkpoint_round_trips_receipt_state() -> Result<()> {
        let checkpoint = ToolOperationReceiptCheckpoint::v1(
            "epoch-4",
            12,
            false,
            vec![ToolOperationReceiptCheckpointEntry {
                operation_id: ToolOperationId::direct("call-3"),
                receipt: ToolOperationReceipt {
                    effect: ToolOperationEffect::PotentialMutation,
                    terminal_state: ToolOperationTerminalState::Completed,
                    result_state: ToolOperationResultState::Persisted,
                },
            }],
        );

        let encoded = serde_json::to_value(&checkpoint)?;
        let decoded = serde_json::from_value::<ToolOperationReceiptCheckpoint>(encoded)?;
        assert_eq!(decoded, checkpoint);
        Ok(())
    }

    #[test]
    fn unknown_version_remains_visible_to_replay_validation() -> Result<()> {
        let activation = serde_json::from_value::<ToolOperationReceiptActivation>(json!({
            "version": 99,
            "epoch_id": "future-epoch",
        }))?;

        assert_eq!(activation.version, 99);
        assert_ne!(activation.version, TOOL_OPERATION_RECEIPT_VERSION);
        Ok(())
    }
}
