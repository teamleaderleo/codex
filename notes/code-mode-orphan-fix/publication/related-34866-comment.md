I opened #<new-issue> to isolate one independently fixable case within this report: code-mode JavaScript can keep only nested command output and discard the returned `session_id` values while the unified-exec manager continues to own the live processes.

The narrower proposal would retain the originating code-mode `CellId` on manager-owned process entries, query the existing manager when that exact cell reaches a terminal response, and include the matching live session IDs in the existing model-visible status. It wouldn't change process ownership, lifetime, cleanup, polling, wake-up policy, JavaScript result fields, or public protocol shapes.

One boundary is worth deciding explicitly. Local process handles can expose exit directly, while exec-server-backed entries rely on exit state already reflected in the manager. Four prototype acceptance cases exercised the exec-server path for live-process reporting; the exit-then-exclude survivor case ran locally only. A recently exited remote process could therefore be reported until manager-cached state advances.

The focused issue asks two scope questions:

1. Should live session IDs be shown only when a cell completes successfully, or also when it fails or is terminated?
2. Should the first version include exec-server-backed sessions, accepting that their exit state can briefly lag, or should it be limited to local sessions?

I also linked a technical deep dive with the exploratory implementation, test coverage, limitations, and reasoning behind the proposed scope.
