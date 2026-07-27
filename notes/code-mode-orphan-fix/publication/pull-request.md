# Report live nested session IDs when code-mode cells finish

<!-- Unpublished, invitation-only pull-request draft. Add the issue relationship only after an issue exists and an upstream maintainer invites the contribution. -->

## Why

A code-mode cell can start nested `exec_command` calls, keep only their output, and discard the returned session IDs. The cell can then finish while those commands remain live, leaving the completion result without the handles needed to manage them.

The session-level unified-exec manager still owns the processes. This change restores their model-visible handles without changing process lifetime or ownership.

## What changed

- Preserve the existing code-mode cell ID on manager-owned process entries.
- Add a read-only manager query for still-live processes created by an exact cell.
- Include the matching session IDs in final `Result` and `Terminated` status text, but not ordinary `Yielded` responses.
- Sort IDs numerically and display at most 64, with an exact suffix such as `(+7 more)` when the list is longer.

Example:

```text
Script completed
Background sessions still running: 6306, 11236
Wall time ...
Output:
...
```

## Testing

- Nine focused formatter and manager tests passed on capped head `eb530466...`.
- Five acceptance cases passed locally on the behaviourally equivalent pre-decoupling capped workspace.
- Four remote-safe acceptance cases passed through the Docker executor. The host-`TempDir` survivor case was excluded from that Docker filter and passed locally.
- Two existing code-mode compatibility tests passed once on the same pre-decoupling capped workspace.
- Current head `77e7e314...` adds only target-Windows routing guards to four POSIX-command acceptance cases.
- A targeted Wine-exec run was attempted on the current code head, but Bazel analysis failed on an unrelated `windows-sandbox-rs` BUILD/macro mismatch before any Rust test was discovered or executed.

The [validation record](validation.md) lists the exact refs, commands, and limitations.

## Notes

- Process lifetime, automatic cleanup, wake-up behaviour, JavaScript result fields, and public protocol shapes are unchanged.
- The 64-ID output bound is intentionally independent of the manager's soft process-store capacity.
- The current base-to-head diff is 903 changed lines because the acceptance module is large. If a smaller review is requested, the production change, focused tests, and primary acceptance reproduction can land first, with the remaining acceptance coverage in a follow-up.
- This is narrower than [#34866](https://github.com/openai/codex/issues/34866): it restores discarded live-session handles but does not redesign background-process continuation or wake-up semantics.