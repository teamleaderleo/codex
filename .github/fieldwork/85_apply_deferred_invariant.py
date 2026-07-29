#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "codex-rs" / "core" / "src"
SPEC_PLAN = CORE / "tools" / "spec_plan.rs"
TESTS = CORE / "tools" / "spec_plan_tests.rs"


def replace_exact(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one match in {path}: found {count} for {old!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


replace_exact(
    SPEC_PLAN,
    "    add_tool_sources(&context, &mut planned_tools);\n    apply_direct_model_only_namespace_overrides(turn_context, &mut planned_tools);\n    append_tool_search_executor(&context, &mut planned_tools);\n",
    "    add_tool_sources(&context, &mut planned_tools);\n    apply_direct_model_only_namespace_overrides(turn_context, &mut planned_tools);\n    normalize_unloadable_deferred_tools(turn_context, &mut planned_tools);\n    append_tool_search_executor(&context, &mut planned_tools);\n",
)

replace_exact(
    SPEC_PLAN,
    "fn apply_direct_model_only_namespace_overrides(\n    turn_context: &TurnContext,\n    planned_tools: &mut PlannedTools,\n) {\n",
    "fn normalize_unloadable_deferred_tools(\n    turn_context: &TurnContext,\n    planned_tools: &mut PlannedTools,\n) {\n    if matches!(\n        effective_tool_mode(turn_context),\n        ToolMode::CodeMode | ToolMode::CodeModeOnly\n    ) {\n        return;\n    }\n\n    let search_enabled = search_tool_enabled(turn_context);\n    for runtime in &mut planned_tools.runtimes {\n        if runtime.exposure() != ToolExposure::Deferred {\n            continue;\n        }\n\n        let has_executable_loader = search_enabled && runtime.search_info().is_some();\n        if !has_executable_loader {\n            *runtime = override_tool_exposure(Arc::clone(runtime), ToolExposure::Direct);\n        }\n    }\n}\n\nfn apply_direct_model_only_namespace_overrides(\n    turn_context: &TurnContext,\n    planned_tools: &mut PlannedTools,\n) {\n",
)

replace_exact(
    TESTS,
    "use crate::session::turn_context::TurnContext;\n",
    "use crate::session::turn_context::TurnContext;\nuse crate::tools::context::ToolInvocation;\n",
)

replace_exact(
    TESTS,
    "impl ToolExecutor<ExtensionToolCall> for DeferredExtensionTool {\n    fn tool_name(&self) -> ToolName {\n        ToolName::plain(\"extension_echo\")\n    }\n\n    fn spec(&self) -> ToolSpec {\n        ToolSpec::Function(ResponsesApiTool {\n            name: \"extension_echo\".to_string(),\n            description: \"Echoes arguments through an extension tool.\".to_string(),\n            strict: true,\n            defer_loading: None,\n            parameters: codex_tools::JsonSchema::object(\n                BTreeMap::from([(\n                    \"message\".to_string(),\n                    codex_tools::JsonSchema::string(/*description*/ None),\n                )]),\n                Some(vec![\"message\".to_string()]),\n                Some(false.into()),\n            ),\n            output_schema: None,\n        })\n    }\n\n    fn exposure(&self) -> ToolExposure {\n        ToolExposure::Deferred\n    }\n\n    fn handle(&self, _call: ExtensionToolCall) -> codex_tools::ToolExecutorFuture<'_> {\n        Box::pin(async { panic!(\"spec planning should not execute extension tools\") })\n    }\n}\n\nfn duplicate_primary_environment(turn: &mut TurnContext) {\n",
    "impl ToolExecutor<ExtensionToolCall> for DeferredExtensionTool {\n    fn tool_name(&self) -> ToolName {\n        ToolName::plain(\"extension_echo\")\n    }\n\n    fn spec(&self) -> ToolSpec {\n        ToolSpec::Function(ResponsesApiTool {\n            name: \"extension_echo\".to_string(),\n            description: \"Echoes arguments through an extension tool.\".to_string(),\n            strict: true,\n            defer_loading: None,\n            parameters: codex_tools::JsonSchema::object(\n                BTreeMap::from([(\n                    \"message\".to_string(),\n                    codex_tools::JsonSchema::string(/*description*/ None),\n                )]),\n                Some(vec![\"message\".to_string()]),\n                Some(false.into()),\n            ),\n            output_schema: None,\n        })\n    }\n\n    fn exposure(&self) -> ToolExposure {\n        ToolExposure::Deferred\n    }\n\n    fn handle(&self, _call: ExtensionToolCall) -> codex_tools::ToolExecutorFuture<'_> {\n        Box::pin(async { panic!(\"spec planning should not execute extension tools\") })\n    }\n}\n\nstruct DeferredCoreToolWithoutSearchInfo;\n\nimpl ToolExecutor<ToolInvocation> for DeferredCoreToolWithoutSearchInfo {\n    fn tool_name(&self) -> ToolName {\n        ToolName::plain(\"unsearchable_deferred\")\n    }\n\n    fn spec(&self) -> ToolSpec {\n        ToolSpec::Function(ResponsesApiTool {\n            name: \"unsearchable_deferred\".to_string(),\n            description: \"Deferred test tool without searchable metadata.\".to_string(),\n            strict: true,\n            defer_loading: None,\n            parameters: codex_tools::JsonSchema::default(),\n            output_schema: None,\n        })\n    }\n\n    fn exposure(&self) -> ToolExposure {\n        ToolExposure::Deferred\n    }\n\n    fn search_info(&self) -> Option<codex_tools::ToolSearchInfo> {\n        None\n    }\n\n    fn handle(&self, _invocation: ToolInvocation) -> codex_tools::ToolExecutorFuture<'_> {\n        Box::pin(async { panic!(\"spec planning should not execute core tools\") })\n    }\n}\n\nimpl CoreToolRuntime for DeferredCoreToolWithoutSearchInfo {}\n\nfn duplicate_primary_environment(turn: &mut TurnContext) {\n",
)

replace_exact(
    TESTS,
    "    missing_model_capability.assert_visible_lacks(&[\"tool_search\"]);\n\n    let missing_deferred_tools = probe(|turn| {\n",
    "    missing_model_capability.assert_visible_lacks(&[\"tool_search\"]);\n    assert_eq!(\n        missing_model_capability.namespace_function_names(\"mcp__searchable\"),\n        &[\"lookup\".to_string()]\n    );\n    assert_eq!(\n        missing_model_capability.exposure(\n            &ToolName::namespaced(\"mcp__searchable\", \"lookup\").to_string()\n        ),\n        ToolExposure::Direct\n    );\n\n    let missing_deferred_tools = probe(|turn| {\n",
)

replace_exact(
    TESTS,
    "    enabled.assert_registered_contains(&[\n        \"tool_search\",\n        &ToolName::namespaced(\"mcp__searchable\", \"lookup\").to_string(),\n    ]);\n}\n\n#[tokio::test]\nasync fn deferred_extension_tools_are_discoverable_with_tool_search() {\n",
    "    enabled.assert_registered_contains(&[\n        \"tool_search\",\n        &ToolName::namespaced(\"mcp__searchable\", \"lookup\").to_string(),\n    ]);\n    assert_eq!(\n        enabled.exposure(&ToolName::namespaced(\"mcp__searchable\", \"lookup\").to_string()),\n        ToolExposure::Deferred\n    );\n}\n\n#[tokio::test]\nasync fn deferred_extension_is_direct_when_search_is_unavailable() {\n    let plan = probe_with(\n        |turn| {\n            set_feature(turn, Feature::Collab, /*enabled*/ false);\n            turn.model_info.supports_search_tool = false;\n        },\n        ToolPlanInputs {\n            extension_tool_executors: vec![Arc::new(DeferredExtensionTool)],\n            ..ToolPlanInputs::default()\n        },\n    )\n    .await;\n\n    plan.assert_visible_contains(&[\"extension_echo\"]);\n    plan.assert_visible_lacks(&[\"tool_search\"]);\n    assert_eq!(plan.exposure(\"extension_echo\"), ToolExposure::Direct);\n}\n\n#[tokio::test]\nasync fn deferred_dynamic_tool_is_direct_when_search_is_unavailable() {\n    let plan = probe_with(\n        |turn| {\n            set_feature(turn, Feature::Collab, /*enabled*/ false);\n            turn.model_info.supports_search_tool = false;\n        },\n        ToolPlanInputs {\n            dynamic_tools: vec![dynamic_tool(\n                Some(\"host_dynamic\"),\n                \"lookup\",\n                /*defer_loading*/ true,\n            )],\n            ..ToolPlanInputs::default()\n        },\n    )\n    .await;\n\n    assert_eq!(\n        plan.namespace_function_names(\"host_dynamic\"),\n        &[\"lookup\".to_string()]\n    );\n    plan.assert_visible_lacks(&[\"tool_search\"]);\n    assert_eq!(\n        plan.exposure(&ToolName::namespaced(\"host_dynamic\", \"lookup\").to_string()),\n        ToolExposure::Direct\n    );\n}\n\n#[tokio::test]\nasync fn deferred_runtime_without_search_metadata_is_direct() {\n    let plan = probe_with(\n        |turn| {\n            set_feature(turn, Feature::Collab, /*enabled*/ false);\n            turn.model_info.supports_search_tool = true;\n        },\n        ToolPlanInputs {\n            tool_runtimes: vec![Arc::new(DeferredCoreToolWithoutSearchInfo)],\n            ..ToolPlanInputs::default()\n        },\n    )\n    .await;\n\n    plan.assert_visible_contains(&[\"unsearchable_deferred\"]);\n    plan.assert_visible_lacks(&[\"tool_search\"]);\n    assert_eq!(\n        plan.exposure(\"unsearchable_deferred\"),\n        ToolExposure::Direct\n    );\n}\n\n#[tokio::test]\nasync fn code_mode_keeps_unsearchable_deferred_runtime_registered() {\n    let plan = probe_with(\n        |turn| {\n            set_feature(turn, Feature::CodeMode, /*enabled*/ true);\n            turn.model_info.tool_mode = Some(ToolMode::CodeMode);\n            turn.model_info.supports_search_tool = true;\n        },\n        ToolPlanInputs {\n            tool_runtimes: vec![Arc::new(DeferredCoreToolWithoutSearchInfo)],\n            ..ToolPlanInputs::default()\n        },\n    )\n    .await;\n\n    plan.assert_visible_contains(&[codex_code_mode::PUBLIC_TOOL_NAME]);\n    plan.assert_visible_lacks(&[\"unsearchable_deferred\", \"tool_search\"]);\n    plan.assert_registered_contains(&[\"unsearchable_deferred\"]);\n    assert_eq!(\n        plan.exposure(\"unsearchable_deferred\"),\n        ToolExposure::Deferred\n    );\n}\n\n#[tokio::test]\nasync fn deferred_extension_tools_are_discoverable_with_tool_search() {\n",
)
