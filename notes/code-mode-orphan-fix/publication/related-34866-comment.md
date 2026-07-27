I opened #<new-issue> to isolate one independently fixable case within this report: code-mode JavaScript can discard nested `session_id` values while the unified-exec manager continues to own the live processes.

This narrower fix can land without deciding the broader lifecycle, continuation, cleanup, polling, or wake-up questions discussed here. It would retain the originating code-mode `CellId` on manager-owned process entries, query the existing manager when that exact cell reaches a terminal response, and include the matching live session IDs in the existing model-visible status.

One boundary remains explicit: local handles can detect exit directly, while exec-server-backed entries rely on manager-observed exit state and can briefly lag an underlying remote exit. The focused issue asks maintainers to decide whether that existing liveness boundary is acceptable for this status report.

The [technical deep dive](https://github.com/teamleaderleo/codex/blob/review/code-mode-issue-ready/notes/code-mode-orphan-fix/publication/deep-dive.md) contains the exploratory implementation, test results, code references, limitations, and reasoning behind the proposed scope.
