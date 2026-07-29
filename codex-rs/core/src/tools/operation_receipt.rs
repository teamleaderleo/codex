//! Privacy-safe operation state used to decide whether compaction may replace raw
//! tool call/result identity.
//!
//! This first-stage contract deliberately carries no tool name, arguments,
//! provider payload, or raw call identifier. A later integration can associate
//! the receipt with an existing durable operation owner.

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum OperationEffect {
    ReadOnly,
    PotentialMutation,
}

impl OperationEffect {
    /// Unknown client-executed runtimes are treated conservatively because a
    /// missing annotation must never authorize an automatic mutation replay.
    pub(crate) fn from_read_only_hint(read_only: Option<bool>) -> Self {
        match read_only {
            Some(true) => Self::ReadOnly,
            Some(false) | None => Self::PotentialMutation,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum HandlerTerminalState {
    ReturnedResult,
    FailedBeforeResult,
}

#[allow(dead_code)] // Wired into history validation in the next source stage.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum OperationIdentityState {
    PendingResult,
    Complete,
    MissingResult,
    DuplicateResult,
    ReorderedResult,
    LateResultPendingReconciliation,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum CompactionDisposition {
    Ready,
    Blocked,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum AutomaticReplayDisposition {
    AllowedForReadOnlyOperation,
    BlockedUntilReconciled,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct OperationTerminalReceipt {
    pub(crate) effect: OperationEffect,
    pub(crate) handler_state: HandlerTerminalState,
    pub(crate) identity_state: OperationIdentityState,
}

impl OperationTerminalReceipt {
    pub(crate) fn at_dispatch_returned(effect: OperationEffect) -> Self {
        Self {
            effect,
            handler_state: HandlerTerminalState::ReturnedResult,
            identity_state: OperationIdentityState::PendingResult,
        }
    }

    pub(crate) fn at_dispatch_failed(effect: OperationEffect) -> Self {
        Self {
            effect,
            handler_state: HandlerTerminalState::FailedBeforeResult,
            identity_state: OperationIdentityState::MissingResult,
        }
    }

    pub(crate) fn compaction_disposition(self) -> CompactionDisposition {
        match self.identity_state {
            OperationIdentityState::Complete => CompactionDisposition::Ready,
            OperationIdentityState::PendingResult
            | OperationIdentityState::MissingResult
            | OperationIdentityState::DuplicateResult
            | OperationIdentityState::ReorderedResult
            | OperationIdentityState::LateResultPendingReconciliation => {
                CompactionDisposition::Blocked
            }
        }
    }

    pub(crate) fn automatic_replay_disposition(self) -> AutomaticReplayDisposition {
        match (self.effect, self.identity_state) {
            (OperationEffect::ReadOnly, OperationIdentityState::Complete) => {
                AutomaticReplayDisposition::AllowedForReadOnlyOperation
            }
            _ => AutomaticReplayDisposition::BlockedUntilReconciled,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn unknown_runtime_defaults_to_potential_mutation() {
        assert_eq!(
            OperationEffect::from_read_only_hint(None),
            OperationEffect::PotentialMutation
        );
    }

    #[test]
    fn explicit_read_only_hint_is_preserved() {
        assert_eq!(
            OperationEffect::from_read_only_hint(Some(true)),
            OperationEffect::ReadOnly
        );
    }

    #[test]
    fn returned_result_blocks_compaction_until_persisted() {
        let receipt = OperationTerminalReceipt::at_dispatch_returned(
            OperationEffect::PotentialMutation,
        );
        assert_eq!(receipt.handler_state, HandlerTerminalState::ReturnedResult);
        assert_eq!(receipt.identity_state, OperationIdentityState::PendingResult);
        assert_eq!(receipt.compaction_disposition(), CompactionDisposition::Blocked);
        assert_eq!(
            receipt.automatic_replay_disposition(),
            AutomaticReplayDisposition::BlockedUntilReconciled
        );
    }

    #[test]
    fn failure_before_result_blocks_compaction_and_replay() {
        let receipt = OperationTerminalReceipt::at_dispatch_failed(
            OperationEffect::PotentialMutation,
        );
        assert_eq!(
            receipt.handler_state,
            HandlerTerminalState::FailedBeforeResult
        );
        assert_eq!(receipt.identity_state, OperationIdentityState::MissingResult);
        assert_eq!(receipt.compaction_disposition(), CompactionDisposition::Blocked);
        assert_eq!(
            receipt.automatic_replay_disposition(),
            AutomaticReplayDisposition::BlockedUntilReconciled
        );
    }

    #[test]
    fn complete_read_only_receipt_allows_read_only_retry() {
        let receipt = OperationTerminalReceipt {
            effect: OperationEffect::ReadOnly,
            handler_state: HandlerTerminalState::ReturnedResult,
            identity_state: OperationIdentityState::Complete,
        };
        assert_eq!(receipt.compaction_disposition(), CompactionDisposition::Ready);
        assert_eq!(
            receipt.automatic_replay_disposition(),
            AutomaticReplayDisposition::AllowedForReadOnlyOperation
        );
    }

    #[test]
    fn complete_mutation_receipt_still_blocks_automatic_replay() {
        let receipt = OperationTerminalReceipt {
            effect: OperationEffect::PotentialMutation,
            handler_state: HandlerTerminalState::ReturnedResult,
            identity_state: OperationIdentityState::Complete,
        };
        assert_eq!(receipt.compaction_disposition(), CompactionDisposition::Ready);
        assert_eq!(
            receipt.automatic_replay_disposition(),
            AutomaticReplayDisposition::BlockedUntilReconciled
        );
    }

    #[test]
    fn every_ambiguous_identity_state_blocks_compaction_and_replay() {
        for identity_state in [
            OperationIdentityState::MissingResult,
            OperationIdentityState::DuplicateResult,
            OperationIdentityState::ReorderedResult,
            OperationIdentityState::LateResultPendingReconciliation,
        ] {
            let receipt = OperationTerminalReceipt {
                effect: OperationEffect::PotentialMutation,
                handler_state: HandlerTerminalState::ReturnedResult,
                identity_state,
            };
            assert_eq!(receipt.compaction_disposition(), CompactionDisposition::Blocked);
            assert_eq!(
                receipt.automatic_replay_disposition(),
                AutomaticReplayDisposition::BlockedUntilReconciled
            );
        }
    }
}
