use codex_protocol::error::CodexErrorDetails;
use codex_protocol::error::Result as CodexResult;
use codex_protocol::models::ResponseItem;
use std::collections::BTreeMap;

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
enum CallFamily {
    Function,
    Custom,
    ToolSearch,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub(crate) enum CompactionIdentityDefectKind {
    DuplicateCall,
    DuplicateOutput,
    MissingOutput,
    OrphanOutput,
    OutputBeforeCall,
    UnpairableCall,
    UnpairableOutput,
}

impl CompactionIdentityDefectKind {
    fn as_str(self) -> &'static str {
        match self {
            Self::DuplicateCall => "duplicate_call",
            Self::DuplicateOutput => "duplicate_output",
            Self::MissingOutput => "missing_output",
            Self::OrphanOutput => "orphan_output",
            Self::OutputBeforeCall => "output_before_call",
            Self::UnpairableCall => "unpairable_call",
            Self::UnpairableOutput => "unpairable_output",
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct CompactionIdentityDefect {
    family: CallFamily,
    pub(crate) kind: CompactionIdentityDefectKind,
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
struct CallKey {
    family: CallFamily,
    call_id: String,
}

/// Rejects raw history that cannot preserve one causal call/result pair per call.
///
/// Prompt normalization deliberately repairs missing outputs and removes orphaned
/// outputs in a cloned model-facing view. Compaction must inspect raw history
/// instead so it never converts an ambiguous execution state into an authoritative
/// replacement checkpoint.
///
/// Legacy local-shell calls and client-executed tool-search items without a call ID
/// are reported as unpairable. Server-executed tool-search items remain outside
/// client call/result pairing because the provider owns their terminal identity.
pub(crate) fn validate_compaction_call_output_identity(items: &[ResponseItem]) -> CodexResult<()> {
    let defects = compaction_identity_defects(items);
    if defects.is_empty() {
        return Ok(());
    }

    let mut counts = BTreeMap::<&'static str, usize>::new();
    for defect in defects {
        *counts.entry(defect.kind.as_str()).or_default() += 1;
    }
    let summary = counts
        .into_iter()
        .map(|(kind, count)| format!("{kind}={count}"))
        .collect::<Vec<_>>()
        .join(", ");

    Err(CodexErrorDetails::InvalidRequest(format!(
        "compaction paused because tool call/result identity is ambiguous ({summary})"
    ))
    .into())
}

fn compaction_identity_defects(items: &[ResponseItem]) -> Vec<CompactionIdentityDefect> {
    let mut calls = BTreeMap::<CallKey, Vec<usize>>::new();
    let mut outputs = BTreeMap::<CallKey, Vec<usize>>::new();
    let mut defects = Vec::new();

    for (index, item) in items.iter().enumerate() {
        match item {
            ResponseItem::FunctionCall { call_id, .. } => {
                record_position(&mut calls, CallFamily::Function, call_id, index);
            }
            ResponseItem::LocalShellCall {
                call_id: Some(call_id),
                ..
            } => {
                record_position(&mut calls, CallFamily::Function, call_id, index);
            }
            ResponseItem::LocalShellCall { call_id: None, .. } => {
                defects.push(CompactionIdentityDefect {
                    family: CallFamily::Function,
                    kind: CompactionIdentityDefectKind::UnpairableCall,
                });
            }
            ResponseItem::FunctionCallOutput { call_id, .. } => {
                record_position(&mut outputs, CallFamily::Function, call_id, index);
            }
            ResponseItem::CustomToolCall { call_id, .. } => {
                record_position(&mut calls, CallFamily::Custom, call_id, index);
            }
            ResponseItem::CustomToolCallOutput { call_id, .. } => {
                record_position(&mut outputs, CallFamily::Custom, call_id, index);
            }
            ResponseItem::ToolSearchCall {
                call_id: Some(call_id),
                execution,
                ..
            } if execution == "client" => {
                record_position(&mut calls, CallFamily::ToolSearch, call_id, index);
            }
            ResponseItem::ToolSearchCall {
                call_id: None,
                execution,
                ..
            } if execution == "client" => {
                defects.push(CompactionIdentityDefect {
                    family: CallFamily::ToolSearch,
                    kind: CompactionIdentityDefectKind::UnpairableCall,
                });
            }
            ResponseItem::ToolSearchOutput {
                call_id: Some(call_id),
                execution,
                ..
            } if execution == "client" => {
                record_position(&mut outputs, CallFamily::ToolSearch, call_id, index);
            }
            ResponseItem::ToolSearchOutput {
                call_id: None,
                execution,
                ..
            } if execution == "client" => {
                defects.push(CompactionIdentityDefect {
                    family: CallFamily::ToolSearch,
                    kind: CompactionIdentityDefectKind::UnpairableOutput,
                });
            }
            _ => {}
        }
    }

    let mut keys = calls
        .keys()
        .chain(outputs.keys())
        .cloned()
        .collect::<Vec<_>>();
    keys.sort();
    keys.dedup();

    for key in keys {
        let call_positions = calls.get(&key).map(Vec::as_slice).unwrap_or_default();
        let output_positions = outputs.get(&key).map(Vec::as_slice).unwrap_or_default();

        if call_positions.is_empty() {
            defects.push(CompactionIdentityDefect {
                family: key.family,
                kind: CompactionIdentityDefectKind::OrphanOutput,
            });
            continue;
        }
        if call_positions.len() > 1 {
            defects.push(CompactionIdentityDefect {
                family: key.family,
                kind: CompactionIdentityDefectKind::DuplicateCall,
            });
        }
        if output_positions.is_empty() {
            defects.push(CompactionIdentityDefect {
                family: key.family,
                kind: CompactionIdentityDefectKind::MissingOutput,
            });
            continue;
        }
        if output_positions.len() > 1 {
            defects.push(CompactionIdentityDefect {
                family: key.family,
                kind: CompactionIdentityDefectKind::DuplicateOutput,
            });
        }
        if output_positions[0] < call_positions[0] {
            defects.push(CompactionIdentityDefect {
                family: key.family,
                kind: CompactionIdentityDefectKind::OutputBeforeCall,
            });
        }
    }
    defects
}

fn record_position(
    positions: &mut BTreeMap<CallKey, Vec<usize>>,
    family: CallFamily,
    call_id: &str,
    index: usize,
) {
    positions
        .entry(CallKey {
            family,
            call_id: call_id.to_string(),
        })
        .or_default()
        .push(index);
}

#[cfg(test)]
#[path = "compaction_identity_tests.rs"]
mod tests;
