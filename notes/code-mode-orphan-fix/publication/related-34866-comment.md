I opened #<new-issue> to isolate one independently fixable case within this report: code-mode JavaScript can discard nested `session_id` values while the unified-exec manager continues to own the live processes.

The narrower proposal recovers only the still-live IDs created by the exact completing cell and includes them in the existing model-visible status. It changes no lifecycle policy, JavaScript result fields, or protocol shapes.

I separated it because #34866 proposes a broader wrapper/process lifecycle representation, while this fix can be evaluated as a small compatibility-preserving change. The new issue includes the executable reproduction, root cause, exec-server liveness limitation, and proposed manager lookup.

I have a working prototype with tests and would be glad to prepare a smaller PR if maintainers prefer this narrow direction.