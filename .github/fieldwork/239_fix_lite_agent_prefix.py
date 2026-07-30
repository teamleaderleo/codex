#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().parents[2] / "codex-rs" / "core" / "tests" / "suite" / "agent_websocket.rs"
text = path.read_text(encoding="utf-8")
old = '''    assert_eq!(generated["input"], warmup["input"]);
    assert_eq!(generated["model"], warmup["model"]);
'''
new = '''    let warmup_input = warmup["input"]
        .as_array()
        .expect("warmup input should be an array");
    let generated_input = generated["input"]
        .as_array()
        .expect("generated input should be an array");
    assert!(
        generated_input.starts_with(warmup_input),
        "generated turn must preserve the exact Responses Lite manifest/instruction prefix"
    );
    let generated_suffix = &generated_input[warmup_input.len()..];
    assert!(
        generated_suffix.iter().any(|item| {
            item.get("role").and_then(serde_json::Value::as_str) == Some("user")
        }),
        "generated turn should append the submitted user message after the exact prewarm prefix"
    );
    assert_eq!(generated["model"], warmup["model"]);
'''
count = text.count(old)
if count != 1:
    raise SystemExit(f"agent prefix assertion: expected one exact match, found {count}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
