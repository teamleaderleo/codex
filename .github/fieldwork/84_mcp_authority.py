from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 anchor, found {count}")
    return text.replace(old, new)


handler = Path("codex-rs/core/src/tools/handlers/mcp.rs")
text = handler.read_text(encoding="utf-8")
text = replace_once(
    text,
    """            call_id.clone(),
            self.tool_info.server_name.clone(),
            self.tool_info.tool.name.to_string(),
            self.hook_tool_name(),
""",
    """            call_id.clone(),
            self.tool_info.clone(),
            self.hook_tool_name(),
""",
    "handler call",
)
handler.write_text(text, encoding="utf-8")

call = Path("codex-rs/core/src/mcp_tool_call.rs")
text = call.read_text(encoding="utf-8")
text = replace_once(
    text,
    "use codex_mcp::PreparedMcpCall;\n",
    "use codex_mcp::PreparedMcpCall;\nuse codex_mcp::ToolInfo;\n",
    "ToolInfo import",
)
text = replace_once(
    text,
    """    call_id: String,
    server: String,
    tool_name: String,
    hook_tool_name: HookToolName,
""",
    """    call_id: String,
    advertised_tool: ToolInfo,
    hook_tool_name: HookToolName,
""",
    "call signature",
)
text = replace_once(
    text,
    """    let turn_context = &step_context.turn;
    // Parse the `arguments` as JSON. An empty string is OK, but invalid JSON
""",
    """    let turn_context = &step_context.turn;
    let server = advertised_tool.server_name.clone();
    let tool_name = advertised_tool.tool.name.to_string();
    // Parse the `arguments` as JSON. An empty string is OK, but invalid JSON
""",
    "turn context",
)
text = replace_once(
    text,
    """/// Handles the specified tool call and dispatches the appropriate MCP tool-call
/// item lifecycle events to the `Session`.
""",
    """fn mcp_tool_authority_matches(advertised: &ToolInfo, live: &ToolInfo) -> bool {
    match (
        serde_json::to_value(advertised),
        serde_json::to_value(live),
    ) {
        (Ok(advertised), Ok(live)) => advertised == live,
        _ => false,
    }
}

/// Handles the specified tool call and dispatches the appropriate MCP tool-call
/// item lifecycle events to the `Session`.
""",
    "authority helper",
)
text = replace_once(
    text,
    """    let metadata = mcp_tool_metadata(&prepared_call);
""",
    """    if !mcp_tool_authority_matches(&advertised_tool, prepared_call.tool_info()) {
        let item_metadata =
            McpToolCallItemMetadata::from_tool_metadata(&server, /*metadata*/ None);
        let result = notify_mcp_tool_call_skip(
            sess.as_ref(),
            turn_context.as_ref(),
            &call_id,
            invocation,
            item_metadata,
            format!(
                "MCP tool `{server}/{tool_name}` blocked because its live authority differs from the model-advertised catalogue"
            ),
            /*already_started*/ false,
        )
        .await;
        return HandledMcpToolCall {
            result: CallToolResult::from_result(result),
            tool_input: arguments_value
                .unwrap_or_else(|| JsonValue::Object(serde_json::Map::new())),
        };
    }

    let metadata = mcp_tool_metadata(&prepared_call);
""",
    "authority gate",
)
call.write_text(text, encoding="utf-8")

tests = Path("codex-rs/core/src/mcp_tool_call_tests.rs")
text = tests.read_text(encoding="utf-8")
if "fn mcp_tool_authority_accepts_identical_advertisement()" in text:
    raise SystemExit("authority tests already present")
text += r'''

fn authority_test_tool(schema: serde_json::Value) -> ToolInfo {
    ToolInfo {
        server_name: "authority-server".to_string(),
        supports_parallel_tool_calls: false,
        server_origin: Some("stdio".to_string()),
        callable_name: "echo".to_string(),
        callable_namespace: "mcp__authority_server".to_string(),
        namespace_description: Some("Authority fixture".to_string()),
        tool: rmcp::model::Tool::new(
            "echo".to_string(),
            "Echo input".to_string(),
            Arc::new(
                schema
                    .as_object()
                    .expect("authority test schema object")
                    .clone(),
            ),
        ),
        openai_file_input_optional_fields: HashMap::new(),
        connector_id: Some("connector-a".to_string()),
        connector_name: Some("Connector A".to_string()),
        plugin_display_names: vec!["Plugin A".to_string()],
    }
}

#[test]
fn mcp_tool_authority_accepts_identical_advertisement() {
    let advertised = authority_test_tool(serde_json::json!({
        "type": "object",
        "properties": {"message": {"type": "string"}}
    }));
    let live = advertised.clone();

    assert!(mcp_tool_authority_matches(&advertised, &live));
}

#[test]
fn mcp_tool_authority_rejects_schema_and_connector_drift() {
    let advertised = authority_test_tool(serde_json::json!({
        "type": "object",
        "properties": {"message": {"type": "string"}}
    }));
    let mut schema_drift = advertised.clone();
    schema_drift.tool = rmcp::model::Tool::new(
        "echo".to_string(),
        "Echo input".to_string(),
        Arc::new(
            serde_json::json!({
                "type": "object",
                "properties": {"count": {"type": "integer"}}
            })
            .as_object()
            .expect("schema drift object")
            .clone(),
        ),
    );
    let mut connector_drift = advertised.clone();
    connector_drift.connector_id = Some("connector-b".to_string());

    assert!(!mcp_tool_authority_matches(&advertised, &schema_drift));
    assert!(!mcp_tool_authority_matches(
        &advertised,
        &connector_drift
    ));
}
'''
tests.write_text(text, encoding="utf-8")
