# Reusable `smoltest` VM runner

Status: proposed fork-local developer tooling

This note replaces an issue tracker entry because GitHub Issues is disabled on this fork. It is intentionally separate from the code-mode orphan Patch 1 publication gate and should not be treated as an upstream Codex product issue.

## Goal

Provide one stable command that agents and humans can use to run Codex tests on a persistent warm Linux VM without repeatedly pasting VM paths, Cargo environment variables, branch-composition commands, cache settings, timeouts, and cleanup logic.

Routine use should be approximately:

```sh
smoltest orphan
smoltest orphan-one large_emitted_output_does_not_truncate_live_session_warning
smoltest unit
smoltest format
```

Agents should be able to request the same named modes without reconstructing the full shell command.

## Proposed layers

### Host launcher

A stable `smoltest` command on the host should:

- select or start the configured Lima VM;
- invoke the guest runner with a named mode;
- stream concise progress;
- preserve the guest exit status;
- report the host-side log location without embedding private paths in repository output.

### Guest runner

A stable guest command should:

- own one dedicated checkout;
- reuse a persistent Cargo target directory;
- fetch and verify configured refs or commits;
- run tests before optional formatting checks;
- clean up test processes;
- emit a compact machine-readable summary.

### Profile or manifest

Machine-specific defaults should live in one local profile rather than in every command. Suggested fields:

- VM name;
- repository URL;
- harness-owned checkout path;
- persistent Cargo target directory;
- Cargo job count;
- stack size and backtrace settings;
- timeout and log directory;
- default integrated branch;
- optional ordered integration commits while agent work is still split across branches.

Repository-owned defaults should reuse existing commands such as `just test` and `just fmt-check` where practical.

## Required behaviour

- Reuse the persistent checkout and build cache.
- Keep destructive reset and cleanup operations confined to the harness-owned checkout.
- Fetch and verify expected refs or commits before execution.
- Support a single integrated branch as the normal case.
- Temporarily support a small ordered integration manifest while parallel branches remain separate.
- Run requested tests before optional formatting audits.
- Capture or summarise noisy formatter output instead of flooding the terminal.
- Preserve `RUST_MIN_STACK=8388608`, preferably by delegating to the repository test recipe.
- Run lifecycle-sensitive integration tests serially when requested.
- Always perform process cleanup and report survivors.
- Return the underlying test exit status.
- Print resolved refs, tested tree or commit, exact test command, and result in a compact final block.
- Avoid credentials and private machine paths in repository history or public output.

## Suggested modes

### `orphan`

Run the complete `code_mode_orphan_sessions` acceptance target serially.

### `orphan-one <test>`

Run one exact test from the acceptance target.

### `unit`

Run focused code-mode and unified-exec unit tests.

### `format`

Run the repository formatting check explicitly, with output captured and condensed.

### `full`

Run broader validation after the focused suite is green.

## Example interface

```sh
# Normal integrated-branch run.
smoltest orphan

# One test.
smoltest orphan-one code_mode_completion_reports_only_sessions_created_by_current_cell

# Exceptional ref override without editing the runner.
SMOLTEST_REF=fix/code-mode-live-session-summary smoltest orphan
```

The profile should supply routine defaults. Overrides are for exceptional runs, not the normal interface.

## Security boundaries

- Do not execute untrusted pull-request code automatically on a personal warm runner.
- Do not store repository or GitHub credentials in the profile.
- Use a dedicated checkout so reset and clean operations cannot affect a human working tree.
- Validate guest paths and refs before shell execution.
- Keep future self-hosted GitHub Actions integration restricted to trusted refs or manual dispatch.

## Acceptance criteria

- After one-time installation, a fresh host shell can run the focused suite with `smoltest orphan`.
- Repeated runs reuse the same build cache.
- Branch and commit defaults can be changed in one profile or manifest without rewriting the runner.
- Test output remains readable and formatter output cannot flood the terminal.
- The final summary is enough for an agent to record the run without asking the user to interpret the full log.
- Installation, update, and removal instructions are documented.
- The runner works manually before any self-hosted Actions integration is attempted.

## Non-goals for the first version

- General-purpose CI orchestration for every repository.
- Automatic execution of arbitrary pull requests.
- Replacing repository-native test commands.
- Hiding provenance or silently testing a moving branch without reporting the resolved commit.

## Recommended implementation order

1. Install a stable guest runner and local profile format.
2. Add the host `smoltest` launcher.
3. Implement `orphan` and `orphan-one` modes using the existing warm cache.
4. Add compact logs and cleanup reporting.
5. Add `unit` and captured `format` modes.
6. Remove temporary multi-commit composition once the integration branch contains the complete test lineage.
7. Consider a restricted self-hosted Actions trigger only after manual use is reliable.
