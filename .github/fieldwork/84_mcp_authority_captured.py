from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 anchor, found {count}")
    return text.replace(old, new)


# Define a deliberate callable-authority comparison in codex-mcp.
tools_path = Path("codex-rs/codex-mcp/src/tools.rs")
tools = tools_path.read_text(encoding="utf-8")
old_impl = '''impl ToolInfo {
    pub fn canonical_tool_name(&self) -> ToolName {
        ToolName::namespaced(self.callable_namespace.clone(), self.callable_name.clone())
    }
}
'''
new_impl = '''impl ToolInfo {
    pub fn canonical_tool_name(&self) -> ToolName {
        ToolName::namespaced(self.callable_namespace.clone(), self.callable_name.clone())
    }

    /// Returns whether two advertised definitions carry the same executable
    /// authority. Presentation, telemetry, scheduling, and the deliberately
    /// weakened cached read-only hint are excluded.
    pub fn has_same_callable_authority_as(&self, other: &Self) -> bool {
        self.callable_authority_value() == other.callable_authority_value()
    }

    fn callable_authority_value(&self) -> serde_json::Value {
        let annotations = self.tool.annotations.as_ref();
        serde_json::json!({
            "server_name": self.server_name,
            "callable_namespace": self.callable_namespace,
            "callable_name": self.callable_name,
            "raw_tool_name": self.tool.name,
            "input_schema": self.tool.input_schema,
            "output_schema": self.tool.output_schema,
            "destructive_hint": annotations.and_then(|value| value.destructive_hint),
            "idempotent_hint": annotations.and_then(|value| value.idempotent_hint),
            "open_world_hint": annotations.and_then(|value| value.open_world_hint),
            "connector_id": self.connector_id,
            "openai_file_input_optional_fields": self.openai_file_input_optional_fields,
            "execution_metadata": self.tool.meta,
        })
    }
}

#[cfg(test)]
#[path = "tools_tests.rs"]
mod tests;
'''
tools = replace_once(tools, old_impl, new_impl, "ToolInfo authority implementation")
tools_path.write_text(tools, encoding="utf-8")

Path("codex-rs/codex-mcp/src/tools_tests.rs").write_text(
    '''use std::collections::HashMap;
use std::sync::Arc;

use rmcp::model::JsonObject;
use rmcp::model::MetaObject;
use rmcp::model::Tool;
use rmcp::model::ToolAnnotations;
use serde_json::json;

use super::ToolInfo;

fn schema(properties: serde_json::Value) -> Arc<JsonObject> {
    Arc::new(
        serde_json::from_value(json!({
            "type": "object",
            "properties": properties,
            "additionalProperties": false
        }))
        .expect("test schema"),
    )
}

fn tool_info() -> ToolInfo {
    let mut tool = Tool::new(
        "search".to_string(),
        "Search the current catalogue.".to_string(),
        schema(json!({"query": {"type": "string"}})),
    );
    tool.title = Some("Search".to_string());
    tool.output_schema = Some(schema(json!({"results": {"type": "array"}})));
    tool.annotations = Some(ToolAnnotations::from_raw(
        /*title*/ None,
        /*read_only_hint*/ None,
        /*destructive_hint*/ Some(false),
        /*idempotent_hint*/ Some(true),
        /*open_world_hint*/ Some(false),
    ));
    let mut meta = MetaObject::new();
    meta.insert("link_id".to_string(), json!("link-one"));
    tool.meta = Some(meta);

    ToolInfo {
        server_name: "docs".to_string(),
        supports_parallel_tool_calls: false,
        server_origin: Some("stdio".to_string()),
        callable_name: "search".to_string(),
        callable_namespace: "mcp__docs".to_string(),
        namespace_description: Some("Documentation tools".to_string()),
        tool,
        openai_file_input_optional_fields: HashMap::from([(
            "attachment".to_string(),
            vec!["filename".to_string()],
        )]),
        connector_id: Some("connector-one".to_string()),
        connector_name: Some("Docs".to_string()),
        plugin_display_names: vec!["Documentation".to_string()],
    }
}

#[test]
fn callable_authority_allows_descriptive_and_cached_read_only_drift() {
    let advertised = tool_info();
    let mut live = advertised.clone();
    live.supports_parallel_tool_calls = true;
    live.server_origin = Some("https://live.example/mcp".to_string());
    live.namespace_description = Some("Current documentation tools".to_string());
    live.connector_name = Some("Docs Live".to_string());
    live.plugin_display_names = vec!["Current Documentation".to_string()];
    live.tool.title = Some("Search live docs".to_string());
    live.tool.description = Some("Search the live catalogue.".to_string().into());
    live.tool.annotations = Some(ToolAnnotations::from_raw(
        /*title*/ Some("Live search".to_string()),
        /*read_only_hint*/ Some(true),
        /*destructive_hint*/ Some(false),
        /*idempotent_hint*/ Some(true),
        /*open_world_hint*/ Some(false),
    ));

    assert!(advertised.has_same_callable_authority_as(&live));
}

#[test]
fn callable_authority_rejects_schema_and_execution_metadata_drift() {
    let advertised = tool_info();

    let mut changed = advertised.clone();
    changed.tool.input_schema = schema(json!({"count": {"type": "integer"}}));
    assert!(!advertised.has_same_callable_authority_as(&changed));

    let mut changed = advertised.clone();
    changed.tool.output_schema = Some(schema(json!({"count": {"type": "integer"}})));
    assert!(!advertised.has_same_callable_authority_as(&changed));

    let mut changed = advertised.clone();
    changed.tool.annotations = Some(ToolAnnotations::from_raw(
        /*title*/ None,
        /*read_only_hint*/ None,
        /*destructive_hint*/ Some(true),
        /*idempotent_hint*/ Some(false),
        /*open_world_hint*/ Some(true),
    ));
    assert!(!advertised.has_same_callable_authority_as(&changed));

    let mut changed = advertised.clone();
    changed.connector_id = Some("connector-two".to_string());
    assert!(!advertised.has_same_callable_authority_as(&changed));

    let mut changed = advertised.clone();
    changed.openai_file_input_optional_fields.insert(
        "attachment".to_string(),
        vec!["filename".to_string(), "mime_type".to_string()],
    );
    assert!(!advertised.has_same_callable_authority_as(&changed));

    let mut changed = advertised.clone();
    changed
        .tool
        .meta
        .as_mut()
        .expect("test meta")
        .insert("connected_account_email".to_string(), json!("other@example.com"));
    assert!(!advertised.has_same_callable_authority_as(&changed));
}
''',
    encoding="utf-8",
)

# Carry the exact advertised ToolInfo into the call path.
handler_path = Path("codex-rs/core/src/tools/handlers/mcp.rs")
handler = handler_path.read_text(encoding="utf-8")
handler = replace_once(
    handler,
    '''            call_id.clone(),
            self.tool_info.server_name.clone(),
            self.tool_info.tool.name.to_string(),
            self.hook_tool_name(),
''',
    '''            call_id.clone(),
            self.tool_info.clone(),
            self.hook_tool_name(),
''',
    "MCP handler advertised authority",
)
handler_path.write_text(handler, encoding="utf-8")

call_path = Path("codex-rs/core/src/mcp_tool_call.rs")
call = call_path.read_text(encoding="utf-8")
call = replace_once(
    call,
    "use codex_mcp::PreparedMcpCall;\n",
    "use codex_mcp::PreparedMcpCall;\nuse codex_mcp::ToolInfo;\n",
    "ToolInfo import",
)
call = replace_once(
    call,
    '''    call_id: String,
    server: String,
    tool_name: String,
    hook_tool_name: HookToolName,
''',
    '''    call_id: String,
    advertised_tool: ToolInfo,
    hook_tool_name: HookToolName,
''',
    "call authority parameters",
)
call = replace_once(
    call,
    '''    let turn_context = &step_context.turn;
    // Parse the `arguments` as JSON. An empty string is OK, but invalid JSON
''',
    '''    let turn_context = &step_context.turn;
    let server = advertised_tool.server_name.clone();
    let tool_name = advertised_tool.tool.name.to_string();
    // Parse the `arguments` as JSON. An empty string is OK, but invalid JSON
''',
    "call authority identity",
)
old_selection = '''    sess.refresh_mcp_if_dirty().await;
    let current_binding = sess
        .services
        .mcp_runtime
        .current_binding_for_call(&server)
        .await;
    let Some(prepared_call) = current_binding
        .as_ref()
        .and_then(|binding| binding.prepare_call(&server, &tool_name))
    else {
        let item_metadata =
            McpToolCallItemMetadata::from_tool_metadata(&server, /*metadata*/ None);
        let result = notify_mcp_tool_call_skip(
            sess.as_ref(),
            turn_context.as_ref(),
            &call_id,
            invocation,
            item_metadata,
            format!("MCP tool `{server}/{tool_name}` is not available to the model"),
            /*already_started*/ false,
        )
        .await;
        return HandledMcpToolCall {
            result: CallToolResult::from_result(result),
            tool_input: arguments_value
                .unwrap_or_else(|| JsonValue::Object(serde_json::Map::new())),
        };
    };
'''
new_selection = '''    let prepared_call = if let Some(prepared_call) =
        step_context.mcp.prepare_call(&server, &tool_name)
    {
        prepared_call
    } else {
        // Cached definitions can be advertised before startup and therefore do
        // not carry a prepared call. Only that path may bind to the live runtime.
        sess.refresh_mcp_if_dirty().await;
        let current_binding = sess
            .services
            .mcp_runtime
            .current_binding_for_call(&server)
            .await;
        let Some(prepared_call) = current_binding
            .as_ref()
            .and_then(|binding| binding.prepare_call(&server, &tool_name))
        else {
            let item_metadata =
                McpToolCallItemMetadata::from_tool_metadata(&server, /*metadata*/ None);
            let result = notify_mcp_tool_call_skip(
                sess.as_ref(),
                turn_context.as_ref(),
                &call_id,
                invocation,
                item_metadata,
                format!("MCP tool `{server}/{tool_name}` is not available to the model"),
                /*already_started*/ false,
            )
            .await;
            return HandledMcpToolCall {
                result: CallToolResult::from_result(result),
                tool_input: arguments_value
                    .unwrap_or_else(|| JsonValue::Object(serde_json::Map::new())),
            };
        };
        if !advertised_tool.has_same_callable_authority_as(prepared_call.tool_info()) {
            let item_metadata =
                McpToolCallItemMetadata::from_tool_metadata(&server, /*metadata*/ None);
            let result = notify_mcp_tool_call_skip(
                sess.as_ref(),
                turn_context.as_ref(),
                &call_id,
                invocation,
                item_metadata,
                format!(
                    "MCP tool `{server}/{tool_name}` changed after it was advertised to the model"
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
        prepared_call
    };
'''
call = replace_once(call, old_selection, new_selection, "captured-first call selection")
call_path.write_text(call, encoding="utf-8")
