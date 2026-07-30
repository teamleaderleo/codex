from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str, label: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    file_path.write_text(text.replace(old, new), encoding="utf-8")


def append_before(path: str, anchor: str, addition: str, label: str) -> None:
    replace_once(path, anchor, addition + anchor, label)


# Protocol-owned rollout envelope.
append_before(
    "codex-rs/protocol/src/tool_operation.rs",
    "\n#[cfg(test)]\nmod tests {",
    """
/// One durable receipt record in rollout order.
#[derive(Clone, Debug, Deserialize, Eq, JsonSchema, PartialEq, Serialize, TS)]
#[serde(tag = "kind", content = "payload", rename_all = "snake_case")]
pub enum ToolOperationReceiptItem {
    Activation(ToolOperationReceiptActivation),
    Update(ToolOperationReceiptUpdate),
}

""",
    "receipt rollout envelope",
)

replace_once(
    "codex-rs/protocol/src/protocol.rs",
    "use crate::user_input::UserInput;\n",
    "use crate::tool_operation::ToolOperationReceiptItem;\nuse crate::user_input::UserInput;\n",
    "protocol receipt import",
)
replace_once(
    "codex-rs/protocol/src/protocol.rs",
    "    WorldState(WorldStateItem),\n    EventMsg(EventMsg),\n",
    "    WorldState(WorldStateItem),\n    ToolOperationReceipt(ToolOperationReceiptItem),\n    EventMsg(EventMsg),\n",
    "rollout receipt variant",
)

# Fail-closed bounded replay owner.
Path("codex-rs/core/src/state/tool_operation_receipts.rs").write_text(
    r'''use std::collections::HashMap;

use codex_protocol::tool_operation::TOOL_OPERATION_RECEIPT_VERSION;
use codex_protocol::tool_operation::ToolOperationEffect;
use codex_protocol::tool_operation::ToolOperationId;
use codex_protocol::tool_operation::ToolOperationReceipt;
use codex_protocol::tool_operation::ToolOperationReceiptActivation;
use codex_protocol::tool_operation::ToolOperationReceiptItem;
use codex_protocol::tool_operation::ToolOperationReceiptUpdate;

const MAX_RETAINED_TOOL_OPERATION_RECEIPTS: usize = 1024;

/// Bounded receipt state reconstructed from surviving rollout records.
#[derive(Clone, Debug, Default)]
pub(crate) struct ToolOperationReceiptLedger {
    epoch_id: Option<String>,
    next_sequence: u64,
    receipts: HashMap<ToolOperationId, ToolOperationReceipt>,
    last_update: Option<ToolOperationReceiptUpdate>,
    coverage_lost: bool,
    invalid: bool,
}

impl ToolOperationReceiptLedger {
    pub(crate) fn apply_item(&mut self, item: &ToolOperationReceiptItem) {
        match item {
            ToolOperationReceiptItem::Activation(activation) => {
                self.apply_activation(activation);
            }
            ToolOperationReceiptItem::Update(update) => self.apply_update(update),
        }
    }

    fn apply_activation(&mut self, activation: &ToolOperationReceiptActivation) {
        if activation.version != TOOL_OPERATION_RECEIPT_VERSION || activation.epoch_id.is_empty() {
            self.invalid = true;
            return;
        }
        if self.epoch_id.as_deref() == Some(activation.epoch_id.as_str()) {
            return;
        }
        self.epoch_id = Some(activation.epoch_id.clone());
        self.next_sequence = 0;
        self.receipts.clear();
        self.last_update = None;
        self.coverage_lost = false;
        self.invalid = false;
    }

    fn apply_update(&mut self, update: &ToolOperationReceiptUpdate) {
        if update.version != TOOL_OPERATION_RECEIPT_VERSION
            || update.epoch_id.is_empty()
            || !operation_id_is_valid(&update.operation_id)
            || self.epoch_id.as_deref() != Some(update.epoch_id.as_str())
        {
            self.invalid = true;
            return;
        }

        if update.sequence != self.next_sequence {
            let identical_duplicate = self
                .last_update
                .as_ref()
                .is_some_and(|last_update| last_update == update)
                && update.sequence.checked_add(1) == Some(self.next_sequence);
            if identical_duplicate {
                return;
            }
            self.invalid = true;
            return;
        }

        let Some(next_sequence) = self.next_sequence.checked_add(1) else {
            self.invalid = true;
            return;
        };

        if self.receipts.contains_key(&update.operation_id)
            || self.receipts.len() < MAX_RETAINED_TOOL_OPERATION_RECEIPTS
        {
            self.receipts
                .insert(update.operation_id.clone(), update.receipt);
        } else {
            self.coverage_lost = true;
        }
        self.next_sequence = next_sequence;
        self.last_update = Some(update.clone());
    }

    pub(crate) fn receipt(
        &self,
        operation_id: &ToolOperationId,
    ) -> Option<ToolOperationReceipt> {
        self.receipts.get(operation_id).copied()
    }

    pub(crate) fn has_unreconciled_potential_mutation(&self) -> bool {
        self.invalid
            || self.coverage_lost
            || self.receipts.values().any(|receipt| {
                receipt.effect == ToolOperationEffect::PotentialMutation
                    && !receipt.is_compaction_ready()
            })
    }

    pub(crate) fn is_invalid(&self) -> bool {
        self.invalid
    }

    pub(crate) fn epoch_id(&self) -> Option<&str> {
        self.epoch_id.as_deref()
    }

    pub(crate) fn next_sequence(&self) -> u64 {
        self.next_sequence
    }
}

fn operation_id_is_valid(operation_id: &ToolOperationId) -> bool {
    match operation_id {
        ToolOperationId::Direct { call_id } => !call_id.is_empty(),
        ToolOperationId::CodeMode {
            cell_id,
            runtime_tool_call_id,
        } => !cell_id.is_empty() && !runtime_tool_call_id.is_empty(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn update_before_activation_fails_closed() {
        let mut ledger = ToolOperationReceiptLedger::default();
        ledger.apply_item(&ToolOperationReceiptItem::Update(
            ToolOperationReceiptUpdate::v1(
                "epoch-1",
                0,
                ToolOperationId::direct("call-1"),
                ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation),
            ),
        ));
        assert!(ledger.is_invalid());
        assert!(ledger.has_unreconciled_potential_mutation());
    }

    #[test]
    fn identical_duplicate_sequence_is_idempotent() {
        let mut ledger = ToolOperationReceiptLedger::default();
        ledger.apply_item(&ToolOperationReceiptItem::Activation(
            ToolOperationReceiptActivation::v1("epoch-1"),
        ));
        let update = ToolOperationReceiptUpdate::v1(
            "epoch-1",
            0,
            ToolOperationId::direct("call-1"),
            ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation),
        );
        ledger.apply_item(&ToolOperationReceiptItem::Update(update.clone()));
        ledger.apply_item(&ToolOperationReceiptItem::Update(update));
        assert!(!ledger.is_invalid());
        assert_eq!(ledger.next_sequence(), 1);
    }
}
''',
    encoding="utf-8",
)

replace_once(
    "codex-rs/core/src/state/mod.rs",
    "mod session;\nmod turn;\n",
    "mod session;\nmod tool_operation_receipts;\nmod turn;\n",
    "state receipt module",
)
replace_once(
    "codex-rs/core/src/state/mod.rs",
    "pub(crate) use session::SessionState;\n",
    "pub(crate) use session::SessionState;\npub(crate) use tool_operation_receipts::ToolOperationReceiptLedger;\n",
    "state receipt export",
)

replace_once(
    "codex-rs/core/src/state/session.rs",
    "use super::AdditionalContextStore;\n",
    "use super::AdditionalContextStore;\nuse super::ToolOperationReceiptLedger;\n",
    "session receipt import",
)
replace_once(
    "codex-rs/core/src/state/session.rs",
    "    pub(crate) additional_context: AdditionalContextStore,\n",
    "    pub(crate) additional_context: AdditionalContextStore,\n    tool_operation_receipts: ToolOperationReceiptLedger,\n",
    "session receipt field",
)
replace_once(
    "codex-rs/core/src/state/session.rs",
    "            additional_context: AdditionalContextStore::default(),\n",
    "            additional_context: AdditionalContextStore::default(),\n            tool_operation_receipts: ToolOperationReceiptLedger::default(),\n",
    "session receipt init",
)
append_before(
    "codex-rs/core/src/state/session.rs",
    "    pub(crate) fn previous_turn_settings(&self) -> Option<PreviousTurnSettings> {\n",
    """    pub(crate) fn install_tool_operation_receipts(
        &mut self,
        tool_operation_receipts: ToolOperationReceiptLedger,
    ) {
        self.tool_operation_receipts = tool_operation_receipts;
    }

    pub(crate) fn tool_operation_receipts(&self) -> &ToolOperationReceiptLedger {
        &self.tool_operation_receipts
    }

""",
    "session receipt methods",
)

# Rollback-aware replay integration.
replace_once(
    "codex-rs/core/src/session/rollout_reconstruction.rs",
    "use crate::context_manager::is_user_turn_boundary;\n",
    "use crate::context_manager::is_user_turn_boundary;\nuse crate::state::ToolOperationReceiptLedger;\n",
    "reconstruction ledger import",
)
replace_once(
    "codex-rs/core/src/session/rollout_reconstruction.rs",
    "use codex_protocol::protocol::SessionContextWindow;\n",
    "use codex_protocol::protocol::SessionContextWindow;\nuse codex_protocol::tool_operation::ToolOperationReceiptItem;\n",
    "reconstruction item import",
)
replace_once(
    "codex-rs/core/src/session/rollout_reconstruction.rs",
    "    pub(super) history: Vec<ResponseItem>,\n",
    "    pub(super) history: Vec<ResponseItem>,\n    pub(super) tool_operation_receipts: ToolOperationReceiptLedger,\n",
    "reconstruction receipt result",
)
replace_once(
    "codex-rs/core/src/session/rollout_reconstruction.rs",
    "    world_state_replay: Vec<&'a RolloutItem>,\n",
    "    world_state_replay: Vec<&'a RolloutItem>,\n    tool_operation_receipt_replay: Vec<&'a ToolOperationReceiptItem>,\n",
    "segment receipt replay",
)
replace_once(
    "codex-rs/core/src/session/rollout_reconstruction.rs",
    "    world_state_replay: &mut Vec<&'a RolloutItem>,\n    window: &mut Option<ReconstructedWindow>,\n",
    "    world_state_replay: &mut Vec<&'a RolloutItem>,\n    tool_operation_receipt_replay: &mut Vec<&'a ToolOperationReceiptItem>,\n    window: &mut Option<ReconstructedWindow>,\n",
    "finalize receipt parameter",
)
replace_once(
    "codex-rs/core/src/session/rollout_reconstruction.rs",
    "    world_state_replay.extend(active_segment.world_state_replay);\n\n",
    "    world_state_replay.extend(active_segment.world_state_replay);\n    tool_operation_receipt_replay.extend(active_segment.tool_operation_receipt_replay);\n\n",
    "finalize receipt replay",
)
replace_once(
    "codex-rs/core/src/session/rollout_reconstruction.rs",
    "        let has_legacy_compaction_without_window_number =\n",
    "        let has_tool_operation_receipt_items = rollout_items\n            .iter()\n            .any(|item| matches!(item, RolloutItem::ToolOperationReceipt(_)));\n        let has_legacy_compaction_without_window_number =\n",
    "receipt full scan flag",
)
replace_once(
    "codex-rs/core/src/session/rollout_reconstruction.rs",
    "        let mut world_state_replay = Vec::new();\n        let mut window = None;\n",
    "        let mut world_state_replay = Vec::new();\n        let mut tool_operation_receipt_replay = Vec::new();\n        let mut window = None;\n",
    "receipt replay accumulator",
)
replace_once(
    "codex-rs/core/src/session/rollout_reconstruction.rs",
    "                RolloutItem::WorldState(_) => {\n                    let active_segment =\n                        active_segment.get_or_insert_with(ActiveReplaySegment::default);\n                    active_segment.world_state_replay.push(item);\n                }\n",
    "                RolloutItem::WorldState(_) => {\n                    let active_segment =\n                        active_segment.get_or_insert_with(ActiveReplaySegment::default);\n                    active_segment.world_state_replay.push(item);\n                }\n                RolloutItem::ToolOperationReceipt(receipt_item) => {\n                    let active_segment =\n                        active_segment.get_or_insert_with(ActiveReplaySegment::default);\n                    active_segment\n                        .tool_operation_receipt_replay\n                        .push(receipt_item);\n                }\n",
    "receipt reverse collection",
)
# Both finalize calls share this argument sequence.
text_path = Path("codex-rs/core/src/session/rollout_reconstruction.rs")
text = text_path.read_text(encoding="utf-8")
old = "                            &mut world_state_replay,\n                            &mut window,\n"
count = text.count(old)
if count != 1:
    raise SystemExit(f"turn finalize receipt args: expected one anchor, found {count}")
text = text.replace(
    old,
    "                            &mut world_state_replay,\n                            &mut tool_operation_receipt_replay,\n                            &mut window,\n",
)
old = "                &mut world_state_replay,\n                &mut window,\n"
count = text.count(old)
if count != 1:
    raise SystemExit(f"tail finalize receipt args: expected one anchor, found {count}")
text = text.replace(
    old,
    "                &mut world_state_replay,\n                &mut tool_operation_receipt_replay,\n                &mut window,\n",
)
text_path.write_text(text, encoding="utf-8")
replace_once(
    "codex-rs/core/src/session/rollout_reconstruction.rs",
    "            if base_replacement_history.is_some()\n",
    "            if !has_tool_operation_receipt_items\n                && base_replacement_history.is_some()\n",
    "receipt full reverse scan gate",
)
replace_once(
    "codex-rs/core/src/session/rollout_reconstruction.rs",
    "                RolloutItem::EventMsg(_)\n                | RolloutItem::TurnContext(_)\n",
    "                RolloutItem::EventMsg(_)\n                | RolloutItem::ToolOperationReceipt(_)\n                | RolloutItem::TurnContext(_)\n",
    "history receipt ignore",
)
replace_once(
    "codex-rs/core/src/session/rollout_reconstruction.rs",
    "                 | RolloutItem::TurnContext(_)\n                 | RolloutItem::EventMsg(_) => {\n",
    "                 | RolloutItem::TurnContext(_)\n                 | RolloutItem::ToolOperationReceipt(_)\n                 | RolloutItem::EventMsg(_) => {\n",
    "world state receipt unreachable",
)
append_before(
    "codex-rs/core/src/session/rollout_reconstruction.rs",
    "        let window = window.or(initial_window).unwrap_or(ReconstructedWindow {\n",
    """        tool_operation_receipt_replay.reverse();
        let mut tool_operation_receipts = ToolOperationReceiptLedger::default();
        for receipt_item in tool_operation_receipt_replay {
            tool_operation_receipts.apply_item(receipt_item);
        }

""",
    "receipt chronological fold",
)
replace_once(
    "codex-rs/core/src/session/rollout_reconstruction.rs",
    "        RolloutReconstruction {\n            history: history.into_raw_items(),\n",
    "        RolloutReconstruction {\n            history: history.into_raw_items(),\n            tool_operation_receipts,\n",
    "receipt reconstruction return",
)

replace_once(
    "codex-rs/core/src/session/mod.rs",
    "            mut history,\n            previous_turn_settings,\n",
    "            mut history,\n            tool_operation_receipts,\n            previous_turn_settings,\n",
    "install receipt destructure",
)
replace_once(
    "codex-rs/core/src/session/mod.rs",
    "            state.replace_history(history, reference_context_item);\n",
    "            state.replace_history(history, reference_context_item);\n            state.install_tool_operation_receipts(tool_operation_receipts);\n",
    "install reconstructed receipts",
)

# Add focused replay tests to the existing reconstruction suite.
append_before(
    "codex-rs/core/src/session/rollout_reconstruction_tests.rs",
    "\n#[tokio::test]\nasync fn reconstruct_history_rollback_keeps_history_and_metadata_in_sync_for_completed_turns() {",
    r'''
#[tokio::test]
async fn receipt_replay_restores_direct_and_code_mode_identity() {
    use codex_protocol::tool_operation::ToolOperationEffect;
    use codex_protocol::tool_operation::ToolOperationId;
    use codex_protocol::tool_operation::ToolOperationReceipt;
    use codex_protocol::tool_operation::ToolOperationReceiptActivation;
    use codex_protocol::tool_operation::ToolOperationReceiptItem;
    use codex_protocol::tool_operation::ToolOperationReceiptUpdate;

    let (session, turn_context) = make_session_and_context().await;
    let direct_id = ToolOperationId::direct("call-1");
    let code_mode_id = ToolOperationId::code_mode("cell-2", "runtime-3");
    let rollout_items = vec![
        RolloutItem::ToolOperationReceipt(ToolOperationReceiptItem::Activation(
            ToolOperationReceiptActivation::v1("epoch-1"),
        )),
        RolloutItem::ToolOperationReceipt(ToolOperationReceiptItem::Update(
            ToolOperationReceiptUpdate::v1(
                "epoch-1",
                0,
                direct_id.clone(),
                ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation),
            ),
        )),
        RolloutItem::ToolOperationReceipt(ToolOperationReceiptItem::Update(
            ToolOperationReceiptUpdate::v1(
                "epoch-1",
                1,
                code_mode_id.clone(),
                ToolOperationReceipt::pending(ToolOperationEffect::ReadOnly),
            ),
        )),
    ];

    let reconstructed = session
        .reconstruct_history_from_rollout(&turn_context, &rollout_items)
        .await;

    assert_eq!(reconstructed.tool_operation_receipts.epoch_id(), Some("epoch-1"));
    assert_eq!(reconstructed.tool_operation_receipts.next_sequence(), 2);
    assert_eq!(
        reconstructed.tool_operation_receipts.receipt(&direct_id),
        Some(ToolOperationReceipt::pending(
            ToolOperationEffect::PotentialMutation
        ))
    );
    assert_eq!(
        reconstructed.tool_operation_receipts.receipt(&code_mode_id),
        Some(ToolOperationReceipt::pending(ToolOperationEffect::ReadOnly))
    );
}

#[tokio::test]
async fn receipt_replay_drops_rolled_back_turn_updates() {
    use codex_protocol::tool_operation::ToolOperationEffect;
    use codex_protocol::tool_operation::ToolOperationId;
    use codex_protocol::tool_operation::ToolOperationReceipt;
    use codex_protocol::tool_operation::ToolOperationReceiptActivation;
    use codex_protocol::tool_operation::ToolOperationReceiptItem;
    use codex_protocol::tool_operation::ToolOperationReceiptUpdate;

    let (session, turn_context) = make_session_and_context().await;
    let turn_context_item = turn_context.to_turn_context_item();
    let operation_id = ToolOperationId::direct("rolled-back-call");
    let mut rollout_items = vec![RolloutItem::ToolOperationReceipt(
        ToolOperationReceiptItem::Activation(ToolOperationReceiptActivation::v1("epoch-1")),
    )];
    rollout_items.extend(completed_user_turn_rollout(
        turn_context_item,
        vec![RolloutItem::ToolOperationReceipt(
            ToolOperationReceiptItem::Update(ToolOperationReceiptUpdate::v1(
                "epoch-1",
                0,
                operation_id.clone(),
                ToolOperationReceipt::pending(ToolOperationEffect::PotentialMutation),
            )),
        )],
    ));
    rollout_items.push(RolloutItem::EventMsg(EventMsg::ThreadRolledBack(
        codex_protocol::protocol::ThreadRolledBackEvent { num_turns: 1 },
    )));

    let reconstructed = session
        .reconstruct_history_from_rollout(&turn_context, &rollout_items)
        .await;

    assert_eq!(reconstructed.tool_operation_receipts.epoch_id(), Some("epoch-1"));
    assert_eq!(reconstructed.tool_operation_receipts.next_sequence(), 0);
    assert_eq!(
        reconstructed.tool_operation_receipts.receipt(&operation_id),
        None
    );
    assert!(!reconstructed.tool_operation_receipts.is_invalid());
}

''',
    "receipt reconstruction tests",
)

# Most exhaustive RolloutItem matches already group ignored session metadata. Add the new local
# metadata record to those wildcard groups while retaining specialized SessionMeta arms.
for rust_path in Path("codex-rs").rglob("*.rs"):
    text = rust_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    output: list[str] = []
    changed = False
    for line in lines:
        stripped = line.lstrip()
        if "RolloutItem::SessionMeta(_)" in stripped:
            nearby = "".join(output[-8:])
            if "RolloutItem::ToolOperationReceipt(_)" not in nearby:
                indent = line[: len(line) - len(stripped)]
                prefix = "| " if stripped.startswith("|") else ""
                output.append(f"{indent}{prefix}RolloutItem::ToolOperationReceipt(_)\n")
                changed = True
        output.append(line)
    if changed:
        rust_path.write_text("".join(output), encoding="utf-8")
