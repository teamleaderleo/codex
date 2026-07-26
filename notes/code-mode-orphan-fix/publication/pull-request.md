# Report live nested session IDs when code-mode cells finish

<!-- Unpublished, invitation-only pull-request draft. Add the issue relationship only after an issue exists and an upstream maintainer invites the contribution. -->

## Why

A code-mode cell can start nested `exec_command` calls, keep only their `.output`, and discard the returned session IDs. The cell can then finish while those commands remain live. The session-level unified-exec process manager still owns the processes, but the final code-mode result has no exact way to recover and report the missing handles.

This change restores that control visibility without changing process ownership or background-process lifetime.

## What changed

- [`ExecCommandHandler`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L132-L138) carries the existing code-mode cell ID into `UnifiedExecContext`.
- [`UnifiedExecContext` and `ProcessEntry`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L76-L99) retain typed creator-cell attribution beside the manager-owned process; [`store_process`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/process_manager.rs#L944-L976) copies it into the stored entry.
- [`live_process_ids_created_by_cell`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L168-L180) filters by exact creator-cell identity, excludes processes whose exit is already reflected in manager state, and sorts logical session IDs numerically.
- [Final-result handling](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L201-L269) performs the lookup for `Result` and `Terminated`, but not ordinary `Yielded` responses.
- [Status formatting](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L270-L305) displays at most 64 sorted IDs. If more match, it appends an exact suffix such as `(+7 more)`.
- Four remote-capable acceptance cases carry [`skip_if_target_windows!`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs) because their command strings require POSIX shell syntax. The host-`TempDir` survivor case retains its broader local-only guard.

The display cap is a separate model-visible hard limit:

```rust
const MAX_INLINE_BACKGROUND_SESSION_IDS: usize = 64;
```

It is intentionally independent of the manager's soft process-store capacity, even though both currently have the value 64. Lists containing 64 or fewer matching IDs are complete. An overflow line does not claim to display every matching process handle.

Example:

```text
Script completed
Background sessions still running: 6306, 11236
Wall time ...
Output:
...
```

Abridged overflow example—the literal output contains all 64 visible IDs:

```text
Background sessions still running: 1, 2, ... 64 (+7 more)
```

## Boundaries

- The existing session-level unified-exec process manager remains the liveness authority.
- The lookup is point-in-time: a process can exit immediately after it is selected.
- Only processes created by the exact completing cell and considered live by manager state at lookup time are included.
- Ordinary `Yielded` responses remain warning-free.
- The warning is prepended after code-mode emitted-output truncation; later global conversation-history limits still apply.
- Process lifetime, automatic termination, persistence, pruning policy, shutdown handling, recovery, wake-up behaviour, JavaScript result schema, and process ownership are unchanged.
- No public protocol schema, event type, event-emission policy, or call-ID format is changed. Existing response-item notifications can carry the intentionally changed completion text.

<details>
<summary>Alternatives considered</summary>

- Reading IDs from JavaScript output cannot recover values that JavaScript discarded.
- Appending IDs to command output would mix control metadata with program output and would still depend on JavaScript preserving it.
- Encoding creator identity in call-ID strings would turn an opaque format into an ownership API.
- A second per-cell process registry would duplicate the existing manager's liveness and lifecycle bookkeeping.
- Automatically waiting for or terminating matching processes would change product lifecycle policy.
- A new JavaScript field or protocol event would not solve JavaScript discarding returned values and would broaden compatibility work.
- Reusing the manager's soft capacity as the display limit would couple internal storage policy to model-visible output.

</details>

## Testing

### Focused formatter and manager tests

The capped head `eb530466...` passed all nine focused tests in [GitHub Actions run 30220464228](https://github.com/teamleaderleo/codex/actions/runs/30220464228):

1. `terminal_cell_id_excludes_yielded_responses`
2. `terminal_script_status_surfaces_sorted_live_background_sessions`
3. `terminal_script_status_preserves_sessions_at_display_limit`
4. `terminal_script_status_caps_sessions_above_display_limit`
5. `terminal_script_status_sorts_before_truncation`
6. `terminal_script_status_formats_exact_omitted_count`
7. `terminal_script_status_omits_warning_for_empty_sessions`
8. `yielded_script_status_does_not_surface_background_sessions`
9. `live_process_ids_created_by_cell_filters_exited_and_sorts`

That run also passed `just fmt`, `just fix -p codex-core`, `git diff --check`, worktree cleanliness, and its recorded supplement-scope checks.

### Acceptance and compatibility coverage

[GitHub Actions run 30217686056](https://github.com/teamleaderleo/codex/actions/runs/30217686056) exercised the capped behaviour before the display constant was decoupled from the manager capacity. Its workspace already contained the final remote-test harness changes.

- local acceptance: 5 passed, 0 failed;
- Docker remote acceptance: four selected cases passed, 0 failed;
- survivor case: excluded from the Docker filter because its host `TempDir` PID/release paths are unavailable inside the executor; passed locally;
- compatibility: `code_mode_can_run_multiple_yielded_sessions` and `code_mode_wait_can_terminate_and_continue` passed once on that pre-decoupling capped workspace.

Exact current head `77e7e314...` adds only target-Windows guards to four POSIX-command acceptance cases. It has not yet received a new public Wine-exec or compatibility Actions run.

No broad differential was run at the final capped or guard-only heads, and the complete workspace suite was not run. The [validation record](validation.md) gives exact refs and commands.

## Review size and staging

The current base-to-head diff is 903 changed lines, above the repository's 800-line review guideline. Production code is a small part of that total; the 527-line acceptance module dominates it.

The smallest coherent first stage, if maintainers prefer a split, is:

1. production provenance, manager query, bounded formatter, the nine focused tests, and the primary discarded-handle acceptance reproduction;
2. supplemental acceptance coverage for exited-process filtering, large-output placement, yielded neutrality, exact-cell isolation, and remote-executor routing.

The bounded formatter belongs in the first stage. The split is a reviewability option rather than a correctness dependency.

## Related issue

[#34866](https://github.com/openai/codex/issues/34866) reports contradictory wrapper/process completion semantics and identifies discarded `session_id` or `exit_code` values as one possible consequence. This change isolates that consequence as a bounded exact-cell visibility fix; it does not implement the broader lifecycle redesign proposed there.
