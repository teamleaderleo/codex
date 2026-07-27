I opened #<new-issue> to isolate one independently fixable case within this report: code-mode JavaScript can retain only nested command output and discard the returned `session_id` values while the unified-exec manager continues to own the live processes.

The narrower proposal adds no lifecycle or protocol representation. It retains the originating code-mode `CellId` on manager-owned process entries, queries the existing manager when that exact cell reaches a terminal response, and includes the matching live logical session IDs in the existing model-visible status. This restores the discarded control handles without changing process ownership, lifetime, cleanup, polling, wake-up policy, JavaScript result fields, or public protocol shapes.

One boundary is worth deciding explicitly. Local process handles can expose exit directly, while exec-server-backed entries rely on exit state already reflected in the manager. Four prototype acceptance cases exercised the exec-server path for live-process reporting; the exit-then-exclude survivor case ran locally only. A recently exited remote process could therefore be reported until manager-cached state advances.

The focused issue asks two design questions:

1. Should the warning appear only for successful `Result` responses, or for every terminal outcome, including failed `Result` and `Terminated`?
2. Is manager-observed liveness acceptable for exec-server-backed processes, or should the broader lifecycle representation proposed here land first?

A focused prototype covers manager, formatter, and end-to-end regression cases; the new issue links the supporting technical notes.