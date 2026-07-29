use super::CompactionIdentityDefectKind;
use super::compaction_identity_defects;
use super::validate_compaction_call_output_identity;
use codex_protocol::models::FunctionCallOutputPayload;
use codex_protocol::models::ResponseItem;

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
        output: FunctionCallOutputPayload::from_text("ok".to_string()),
        internal_chat_message_metadata_passthrough: None,
    }
}

fn custom_call(call_id: &str) -> ResponseItem {
    ResponseItem::CustomToolCall {
        id: None,
        status: Some("completed".to_string()),
        call_id: call_id.to_string(),
        name: "apply_patch".to_string(),
        namespace: None,
        input: "*** Begin Patch\n*** End Patch".to_string(),
        internal_chat_message_metadata_passthrough: None,
    }
}

fn custom_output(call_id: &str) -> ResponseItem {
    ResponseItem::CustomToolCallOutput {
        id: None,
        call_id: call_id.to_string(),
        name: Some("apply_patch".to_string()),
        output: FunctionCallOutputPayload::from_text("done".to_string()),
        internal_chat_message_metadata_passthrough: None,
    }
}

#[test]
fn accepts_complete_function_and_custom_pairs() {
    let items = vec![
        function_call("call-1"),
        function_output("call-1"),
        custom_call("call-2"),
        custom_output("call-2"),
    ];

    assert!(validate_compaction_call_output_identity(&items).is_ok());
    assert_eq!(compaction_identity_defects(&items), Vec::new());
}

#[test]
fn rejects_missing_output() {
    let defects = compaction_identity_defects(&[function_call("call-secret")]);

    assert_eq!(defects.len(), 1);
    assert_eq!(defects[0].kind, CompactionIdentityDefectKind::MissingOutput);
}

#[test]
fn rejects_duplicate_output() {
    let defects = compaction_identity_defects(&[
        function_call("call-1"),
        function_output("call-1"),
        function_output("call-1"),
    ]);

    assert_eq!(defects.len(), 1);
    assert_eq!(
        defects[0].kind,
        CompactionIdentityDefectKind::DuplicateOutput
    );
}

#[test]
fn rejects_duplicate_call() {
    let defects = compaction_identity_defects(&[
        function_call("call-1"),
        function_call("call-1"),
        function_output("call-1"),
    ]);

    assert_eq!(defects.len(), 1);
    assert_eq!(defects[0].kind, CompactionIdentityDefectKind::DuplicateCall);
}

#[test]
fn rejects_output_before_call() {
    let defects =
        compaction_identity_defects(&[function_output("call-1"), function_call("call-1")]);

    assert_eq!(defects.len(), 1);
    assert_eq!(
        defects[0].kind,
        CompactionIdentityDefectKind::OutputBeforeCall
    );
}

#[test]
fn rejects_orphan_output() {
    let defects = compaction_identity_defects(&[function_output("call-1")]);

    assert_eq!(defects.len(), 1);
    assert_eq!(defects[0].kind, CompactionIdentityDefectKind::OrphanOutput);
}

#[test]
fn public_error_does_not_include_call_id() {
    let error = validate_compaction_call_output_identity(&[function_call("private-call-id")])
        .expect_err("missing output must reject compaction");
    let message = error.to_string();

    assert!(message.contains("missing_output=1"));
    assert!(!message.contains("private-call-id"));
}
