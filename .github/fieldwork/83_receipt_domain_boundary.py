from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str, label: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    file_path.write_text(text.replace(old, new), encoding="utf-8")


path = "codex-rs/protocol/src/tool_operation.rs"
replace_once(
    path,
    '''
    /// Returns whether this receipt permits compaction of the represented operation.
    pub fn is_compaction_ready(&self) -> bool {
        match self.effect {
            ToolOperationEffect::ReadOnly => true,
            ToolOperationEffect::PotentialMutation => {
                matches!(
                    self.terminal_state,
                    ToolOperationTerminalState::Completed
                        | ToolOperationTerminalState::Failed
                        | ToolOperationTerminalState::Aborted
                ) && self.result_state == ToolOperationResultState::Persisted
            }
        }
    }
''',
    "",
    "remove wire compaction predicate",
)
replace_once(
    path,
    '''    #[test]
    fn potential_mutation_requires_terminal_and_persisted_result() {
        let mut receipt = ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation);
        assert!(!receipt.is_compaction_ready());

        receipt.record_terminal_outcome(ToolOperationTerminalState::Completed);
        assert!(!receipt.is_compaction_ready());

        receipt.record_result_persisted();
        assert!(receipt.is_compaction_ready());
    }
''',
    '''    #[test]
    fn potential_mutation_records_terminal_and_persisted_result() {
        let mut receipt = ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation);
        assert_eq!(
            receipt.terminal_state,
            ToolOperationTerminalState::Pending
        );
        assert_eq!(receipt.result_state, ToolOperationResultState::Pending);

        receipt.record_terminal_outcome(ToolOperationTerminalState::Completed);
        assert_eq!(
            receipt.terminal_state,
            ToolOperationTerminalState::Completed
        );

        receipt.record_result_persisted();
        assert_eq!(receipt.result_state, ToolOperationResultState::Persisted);
    }
''',
    "replace compaction-decision test",
)
replace_once(
    path,
    '''        assert_eq!(receipt.result_state, ToolOperationResultState::Ambiguous);
        assert!(!receipt.is_compaction_ready());
''',
    '''        assert_eq!(receipt.result_state, ToolOperationResultState::Ambiguous);
''',
    "remove duplicate-result compaction assertion",
)
replace_once(
    path,
    '''    #[test]
    fn code_mode_identity_excludes_synthetic_host_call_id() -> Result<()> {
''',
    '''    #[test]
    fn wire_dto_preserves_unvalidated_state_for_domain_validation() -> Result<()> {
        let receipt = serde_json::from_value::<ToolOperationReceipt>(json!({
            "effect": "read_only",
            "terminal_state": "pending",
            "result_state": "pending",
        }))?;

        assert_eq!(receipt.effect, ToolOperationEffect::ReadOnly);
        assert_eq!(
            receipt.terminal_state,
            ToolOperationTerminalState::Pending
        );
        assert_eq!(receipt.result_state, ToolOperationResultState::Pending);
        Ok(())
    }

    #[test]
    fn code_mode_identity_excludes_synthetic_host_call_id() -> Result<()> {
''',
    "add permissive wire dto control",
)
