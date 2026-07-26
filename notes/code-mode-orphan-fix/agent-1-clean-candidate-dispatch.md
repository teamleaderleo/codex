# Agent 1 dispatch: prepare the clean Patch 1 candidate

Date: 2026-07-26

## Purpose

Prepare the upstream-ready Patch 1 branch while preserving the existing investigation branches and Markdown as provenance.

This assignment does **not** change the reviewed Patch 1 contract. It reconstructs the already reviewed net effect on current upstream main, runs repository-native hygiene, and publishes a clean comparison for the final team sanity review.

Do not open the upstream issue or pull request yet.

## Required reading

Before changing code, read:

- `notes/code-mode-orphan-fix/coordination-status.md`;
- `notes/code-mode-orphan-fix/final-net-diff-review-73e5b9f.md`;
- `notes/code-mode-orphan-fix/agent-4-history-issue-report.md`;
- `notes/code-mode-orphan-fix/workflow-retrospective-2026-07-26.md`.

## References

Investigation baseline:

`20dafe201d91d4405eef05ecd1db0257f13a9ac8`

Reviewed formatted implementation:

`73e5b9fc28de0815975fad3c3d70a6a0b38399b1`

Reviewed comparison:

`20dafe201d91d4405eef05ecd1db0257f13a9ac8...73e5b9fc28de0815975fad3c3d70a6a0b38399b1`

Upstream `openai/codex` main observed when this dispatch was written:

`61a44880a85d2fd0d8770908dea5733495e571c8`

That upstream head is two unrelated commits after the investigation baseline. Re-fetch upstream immediately before beginning and record the actual base you use; do not assume the observed SHA is still current.

No clean-candidate branch existed when this dispatch was written.

## Reviewed file set

The reviewed net effect changes exactly these files:

1. `codex-rs/core/src/tools/code_mode/mod.rs`
2. `codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs`
3. `codex-rs/core/src/unified_exec/mod.rs`
4. `codex-rs/core/src/unified_exec/mod_tests.rs`
5. `codex-rs/core/src/unified_exec/process_manager.rs`
6. `codex-rs/core/src/unified_exec/process_manager_tests.rs`
7. `codex-rs/core/tests/code_mode_orphan_sessions.rs`

Do not include coordination, research, audit, review, runtime-report, retrospective, or agent-handoff Markdown in the clean candidate.

## Patch 1 contract to preserve

The clean candidate must remain visibility-only:

- preserve typed `ToolCallSource::CodeMode` creator-cell attribution;
- carry the typed `CellId` through `UnifiedExecContext` into stored `ProcessEntry` metadata;
- keep the unified-exec process manager as the liveness source of truth;
- query by exact creator cell;
- exclude exited processes;
- sort logical process IDs deterministically;
- disclose surviving IDs only for terminal `Result` and `Terminated` responses;
- keep ordinary `Yielded` responses completion-neutral;
- place the summary outside emitted-output truncation;
- preserve opaque nested tool call IDs;
- preserve the JavaScript-visible `session_id` schema;
- do not change termination, persistence, pruning, shutdown, interrupt, dispatch, subagent, remote-exec, recovery, or public-protocol policy.

Reject any reconstruction change that expands this boundary.

## Work sequence

### 1. Add your independent retrospective

Before coordinating around other comments, add one independent comment to:

`https://github.com/teamleaderleo/stensibly/issues/246`

Use the shared prompts and the Agent 1 questions. In particular, clarify from your original conversation history whether Patch 2 and Patch 3 were concrete planned proposals or only labels for possible follow-up families.

Do not modify Codex branches as part of the retrospective comment.

### 2. Establish the clean base

- Fetch current `openai/codex` main.
- Record the exact upstream SHA.
- Record divergence from `20dafe201d91d4405eef05ecd1db0257f13a9ac8`.
- Confirm whether upstream touched any of the seven reviewed files.
- If upstream touched one of those files, resolve only the concrete compatibility conflict and describe it explicitly.

Suggested branch name:

`fix/code-mode-live-session-summary-clean`

Create it from the exact current upstream main SHA, not from an investigation branch.

### 3. Reconstruct the reviewed net effect

Reapply the semantic net effect from:

`20dafe201d91d4405eef05ecd1db0257f13a9ac8...73e5b9fc28de0815975fad3c3d70a6a0b38399b1`

Prefer reconstruction from the final reviewed diff or selected-file patch rather than merging or rebasing the investigation ancestry.

The clean branch must not contain:

- the call-ID-prefix prototype;
- research or coordination commits;
- merge-only provenance commits;
- runtime reports;
- issue drafts;
- retrospective files.

Commit structure:

- Default to one coherent commit containing implementation and its focused tests.
- Use two commits only if separating production changes and tests materially improves review without creating an unclear or broken intermediate state.
- Record which structure you chose and why.

### 4. Capture named-tree state before validation

Record:

```text
upstream_base_sha=
clean_branch=
worktree_sha_before_format=
worktree_dirty_before_format=
required_tool_availability=
```

Check the repository instructions and tool availability before running commands. Do not silently substitute a different validation workflow.

### 5. Run repository-native hygiene

Use the repository-documented workflow where available.

At minimum, determine and record the results of:

- repository-native formatting (`just fmt` from `codex-rs`);
- scoped lint/fix (`just fix -p codex-core`);
- repository-native project tests for `codex-core`;
- the dedicated `code_mode_orphan_sessions` acceptance target through the repository-supported test route;
- any platform skips or unavailable tools.

Do not claim the complete workspace suite unless it actually runs. The repository instructions require human approval before the complete `just test` workspace run; stop and request that decision rather than assuming approval.

If the documented wrapper cannot select the focused target, inspect the `justfile` and record the exact supported command. Do not repeat the earlier overly broad Cargo fallback that selected unrelated integration binaries.

Separate results into:

- passed;
- failed assertion or compile error;
- skipped;
- not run;
- infrastructure or environment failure;
- command-selection error.

### 6. Capture named-tree state after hygiene

Record:

```text
worktree_sha_after_format_and_fix=
worktree_dirty_after_format_and_fix=
files_changed_by_format_or_fix=
```

If formatting or lint/fix changes files, commit the resulting exact tree before treating later validation as canonical.

### 7. Publish and inspect the clean branch

Push the clean branch, but do not open a pull request.

Record actual output or exact summaries for:

```sh
git status --short
git diff --check
git log --oneline --decorate -8
git diff --stat <upstream-base>...HEAD
git diff --name-status <upstream-base>...HEAD
```

Also record:

- clean candidate head SHA;
- upstream base SHA;
- comparison URL/ref;
- changed-file list;
- commit count;
- tests and hygiene actually run;
- anything not run.

### 8. Prove equivalence to the reviewed tree

Compare the clean candidate against the reviewed Patch 1 head.

Because the bases differ, do not rely only on raw commit ancestry. Verify the seven-file semantic patch:

- no reviewed production or acceptance behaviour is missing;
- no research artifact is present;
- no lifecycle-policy expansion appears;
- any difference is attributable only to current upstream context, formatting, or an explicitly described conflict resolution.

Provide enough information for Agent 3 to perform an independent final clean-candidate review.

## Required handoff

Return:

```text
Agent: 1 — clean candidate owner
Retrospective comment: <link>
Patch 2/3 clarification: <answer>
Upstream base SHA:
Clean branch:
Clean head SHA:
Commit structure and rationale:
Changed files:
Upstream conflicts or adaptations:
Formatting command and result:
Lint/fix command and result:
Focused/project tests and results:
Acceptance command and result:
Complete workspace test: passed / failed / not run pending approval
Skips, flakes, infrastructure failures, or command-selection failures:
Repository inspection results:
Clean comparison:
Equivalence assessment against 73e5b9fc...:
Open risks:
Decision requested:
Recommended next action:
```

## Publication and scope restrictions

- Do not open the upstream Codex issue.
- Do not open the upstream Codex pull request.
- Do not delete or force-push the investigation branches.
- Do not add the workflow retrospective or coordination notes to the clean candidate.
- Do not expand Patch 1 into Patch 2/3 work.
- Do not call the cross-turn dispatch path reproduced without executable evidence.
- Do not perform irreversible external actions without explicit human approval.
