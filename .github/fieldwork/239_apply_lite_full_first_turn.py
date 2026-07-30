#!/usr/bin/env python3
from pathlib import Path
import runpy
import subprocess

ORIGINAL_COMMIT = "c5e8eae5cef579b8de8c7b3b3459f2c3661ce884"
RELATIVE_PATH = ".github/fieldwork/239_apply_lite_full_first_turn.py"
CURRENT_PATH = Path(__file__).resolve()

source = subprocess.check_output(
    ["git", "show", f"{ORIGINAL_COMMIT}:{RELATIVE_PATH}"],
    text=True,
)
exec(
    compile(source, str(CURRENT_PATH), "exec"),
    {"__name__": "__main__", "__file__": str(CURRENT_PATH)},
)
runpy.run_path(
    str(CURRENT_PATH.with_name("239_fix_lite_agent_prefix.py")),
    run_name="__main__",
)
