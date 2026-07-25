# Code-mode orphan process investigation

This branch contains coordination notes for investigating and prototyping fixes for a Codex code-mode lifecycle bug. It is intentionally separate from implementation branches so an eventual upstream patch can remain focused.

## Baseline

- Fork: `teamleaderleo/codex`
- Upstream: `openai/codex`
- Baseline commit: `20dafe201d91d4405eef05ecd1db0257f13a9ac8`
- Observed Desktop bundle: `26.715.12143`
- Platform: macOS

All proposal branches should start from the baseline commit unless they are deliberately rebased and the new base is recorded in the branch notes.

## Confirmed incident

A code-mode cell launched three nested commands using `Promise.all`:

1. Playwright desktop screenshot
2. Playwright mobile screenshot
3. `curl`

Each nested `exec_command` used `yield_time_ms: 30000`. The outer code-mode cell initially yielded after 11 seconds. Codex called `wait` for the cell. At approximately the 30-second nested yield boundary, the cell reported `Script completed`, while the two Playwright commands had returned live unified-exec session IDs and continued running in the background.

The JavaScript consumed only `result.output`, discarding the live `session_id` values. The agent retried the screenshot work through a different URL, completed the turn, and never terminated the first two sessions.

Days later, the original process groups were still alive under PID 1 on macOS. Codex Desktop attribution and the persisted process registry tied them to the same conversation and commands.

## Root-cause layers

The incident spans three independently useful repair areas:

1. **Visibility and API safety** — a code-mode cell can say `Script completed` while nested exec sessions remain live and their handles can be silently discarded.
2. **Turn and subagent lifecycle** — a turn can finish while yielded code-mode cells or background sessions remain owned by a hidden subagent.
3. **macOS recovery** — detached process groups can survive owner loss because macOS lacks the Linux parent-death signal used by the current implementation.

These areas should be explored separately. A single large patch would be difficult to reason about and review.

## Branch map

- `fix/code-mode-live-session-summary`
  - First implementation target.
  - Surface live nested unified-exec sessions in the outer code-mode result.
- `fix/subagent-yielded-cell-cleanup`
  - Explore completion policy for hidden subagents that still own live cells or sessions.
- `fix/macos-orphan-recovery`
  - Explore durable process-group ownership and stale-process recovery on macOS.
- `research/code-mode-orphan-handoffs`
  - Coordination notes only. Do not base an upstream patch on this branch.

## Working rules

- Write the failing regression test before the implementation when practical.
- Keep each proposal branch independently reviewable.
- Do not mix policy changes with macOS-specific recovery work.
- Do not upload private rollout logs, prompts, environment dumps, image data, or access tokens.
- Record assumptions separately from confirmed behavior.
- Prefer cross-platform test helpers over shell-specific commands such as `sleep`.
- Upstream contributions are by invitation. Open an issue with evidence and design discussion before opening a PR.

## Suggested order

1. Complete the Patch 1 regression test and minimal visibility fix.
2. Use that vocabulary and test machinery to evaluate Patch 2 policies.
3. Investigate Patch 3 independently because it concerns crash recovery and operating-system process semantics.

See the other documents in this directory for agent-ready handoffs.