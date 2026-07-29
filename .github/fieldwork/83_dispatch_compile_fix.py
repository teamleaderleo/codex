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
    CORE / "tools" / "registry.rs",
    "use crate::tools::context::ToolPayload;\n",
    "use crate::tools::context::ToolPayload;\nuse crate::tools::context::ToolCallSource;\n",
)
replace_exact(
    CORE / "tools" / "lifecycle.rs",
    "            ToolCallOutcome::Aborted => ToolOperationTerminalState::Aborted,\n            _ => ToolOperationTerminalState::Ambiguous,\n",
    "            ToolCallOutcome::Aborted => ToolOperationTerminalState::Aborted,\n",
)
