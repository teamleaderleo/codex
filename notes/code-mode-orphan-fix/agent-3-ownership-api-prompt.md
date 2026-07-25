You are reviewing resource ownership and API safety around Codex code mode and unified exec.

Repository: `teamleaderleo/codex`
Baseline commit: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
Scope: read-only.

Question:
Who owns a nested unified-exec process from spawn through yield, polling, cell completion, turn completion, session shutdown, and runtime loss?

Tasks:
1. Build a state machine for `UnifiedExecProcessManager` entries and code-mode cells.
2. Identify ownership transitions, cleanup triggers, and places where ownership is implicit or can be lost.
3. Evaluate the JavaScript API as a resource-handling interface: `session_id` naming, discarded handles, completion wording, and backwards-compatible ways to surface live sessions.
4. Audit for at most five adjacent defects in the same family: dropped task handles, ignored terminate errors, Drop-only cleanup, stale registry entries, or outer completion while nested work remains live.
5. Compare at least three Patch 1 implementation options and recommend the smallest one that changes visibility only.

Deliver under 1,800 words:
- state machine and compact call graph;
- recommended Patch 1 design;
- race and compatibility risks;
- no more than five precise adjacent findings, each with file, symbol, scenario, confidence, and test coverage.

Do not edit code or publish anything. Do not open a PR or issue. Do not push to `main`.