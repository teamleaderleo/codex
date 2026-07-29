use std::error::Error;
use std::fmt;

/// Classifies whether replaying a tool operation can repeat an external effect.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub enum ToolOperationEffect {
    /// The runtime guarantees that repeating the call cannot commit an external mutation.
    ReadOnly,
    /// The runtime may mutate state, or has not supplied a stronger classification.
    #[default]
    PotentialMutation,
}

/// Terminal state reported by the runtime that owned tool execution.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ToolOperationTerminalOutcome {
    Completed { success: bool },
    Failed { handler_executed: bool },
    Blocked,
    Aborted,
}

/// Bounded lifecycle state for one durable tool call.
///
/// The receipt intentionally excludes tool arguments, output bodies, resource names,
/// credentials, and provider payloads. A persistence layer can bind this state to a
/// separate stable or keyed operation identity.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ToolOperationReceipt {
    effect: ToolOperationEffect,
    terminal_outcome: Option<ToolOperationTerminalOutcome>,
    result_persisted: bool,
}

impl ToolOperationReceipt {
    pub fn new(effect: ToolOperationEffect) -> Self {
        Self {
            effect,
            terminal_outcome: None,
            result_persisted: false,
        }
    }

    pub fn effect(self) -> ToolOperationEffect {
        self.effect
    }

    pub fn terminal_outcome(self) -> Option<ToolOperationTerminalOutcome> {
        self.terminal_outcome
    }

    pub fn result_persisted(self) -> bool {
        self.result_persisted
    }

    pub fn record_terminal_outcome(
        &mut self,
        outcome: ToolOperationTerminalOutcome,
    ) -> Result<(), ToolOperationReceiptError> {
        if self.terminal_outcome.is_some() {
            return Err(ToolOperationReceiptError::TerminalOutcomeAlreadyRecorded);
        }
        self.terminal_outcome = Some(outcome);
        Ok(())
    }

    pub fn record_result_persisted(&mut self) -> Result<(), ToolOperationReceiptError> {
        if self.result_persisted {
            return Err(ToolOperationReceiptError::ResultAlreadyPersisted);
        }
        self.result_persisted = true;
        Ok(())
    }

    /// Returns true once execution has a terminal outcome and its result is durable.
    pub fn is_reconciled(self) -> bool {
        self.terminal_outcome.is_some() && self.result_persisted
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ToolOperationReceiptError {
    TerminalOutcomeAlreadyRecorded,
    ResultAlreadyPersisted,
}

impl fmt::Display for ToolOperationReceiptError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::TerminalOutcomeAlreadyRecorded => {
                formatter.write_str("tool operation terminal outcome was already recorded")
            }
            Self::ResultAlreadyPersisted => {
                formatter.write_str("tool operation result was already persisted")
            }
        }
    }
}

impl Error for ToolOperationReceiptError {}

#[cfg(test)]
#[path = "operation_receipt_tests.rs"]
mod tests;
