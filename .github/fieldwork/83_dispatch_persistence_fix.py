#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "codex-rs" / "core" / "src"


def replace_exact(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one match in {path}: found {count} for {old!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


replace_exact(
    CORE / "state" / "tool_operation.rs",
    "    pub(crate) fn snapshot(&self) -> BTreeMap<String, ToolOperationReceipt> {\n        self.receipts.clone()\n    }\n",
    "    pub(crate) fn record_result_ambiguous(&mut self, call_id: &str) {\n        self.receipts\n            .entry(call_id.to_string())\n            .or_insert_with(|| {\n                ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation)\n            })\n            .record_result_ambiguous();\n    }\n\n    pub(crate) fn snapshot(&self) -> BTreeMap<String, ToolOperationReceipt> {\n        self.receipts.clone()\n    }\n",
)

replace_exact(
    CORE / "session" / "tool_operation.rs",
    "    pub(crate) async fn record_tool_operation_result_persisted(&self, call_id: &str) {\n        self.state\n            .lock()\n            .await\n            .tool_operation_receipts\n            .record_result_persisted(call_id);\n    }\n\n    pub(crate) async fn tool_operation_receipts_snapshot(\n",
    "    pub(crate) async fn record_tool_operation_result_persisted(&self, call_id: &str) {\n        self.state\n            .lock()\n            .await\n            .tool_operation_receipts\n            .record_result_persisted(call_id);\n    }\n\n    pub(crate) async fn record_tool_operation_result_ambiguous(&self, call_id: &str) {\n        self.state\n            .lock()\n            .await\n            .tool_operation_receipts\n            .record_result_ambiguous(call_id);\n    }\n\n    pub(crate) async fn tool_operation_receipts_snapshot(\n",
)

replace_exact(
    CORE / "session" / "mod.rs",
    "    pub(crate) async fn record_conversation_items(\n        &self,\n        turn_context: &TurnContext,\n        items: &[ResponseItem],\n    ) {\n",
    "    pub(crate) async fn record_conversation_items(\n        &self,\n        turn_context: &TurnContext,\n        items: &[ResponseItem],\n    ) -> bool {\n",
)
replace_exact(
    CORE / "session" / "mod.rs",
    "        self.persist_rollout_response_items(items).await;\n        self.send_raw_response_items(turn_context, items).await;\n    }\n",
    "        let result_persisted = self.persist_rollout_response_items(items).await;\n        self.send_raw_response_items(turn_context, items).await;\n        result_persisted\n    }\n",
)
replace_exact(
    CORE / "session" / "mod.rs",
    "    async fn persist_rollout_response_items(&self, items: &[ResponseItem]) {\n        let rollout_items: Vec<RolloutItem> = items\n            .iter()\n            .cloned()\n            .map(RolloutItem::ResponseItem)\n            .collect();\n        self.persist_rollout_items(&rollout_items).await;\n    }\n",
    "    async fn persist_rollout_response_items(&self, items: &[ResponseItem]) -> bool {\n        let rollout_items: Vec<RolloutItem> = items\n            .iter()\n            .cloned()\n            .map(RolloutItem::ResponseItem)\n            .collect();\n        self.persist_rollout_items_checked(&rollout_items).await\n    }\n",
)
replace_exact(
    CORE / "session" / "mod.rs",
    "    #[tracing::instrument(level = \"trace\", skip_all, fields(item_count = items.len()))]\n    pub(crate) async fn persist_rollout_items(&self, items: &[RolloutItem]) {\n        if let Some(live_thread) = self.live_thread()\n            && let Err(e) = live_thread.append_items(items).await\n        {\n            error!(\"failed to record rollout items: {e:#}\");\n        }\n    }\n",
    "    #[tracing::instrument(level = \"trace\", skip_all, fields(item_count = items.len()))]\n    pub(crate) async fn persist_rollout_items(&self, items: &[RolloutItem]) {\n        let _ = self.persist_rollout_items_checked(items).await;\n    }\n\n    /// Persists rollout items and reports whether they reached the authoritative\n    /// history for this session lifetime. Ephemeral sessions intentionally use\n    /// in-memory history as their complete lifetime.\n    async fn persist_rollout_items_checked(&self, items: &[RolloutItem]) -> bool {\n        let Some(live_thread) = self.live_thread() else {\n            return true;\n        };\n        if let Err(e) = live_thread.append_items(items).await {\n            error!(\"failed to record rollout items: {e:#}\");\n            return false;\n        }\n        true\n    }\n",
)

replace_exact(
    CORE / "session" / "turn.rs",
    "                sess.record_conversation_items(&turn_context, std::slice::from_ref(&response_item))\n                    .await;\n                if let Some(call_id) = call_id {\n                    sess.record_tool_operation_result_persisted(&call_id).await;\n                }\n",
    "                let result_persisted = sess\n                    .record_conversation_items(&turn_context, std::slice::from_ref(&response_item))\n                    .await;\n                if let Some(call_id) = call_id {\n                    if result_persisted {\n                        sess.record_tool_operation_result_persisted(&call_id).await;\n                    } else {\n                        sess.record_tool_operation_result_ambiguous(&call_id).await;\n                    }\n                }\n",
)

ledger_tests = CORE / "state" / "tool_operation_tests.rs"
with ledger_tests.open("a", encoding="utf-8") as handle:
    handle.write(r'''

#[test]
fn failed_persistence_marks_result_ambiguous() {
    let mut receipts = ToolOperationReceipts::default();
    receipts.start("call-1", ToolOperationEffect::PotentialMutation);
    receipts.record_terminal("call-1", ToolOperationTerminalState::Completed);
    receipts.record_result_ambiguous("call-1");

    assert_eq!(
        receipts.snapshot()["call-1"].result_state,
        ToolOperationResultState::Ambiguous
    );
    assert!(!receipts.snapshot()["call-1"].is_compaction_ready());
}
''')
