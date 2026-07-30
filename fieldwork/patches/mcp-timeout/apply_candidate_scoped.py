#!/usr/bin/env python3
from __future__ import annotations

import runpy
import sys
import tempfile
from pathlib import Path

SOURCE = Path(__file__).with_name("apply_candidate.py")
CALL_TOOL = '    pub async fn call_tool(\n'
OLD_SELECTOR = "    start = text.index(START)\n"
NEW_SELECTOR = (
    "    call_tool = text.index(CALL_TOOL)\n"
    "    start = text.index(START, call_tool)\n"
)


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    if source.count(OLD_SELECTOR) != 2:
        raise SystemExit(
            "expected exactly two unscoped candidate selectors in apply_candidate.py"
        )
    if "CALL_TOOL =" in source:
        raise SystemExit("apply_candidate.py already contains a call_tool selector")

    patched = source.replace(
        'START = "        let requested_modern = self.protocol_mode == McpProtocolMode::V20260728;\\n"\n',
        'CALL_TOOL = "    pub async fn call_tool(\\n"\n'
        'START = "        let requested_modern = self.protocol_mode == McpProtocolMode::V20260728;\\n"\n',
        1,
    ).replace(OLD_SELECTOR, NEW_SELECTOR)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".py",
        delete=False,
    ) as handle:
        handle.write(patched)
        patched_path = Path(handle.name)

    try:
        sys.argv[0] = str(SOURCE)
        runpy.run_path(str(patched_path), run_name="__main__")
    finally:
        patched_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
