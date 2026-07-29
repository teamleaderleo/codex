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


ledger = r'''use std::collections::BTreeMap;
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

    pub(crate) fn snapshot(&self) -> BTreeMap<String, ToolOperationReceipt> {
        self.receipts.clone()
    }
}

#[cfg(test)]
#[path = "tool_operation_tests.rs"]
mod tests;
'''

ledger_tests = r'''use super::*;
use codex_tools::ToolOperationResultState;

#[test]
fn complete_potential_mutation_receipt_is_retained() {
    let mut receipts = ToolOperationReceipts::default();
    receipts.start("call-1", ToolOperationEffect::PotentialMutation);
    receipts.record_terminal("call-1", ToolOperationTerminalState::Completed);
    receipts.record_result_persisted("call-1");

    assert_eq!(
        receipts.snapshot(),
        BTreeMap::from([(
            "call-1".to_string(),
            ToolOperationReceipt {
                version: 1,
                effect: ToolOperationEffect::PotentialMutation,
                terminal_state: ToolOperationTerminalState::Completed,
                result_state: ToolOperationResultState::Persisted,
            },
        )])
    );
}

#[test]
fn duplicate_start_marks_receipt_ambiguous_and_escalates_effect() {
    let mut receipts = ToolOperationReceipts::default();
    receipts.start("call-1", ToolOperationEffect::ReadOnly);
    receipts.start("call-1", ToolOperationEffect::PotentialMutation);

    assert_eq!(
        receipts.snapshot()["call-1"],
        ToolOperationReceipt {
            version: 1,
            effect: ToolOperationEffect::PotentialMutation,
            terminal_state: ToolOperationTerminalState::Ambiguous,
            result_state: ToolOperationResultState::Ambiguous,
        }
    );
}

#[test]
fn terminal_or_result_without_start_stays_conservative() {
    let mut receipts = ToolOperationReceipts::default();
    receipts.record_terminal("terminal-first", ToolOperationTerminalState::Failed);
    receipts.record_result_persisted("result-first");

    assert_eq!(
        receipts.snapshot(),
        BTreeMap::from([
            (
                "result-first".to_string(),
                ToolOperationReceipt {
                    version: 1,
                    effect: ToolOperationEffect::PotentialMutation,
                    terminal_state: ToolOperationTerminalState::Pending,
                    result_state: ToolOperationResultState::Persisted,
                },
            ),
            (
                "terminal-first".to_string(),
                ToolOperationReceipt {
                    version: 1,
                    effect: ToolOperationEffect::PotentialMutation,
                    terminal_state: ToolOperationTerminalState::Failed,
                    result_state: ToolOperationResultState::Pending,
                },
            ),
        ])
    );
}
'''

session_impl = r'''use std::collections::BTreeMap;

use codex_tools::ToolOperationEffect;
use codex_tools::ToolOperationReceipt;
use codex_tools::ToolOperationTerminalState;

use super::session::Session;

impl Session {
    pub(crate) async fn start_tool_operation_receipt(
        &self,
        call_id: &str,
        effect: ToolOperationEffect,
    ) {
        self.state
            .lock()
            .await
            .tool_operation_receipts
            .start(call_id, effect);
    }

    pub(crate) async fn record_tool_operation_terminal(
        &self,
        call_id: &str,
        terminal_state: ToolOperationTerminalState,
    ) {
        self.state
            .lock()
            .await
            .tool_operation_receipts
            .record_terminal(call_id, terminal_state);
    }

    pub(crate) async fn record_tool_operation_result_persisted(&self, call_id: &str) {
        self.state
            .lock()
            .await
            .tool_operation_receipts
            .record_result_persisted(call_id);
    }

    pub(crate) async fn tool_operation_receipts_snapshot(
        &self,
    ) -> BTreeMap<String, ToolOperationReceipt> {
        self.state
            .lock()
            .await
            .tool_operation_receipts
            .snapshot()
    }
}
'''

(CORE / "state" / "tool_operation.rs").write_text(ledger, encoding="utf-8")
(CORE / "state" / "tool_operation_tests.rs").write_text(ledger_tests, encoding="utf-8")
(CORE / "session" / "tool_operation.rs").write_text(session_impl, encoding="utf-8")

replace_exact(
    CORE / "state" / "mod.rs",
    "mod session;\nmod turn;\n",
    "mod session;\nmod tool_operation;\nmod turn;\n",
)
replace_exact(
    CORE / "state" / "mod.rs",
    "pub(crate) use session::SessionState;\n",
    "pub(crate) use session::SessionState;\npub(crate) use tool_operation::ToolOperationReceipts;\n",
)
replace_exact(
    CORE / "state" / "session.rs",
    "use super::AdditionalContextStore;\n",
    "use super::AdditionalContextStore;\nuse super::ToolOperationReceipts;\n",
)
replace_exact(
    CORE / "state" / "session.rs",
    "    pub(crate) history: ContextManager,\n    pub(crate) latest_rate_limits: Option<RateLimitSnapshot>,\n",
    "    pub(crate) history: ContextManager,\n    pub(crate) tool_operation_receipts: ToolOperationReceipts,\n    pub(crate) latest_rate_limits: Option<RateLimitSnapshot>,\n",
)
replace_exact(
    CORE / "state" / "session.rs",
    "            history,\n            latest_rate_limits: None,\n",
    "            history,\n            tool_operation_receipts: ToolOperationReceipts::default(),\n            latest_rate_limits: None,\n",
)
replace_exact(
    CORE / "session" / "mod.rs",
    "mod token_budget;\n",
    "mod token_budget;\nmod tool_operation;\n",
)

replace_exact(
    CORE / "tools" / "lifecycle.rs",
    "use codex_tools::ToolName;\n",
    "use codex_tools::ToolName;\nuse codex_tools::ToolOperationTerminalState;\n",
)
replace_exact(
    CORE / "tools" / "lifecycle.rs",
    ") {\n    for contributor in session.services.extensions.tool_lifecycle_contributors() {\n",
    ") {\n    if matches!(&source, ToolCallSource::Direct) {\n        let terminal_state = match &outcome {\n            ToolCallOutcome::Completed { .. } => ToolOperationTerminalState::Completed,\n            ToolCallOutcome::Failed { .. } | ToolCallOutcome::Blocked => {\n                ToolOperationTerminalState::Failed\n            }\n            ToolCallOutcome::Aborted => ToolOperationTerminalState::Aborted,\n            _ => ToolOperationTerminalState::Ambiguous,\n        };\n        session\n            .record_tool_operation_terminal(call_id, terminal_state)\n            .await;\n    }\n\n    for contributor in session.services.extensions.tool_lifecycle_contributors() {\n",
)

replace_exact(
    CORE / "tools" / "registry.rs",
    "use codex_tools::ToolName;\n",
    "use codex_tools::ToolName;\nuse codex_tools::ToolOperationEffect;\nuse codex_tools::ToolOperationTerminalState;\n",
)
replace_exact(
    CORE / "tools" / "registry.rs",
    "            None => {\n                let message = unsupported_tool_call_message(&invocation.payload, &tool_name);\n",
    "            None => {\n                if matches!(&invocation.source, ToolCallSource::Direct) {\n                    invocation\n                        .session\n                        .start_tool_operation_receipt(\n                            &call_id_owned,\n                            ToolOperationEffect::PotentialMutation,\n                        )\n                        .await;\n                    invocation\n                        .session\n                        .record_tool_operation_terminal(\n                            &call_id_owned,\n                            ToolOperationTerminalState::Failed,\n                        )\n                        .await;\n                }\n                let message = unsupported_tool_call_message(&invocation.payload, &tool_name);\n",
)
replace_exact(
    CORE / "tools" / "registry.rs",
    "        };\n\n        let telemetry_tags = tool.telemetry_tags(&invocation).await;\n",
    "        };\n\n        if matches!(&invocation.source, ToolCallSource::Direct) {\n            invocation\n                .session\n                .start_tool_operation_receipt(&call_id_owned, tool.operation_effect())\n                .await;\n        }\n\n        let telemetry_tags = tool.telemetry_tags(&invocation).await;\n",
)
replace_exact(
    CORE / "tools" / "registry.rs",
    "            let err = FunctionCallError::Fatal(message);\n            dispatch_trace.record_failed(&err);\n            return Err(err);\n",
    "            if matches!(&invocation.source, ToolCallSource::Direct) {\n                invocation\n                    .session\n                    .record_tool_operation_terminal(\n                        &call_id_owned,\n                        ToolOperationTerminalState::Failed,\n                    )\n                    .await;\n            }\n            let err = FunctionCallError::Fatal(message);\n            dispatch_trace.record_failed(&err);\n            return Err(err);\n",
)
replace_exact(
    CORE / "tools" / "registry.rs",
    "    fn exposure(&self) -> ToolExposure {\n        self.exposure\n    }\n\n    fn supports_parallel_tool_calls(&self) -> bool {\n",
    "    fn exposure(&self) -> ToolExposure {\n        self.exposure\n    }\n\n    fn operation_effect(&self) -> codex_tools::ToolOperationEffect {\n        self.handler.operation_effect()\n    }\n\n    fn supports_parallel_tool_calls(&self) -> bool {\n",
)

replace_exact(
    CORE / "session" / "turn.rs",
    "            Ok(response_input) => {\n                let response_item = response_input.into();\n                sess.record_conversation_items(&turn_context, std::slice::from_ref(&response_item))\n                    .await;\n",
    "            Ok(response_input) => {\n                let call_id = response_input_tool_call_id(&response_input).map(str::to_string);\n                let response_item = response_input.into();\n                sess.record_conversation_items(&turn_context, std::slice::from_ref(&response_item))\n                    .await;\n                if let Some(call_id) = call_id {\n                    sess.record_tool_operation_result_persisted(&call_id).await;\n                }\n",
)
replace_exact(
    CORE / "session" / "turn.rs",
    "    Ok(())\n}\n\nfn assign_missing_streamed_response_item_id(\n",
    "    Ok(())\n}\n\nfn response_input_tool_call_id(item: &ResponseInputItem) -> Option<&str> {\n    match item {\n        ResponseInputItem::FunctionCallOutput { call_id, .. }\n        | ResponseInputItem::McpToolCallOutput { call_id, .. }\n        | ResponseInputItem::CustomToolCallOutput { call_id, .. }\n        | ResponseInputItem::ToolSearchOutput { call_id, .. } => Some(call_id),\n        ResponseInputItem::Message { .. } => None,\n    }\n}\n\nfn assign_missing_streamed_response_item_id(\n",
)

registry_tests = CORE / "tools" / "registry_tests.rs"
with registry_tests.open("a", encoding="utf-8") as handle:
    handle.write(r'''

struct ReadOnlyEffectHandler {
    tool_name: codex_tools::ToolName,
}

impl ToolExecutor<ToolInvocation> for ReadOnlyEffectHandler {
    fn tool_name(&self) -> codex_tools::ToolName {
        self.tool_name.clone()
    }

    fn spec(&self) -> codex_tools::ToolSpec {
        test_spec(&self.tool_name)
    }

    fn operation_effect(&self) -> codex_tools::ToolOperationEffect {
        codex_tools::ToolOperationEffect::ReadOnly
    }

    fn handle(&self, _invocation: ToolInvocation) -> codex_tools::ToolExecutorFuture<'_> {
        Box::pin(async {
            Ok(Box::new(
                crate::tools::context::FunctionToolOutput::from_text(
                    "ok".to_string(),
                    Some(true),
                ),
            ) as Box<dyn crate::tools::context::ToolOutput>)
        })
    }
}

impl CoreToolRuntime for ReadOnlyEffectHandler {}

#[test]
fn exposure_override_preserves_operation_effect() {
    let handler = Arc::new(ReadOnlyEffectHandler {
        tool_name: codex_tools::ToolName::plain("read_only"),
    }) as Arc<dyn CoreToolRuntime>;

    let overridden = override_tool_exposure(handler, ToolExposure::Hidden);

    assert_eq!(
        overridden.operation_effect(),
        codex_tools::ToolOperationEffect::ReadOnly
    );
}
''')
