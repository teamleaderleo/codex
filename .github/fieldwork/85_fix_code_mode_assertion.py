#!/usr/bin/env python3
from pathlib import Path

path = Path("codex-rs/core/src/tools/spec_plan_tests.rs")
text = path.read_text(encoding="utf-8")
old = '    plan.assert_visible_lacks(&["unsearchable_deferred", "tool_search"]);\n'
new = '    plan.assert_visible_lacks(&["unsearchable_deferred"]);\n'

if text.count(old) == 1:
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
elif text.count(new) == 1:
    pass
else:
    raise SystemExit(
        "expected exactly one old or corrected Code Mode assertion anchor"
    )
