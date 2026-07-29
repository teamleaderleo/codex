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


module = r'''use std::collections::BTreeMap;

use codex_protocol::error::CodexErrorDetails;
use codex_protocol::error::Result as CodexResult;
use codex_protocol::models::ResponseItem;

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub(super) enum CallResultIdentityIssue {
    MissingCallId {
        family: &'static str,
        index: usize,
    },
    MissingOutputCallId {
        family: &'static str,
        index: usize,
    },
    DuplicateCall {
        family: &'static str,
        call_id: String,
    },
    MissingOutput {
        family: &'static str,
        call_id: String,
    },
    DuplicateOutput {
        family: &'static str,
        call_id: String,
    },
    OutputPrecedesCall {
        family: &'static str,
        call_id: String,
    },
    OrphanOutput {
        family: &'static str,
        call_id: String,
    },
}

impl CallResultIdentityIssue {
    fn code(&self) -> String {
        match self {
            Self::MissingCallId { family, index } => {
                format!("missing_call_id:{family}:{index}")
            }
            Self::MissingOutputCallId { family, index } => {
                format!("missing_output_call_id:{family}:{index}")
            }
            Self::DuplicateCall { family, call_id } => {
                format!("duplicate_call:{family}:{call_id}")
            }
            Self::MissingOutput { family, call_id } => {
                format!("missing_output:{family}:{call_id}")
            }
            Self::DuplicateOutput { family, call_id } => {
                format!("duplicate_output:{family}:{call_id}")
            }
            Self::OutputPrecedesCall { family, call_id } => {
                format!("output_precedes_call:{family}:{call_id}")
            }
            Self::OrphanOutput { family, call_id } => {
                format!("orphan_output:{family}:{call_id}")
            }
        }
    }
}

struct IdentityFamily {
    name: &'static str,
    calls: BTreeMap<String, Vec<usize>>,
    outputs: BTreeMap<String, Vec<usize>>,
}

impl IdentityFamily {
    fn new(name: &'static str) -> Self {
        Self {
            name,
            calls: BTreeMap::new(),
            outputs: BTreeMap::new(),
        }
    }

    fn record_call(
        &mut self,
        index: usize,
        call_id: Option<&str>,
        issues: &mut Vec<CallResultIdentityIssue>,
    ) {
        let Some(call_id) = call_id.map(str::trim).filter(|call_id| !call_id.is_empty()) else {
            issues.push(CallResultIdentityIssue::MissingCallId {
                family: self.name,
                index,
            });
            return;
        };
        self.calls
            .entry(call_id.to_string())
            .or_default()
            .push(index);
    }

    fn record_output(
        &mut self,
        index: usize,
        call_id: &str,
        issues: &mut Vec<CallResultIdentityIssue>,
    ) {
        let call_id = call_id.trim();
        if call_id.is_empty() {
            issues.push(CallResultIdentityIssue::MissingOutputCallId {
                family: self.name,
                index,
            });
            return;
        }
        self.outputs
            .entry(call_id.to_string())
            .or_default()
            .push(index);
    }

    fn append_issues(&self, issues: &mut Vec<CallResultIdentityIssue>) {
        for (call_id, call_positions) in &self.calls {
            if call_positions.len() > 1 {
                issues.push(CallResultIdentityIssue::DuplicateCall {
                    family: self.name,
                    call_id: call_id.clone(),
                });
            }

            match self.outputs.get(call_id) {
                None => issues.push(CallResultIdentityIssue::MissingOutput {
                    family: self.name,
                    call_id: call_id.clone(),
                }),
                Some(output_positions) if output_positions.len() > 1 => {
                    issues.push(CallResultIdentityIssue::DuplicateOutput {
                        family: self.name,
                        call_id: call_id.clone(),
                    });
                }
                Some(output_positions)
                    if output_positions[0]
                        < *call_positions
                            .first()
                            .expect("call positions must be non-empty") =>
                {
                    issues.push(CallResultIdentityIssue::OutputPrecedesCall {
                        family: self.name,
                        call_id: call_id.clone(),
                    });
                }
                Some(_) => {}
            }
        }

        for call_id in self.outputs.keys() {
            if !self.calls.contains_key(call_id) {
                issues.push(CallResultIdentityIssue::OrphanOutput {
                    family: self.name,
                    call_id: call_id.clone(),
                });
            }
        }
    }
}

pub(super) fn call_result_identity_issues(
    items: &[ResponseItem],
) -> Vec<CallResultIdentityIssue> {
    let mut issues = Vec::new();
    let mut function = IdentityFamily::new("function");
    let mut custom = IdentityFamily::new("custom");

    for (index, item) in items.iter().enumerate() {
        match item {
            ResponseItem::FunctionCall { call_id, .. } => {
                function.record_call(index, Some(call_id), &mut issues);
            }
            ResponseItem::LocalShellCall { call_id, .. } => {
                function.record_call(index, call_id.as_deref(), &mut issues);
            }
            ResponseItem::FunctionCallOutput { call_id, .. } => {
                function.record_output(index, call_id, &mut issues);
            }
            ResponseItem::CustomToolCall { call_id, .. } => {
                custom.record_call(index, Some(call_id), &mut issues);
            }
            ResponseItem::CustomToolCallOutput { call_id, .. } => {
                custom.record_output(index, call_id, &mut issues);
            }
            _ => {}
        }
    }

    function.append_issues(&mut issues);
    custom.append_issues(&mut issues);
    issues.sort();
    issues.dedup();
    issues
}

/// Rejects compaction before prompt normalization can synthesize missing outputs
/// or remove orphaned outputs from the request projection.
///
/// Response history currently carries no durable effect annotation for function,
/// custom, or local-shell calls. The gate therefore treats ambiguity in every
/// such call family conservatively. Complete call/result pairs continue normally.
pub(crate) fn validate_compaction_call_result_identity(items: &[ResponseItem]) -> CodexResult<()> {
    let issues = call_result_identity_issues(items);
    if issues.is_empty() {
        return Ok(());
    }

    let details = issues
        .iter()
        .map(CallResultIdentityIssue::code)
        .collect::<Vec<_>>()
        .join(", ");
    Err(CodexErrorDetails::InvalidRequest(format!(
        "compaction blocked because tool call/result identity is ambiguous: {details}"
    ))
    .into())
}

#[cfg(test)]
#[path = "call_result_identity_tests.rs"]
mod tests;
'''


tests = r'''use super::*;
use codex_protocol::models::FunctionCallOutputPayload;
use codex_protocol::models::LocalShellAction;
use codex_protocol::models::LocalShellExecAction;
use codex_protocol::models::LocalShellStatus;

fn function_call(call_id: &str) -> ResponseItem {
    ResponseItem::FunctionCall {
        id: None,
        name: "set_marker".to_string(),
        namespace: None,
        arguments: "{}".to_string(),
        call_id: call_id.to_string(),
        internal_chat_message_metadata_passthrough: None,
    }
}

fn function_output(call_id: &str) -> ResponseItem {
    ResponseItem::FunctionCallOutput {
        id: None,
        call_id: call_id.to_string(),
        output: FunctionCallOutputPayload::from_text("marker=green".to_string()),
        internal_chat_message_metadata_passthrough: None,
    }
}

fn custom_call(call_id: &str) -> ResponseItem {
    ResponseItem::CustomToolCall {
        id: None,
        status: None,
        call_id: call_id.to_string(),
        name: "set_marker_custom".to_string(),
        namespace: None,
        input: "green".to_string(),
        internal_chat_message_metadata_passthrough: None,
    }
}

fn custom_output(call_id: &str) -> ResponseItem {
    ResponseItem::CustomToolCallOutput {
        id: None,
        call_id: call_id.to_string(),
        name: None,
        output: FunctionCallOutputPayload::from_text("marker=green".to_string()),
        internal_chat_message_metadata_passthrough: None,
    }
}

fn local_shell_call(call_id: Option<&str>) -> ResponseItem {
    ResponseItem::LocalShellCall {
        id: None,
        call_id: call_id.map(str::to_string),
        status: LocalShellStatus::Completed,
        action: LocalShellAction::Exec(LocalShellExecAction {
            command: vec!["printf".to_string(), "green".to_string()],
            timeout_ms: None,
            working_directory: None,
            env: None,
            user: None,
        }),
        internal_chat_message_metadata_passthrough: None,
    }
}

#[test]
fn complete_function_custom_and_shell_pairs_are_valid() {
    let items = vec![
        function_call("function-1"),
        function_output("function-1"),
        custom_call("custom-1"),
        custom_output("custom-1"),
        local_shell_call(Some("shell-1")),
        function_output("shell-1"),
    ];

    assert_eq!(call_result_identity_issues(&items), Vec::new());
    assert_eq!(validate_compaction_call_result_identity(&items), Ok(()));
}

#[test]
fn missing_output_is_reported_before_prompt_repair() {
    assert_eq!(
        call_result_identity_issues(&[function_call("call-1")]),
        vec![CallResultIdentityIssue::MissingOutput {
            family: "function",
            call_id: "call-1".to_string(),
        }]
    );
}

#[test]
fn duplicate_output_is_reported() {
    assert_eq!(
        call_result_identity_issues(&[
            function_call("call-1"),
            function_output("call-1"),
            function_output("call-1"),
        ]),
        vec![CallResultIdentityIssue::DuplicateOutput {
            family: "function",
            call_id: "call-1".to_string(),
        }]
    );
}

#[test]
fn output_before_call_is_reported() {
    assert_eq!(
        call_result_identity_issues(&[
            custom_output("call-1"),
            custom_call("call-1"),
        ]),
        vec![CallResultIdentityIssue::OutputPrecedesCall {
            family: "custom",
            call_id: "call-1".to_string(),
        }]
    );
}

#[test]
fn orphan_output_is_reported() {
    assert_eq!(
        call_result_identity_issues(&[function_output("call-1")]),
        vec![CallResultIdentityIssue::OrphanOutput {
            family: "function",
            call_id: "call-1".to_string(),
        }]
    );
}

#[test]
fn duplicate_call_id_is_reported() {
    assert_eq!(
        call_result_identity_issues(&[
            function_call("call-1"),
            function_call("call-1"),
            function_output("call-1"),
        ]),
        vec![CallResultIdentityIssue::DuplicateCall {
            family: "function",
            call_id: "call-1".to_string(),
        }]
    );
}

#[test]
fn missing_local_shell_call_id_is_reported() {
    assert_eq!(
        call_result_identity_issues(&[local_shell_call(None)]),
        vec![CallResultIdentityIssue::MissingCallId {
            family: "function",
            index: 0,
        }]
    );
}

#[test]
fn validation_returns_stable_invalid_request_message() {
    let error = validate_compaction_call_result_identity(&[function_call("call-1")])
        .expect_err("missing output should block compaction");

    assert_eq!(
        error.to_string(),
        "compaction blocked because tool call/result identity is ambiguous: missing_output:function:call-1"
    );
}
'''

(CORE / "context_manager" / "call_result_identity.rs").write_text(module, encoding="utf-8")
(CORE / "context_manager" / "call_result_identity_tests.rs").write_text(tests, encoding="utf-8")

replace_exact(
    CORE / "context_manager" / "mod.rs",
    "mod history;\nmod normalize;\n",
    "mod call_result_identity;\nmod history;\nmod normalize;\n",
)
replace_exact(
    CORE / "context_manager" / "mod.rs",
    "pub(crate) use history::ContextManager;\n",
    "pub(crate) use call_result_identity::validate_compaction_call_result_identity;\npub(crate) use history::ContextManager;\n",
)

replace_exact(
    CORE / "compact.rs",
    "use crate::context::world_state::WorldState;\n",
    "use crate::context::world_state::WorldState;\nuse crate::context_manager::validate_compaction_call_result_identity;\n",
)
replace_exact(
    CORE / "compact.rs",
    "    loop {\n        // Clone is required because of the loop\n",
    "    loop {\n        validate_compaction_call_result_identity(history.raw_items())?;\n        // Clone is required because of the loop\n",
)

replace_exact(
    CORE / "compact_remote_request.rs",
    "use crate::compact::CompactionAnalyticsDetails;\n",
    "use crate::compact::CompactionAnalyticsDetails;\nuse crate::context_manager::validate_compaction_call_result_identity;\n",
)
replace_exact(
    CORE / "compact_remote_request.rs",
    "    let prompt_input = history.for_prompt(&turn_context.model_info.input_modalities);\n",
    "    validate_compaction_call_result_identity(history.raw_items())?;\n    let prompt_input = history.for_prompt(&turn_context.model_info.input_modalities);\n",
)

replace_exact(
    CORE / "compact_remote_v2_attempt.rs",
    "use crate::compact_remote::trim_function_call_history_to_fit_context_window;\n",
    "use crate::compact_remote::trim_function_call_history_to_fit_context_window;\nuse crate::context_manager::validate_compaction_call_result_identity;\n",
)
replace_exact(
    CORE / "compact_remote_v2_attempt.rs",
    "    let mut input = history.for_prompt(&turn_context.model_info.input_modalities);\n",
    "    validate_compaction_call_result_identity(history.raw_items())?;\n    let mut input = history.for_prompt(&turn_context.model_info.input_modalities);\n",
)
