# Code-mode live session IDs

A code-mode cell can start nested terminal commands, keep only their output, and discard the returned session IDs while the processes remain live in the session-level unified-exec manager. The final result can then say `Script completed` without showing the handles needed to inspect, continue, or stop those commands.

The patch retains the existing creator-cell identity on stored process entries and, when a cell finishes, asks the existing manager which processes created by that exact cell are still live. It reports their logical session IDs in numeric order.

## What changes

- Final `Result` and `Terminated` responses can include `Background sessions still running: ...`.
- Only still-live processes created by the exact completing cell are reported.
- At most 64 IDs are displayed, followed by an exact omitted count when needed.
- Ordinary `Yielded` responses remain unchanged.
- Process ownership, lifetime, cleanup, wake-up behaviour, and public protocol shapes remain unchanged.

## Evidence

- Current upstream `main` snapshot `95637f70...` still formats completion status from the runtime response alone and contains no equivalent manager lookup.
- Nine focused formatter and manager tests passed on capped head `eb530466...`.
- Five acceptance cases passed locally, and four remote-safe cases passed through the Docker executor, on the behaviourally equivalent pre-decoupling capped workspace.
- Current code head `77e7e314...` adds only target-Windows routing guards for POSIX-command acceptance cases.
- A targeted Wine-exec run was attempted on the current code head, but an unrelated Bazel BUILD/macro mismatch stopped analysis before any Rust tests were discovered or executed.

See [validation.md](validation.md) for exact refs and run boundaries, and [deep-dive.md](deep-dive.md) for the implementation details.