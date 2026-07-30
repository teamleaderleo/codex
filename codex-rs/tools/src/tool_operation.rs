use serde::Deserialize;
use serde::Serialize;

pub const TOOL_OPERATION_RECEIPT_VERSION: u8 = 2;

/// Declares whether a tool invocation can change state outside the model transcript.
///
/// Unknown runtimes remain conservative by using [`ToolOperationEffect::PotentialMutation`].
#[derive(Clone, Copy, Debug, Default, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ToolOperationEffect {
    ReadOnly,
    #[default]
    PotentialMutation,
}

/// Records the terminal state reported by the tool runtime.
#[derive(Clone, Copy, Debug, Default, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ToolOperationTerminalState {
    #[default]
    Pending,
    NotStarted,
    Completed,
    Failed,
    Aborted,
    Ambiguous,
}

/// Records whether one durable result has been persisted for the invocation.
#[derive(Clone, Copy, Debug, Default, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ToolOperationResultState {
    #[default]
    Pending,
    Persisted,
    Ambiguous,
}

/// Privacy-safe lifecycle state for one tool invocation.
///
/// Call identity remains the responsibility of the owning store. This receipt contains no tool
/// arguments, output body, credentials, resource names, or provider payloads.
#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ToolOperationReceipt {
    pub version: u8,
    pub effect: ToolOperationEffect,
    pub terminal_state: ToolOperationTerminalState,
    pub result_state: ToolOperationResultState,
}

impl ToolOperationReceipt {
    pub fn pending(effect: ToolOperationEffect) -> Self {
        Self {
            version: TOOL_OPERATION_RECEIPT_VERSION,
            effect,
            terminal_state: ToolOperationTerminalState::Pending,
            result_state: ToolOperationResultState::Pending,
        }
    }

    /// Records one terminal runtime outcome.
    ///
    /// Repeating the same outcome is idempotent. Conflicting or invalid transitions become
    /// ambiguous and must be reconciled before potentially mutating history can be compacted.
    pub fn record_terminal_outcome(&mut self, outcome: ToolOperationTerminalState) {
        self.terminal_state = match (self.terminal_state, outcome) {
            (
                ToolOperationTerminalState::Pending,
                ToolOperationTerminalState::NotStarted
                | ToolOperationTerminalState::Completed
                | ToolOperationTerminalState::Failed
                | ToolOperationTerminalState::Aborted,
            ) => outcome,
            (current, repeated) if current == repeated => current,
            _ => ToolOperationTerminalState::Ambiguous,
        };
    }

    /// Records persistence of one result item.
    ///
    /// A second persistence observation is ambiguous until call/result identity is reconciled.
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

    /// Returns whether this receipt alone permits compaction.
    ///
    /// Read-only calls do not require a durable result to protect external state. Potential
    /// mutations require one unambiguous terminal outcome and one persisted result.
    pub fn is_compaction_ready(&self) -> bool {
        match self.effect {
            ToolOperationEffect::ReadOnly => true,
            ToolOperationEffect::PotentialMutation => {
                matches!(
                    self.terminal_state,
                    ToolOperationTerminalState::NotStarted
                        | ToolOperationTerminalState::Completed
                        | ToolOperationTerminalState::Failed
                ) && self.result_state == ToolOperationResultState::Persisted
            }
        }
    }
}

#[cfg(test)]
#[path = "tool_operation_tests.rs"]
mod tests;
