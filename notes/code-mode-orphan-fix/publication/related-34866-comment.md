I opened #<new-issue> to isolate one independently fixable case within this report: code-mode JavaScript can discard nested `session_id` values while the unified-exec manager continues to own the live processes.

#34866 remains broader and also covers lifecycle contradictions beyond discarded handles. The new issue is independently actionable because it restores model-visible handles from existing manager state without redefining wrapper completion or process lifecycle semantics.

The proposed change retains the originating code-mode `CellId` on manager-owned process entries, queries the existing manager when that exact cell reaches an in-scope terminal response, and includes the matching live session IDs in the existing model-visible status.

One boundary remains explicit: local handles can detect exit directly, while exec-server-backed entries rely on manager-observed exit state and can briefly lag an underlying remote exit. The focused issue asks maintainers to decide whether that existing liveness boundary is acceptable for this status report.

The [technical deep dive](https://github.com/teamleaderleo/codex/blob/review/code-mode-issue-ready/notes/code-mode-orphan-fix/publication/deep-dive.md) contains the exploratory implementation, test results, code references, limitations, and reasoning behind the proposed scope.
