You are the test and runtime prototype lead for a Codex bug fix.

Repository: `teamleaderleo/codex`
Baseline commit: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
Suggested scratch branch: `research/code-mode-live-session-test`

Confirmed bug:
A code-mode JavaScript cell can call multiple `tools.exec_command()` operations. When nested commands hit `yield_time_ms`, each result can contain a live unified-exec `session_id`. JavaScript can consume only `result.output`, discard those IDs, and finish. The outer cell then says `Script completed` while nested sessions remain alive.

Tasks:
1. Trace the path from nested `tools.exec_command()` through `ExecCommandToolOutput` to the JavaScript-visible result and outer `RuntimeResponse::Result`.
2. Find the best existing deterministic cross-platform helper for a command that remains alive long enough to yield.
3. Implement the smallest regression test proving that two nested commands yield, JavaScript discards `session_id`, the outer cell completes, and current output does not surface the live sessions.
4. Make teardown terminate every spawned process even when an assertion fails.
5. Do not modify production behavior.

Deliver:
- one focused scratch-branch commit if the test is reliable;
- compact call graph with exact files and symbols;
- test command and result;
- platform concerns and teardown guarantees;
- recommendation for where the production fix should hook in.

Do not open a PR or upstream issue. Do not merge into the Patch 1 branch. Do not push to `main`.