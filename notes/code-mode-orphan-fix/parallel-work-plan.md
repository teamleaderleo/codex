# Parallel work plan

## Decision

Keep Patch 1 on one implementation branch. Parallelize investigation, test design, and review around that branch rather than having multiple agents edit the same runtime path.

Run Patches 2 and 3 as independent research tracks after Patch 1 has a stable failing test and shared terminology. They may proceed concurrently because their main code paths and design questions differ.

## Patch 1 roles

### Integrator

Owns `fix/code-mode-live-session-summary`.

Responsibilities:

- keep the branch based on the recorded baseline;
- add the failing regression test;
- choose and implement the smallest data-flow change;
- run focused formatting, lint, and tests;
- reconcile findings from the other roles;
- keep commits atomic.

Only the integrator should make broad edits to the Patch 1 implementation branch.

### Test scout

Read-only or scratch-branch task.

Questions:

- Which existing code-mode tests already exercise nested `exec_command` and yielded sessions?
- Which cross-platform test helper can remain alive long enough to yield deterministically?
- How can the test assert that the outer code cell completed while nested sessions remain live?
- How should teardown guarantee that no helper process survives a failed test?

Deliverable:

- a proposed test name;
- exact fixture/helper choice;
- expected assertions;
- files and approximate insertion point;
- known platform concerns.

### Runtime data-flow scout

Read-only or scratch-branch task.

Trace:

1. nested code-mode invocation;
2. `ExecCommandToolOutput` creation;
3. conversion to the JavaScript-visible value;
4. code-cell completion;
5. process-manager lookup and cell cleanup.

Deliverable:

- a short call graph;
- two or three implementation options;
- the smallest option that can report still-live session IDs without changing persistence policy;
- compatibility risks.

### Adversarial reviewer

Begins after the first implementation commit.

Review for:

- races between process exit and outer-result generation;
- stale IDs reported after a process has already exited;
- duplicate IDs from repeated polling;
- output truncation hiding the warning;
- behaviour for successful, failed, terminated, and yielded cells;
- direct tool calls versus nested code-mode calls;
- cleanup after test failures.

Deliverable:

- blocking findings only;
- suggested tests for each blocking finding;
- no broad redesign unless the implementation cannot be made correct.

## Patch 2 research track

May begin once Patch 1 has a test that reliably creates a live nested session.

Initial work should be policy analysis and targeted prototypes, not a final implementation. Compare:

- automatic termination at hidden-subagent completion;
- explicit persistence opt-in;
- ownership transfer to the parent agent;
- blocking completion while live cells exist;
- warning-only behaviour.

The track must preserve valid dev-server and watcher workflows.

## Patch 3 research track

May run independently on macOS.

Research and prototype:

- persisted process-group IDs;
- startup stale-group reconciliation;
- guardian/death-pipe designs;
- process identity checks that prevent killing reused PIDs or unrelated groups;
- behaviour on graceful shutdown, crash, force quit, and upgrade.

Do not merge a macOS-specific prototype into Patch 1.

## Agent handoff format

Every agent report should contain:

```text
Task:
Baseline commit:
Branch or read-only scope:
Files inspected:
Confirmed findings:
Assumptions:
Recommended change:
Tests:
Risks or unanswered questions:
```

Keep reports under roughly 1,500 words. Link precise files and symbols. Avoid pasting large source files or private logs.

## Merge discipline

- One owner per implementation branch.
- Research agents may use scratch branches named `research/<topic>`.
- Cherry-pick only focused commits with tests or durable notes.
- Do not merge speculative policy work into Patch 1.
- Rebase proposal branches onto upstream `main` only at deliberate checkpoints.
- Record the tested commit SHA in every handoff.

## Proposed sequence

1. Create `fix/code-mode-live-session-summary` from the baseline.
2. Run the test scout and runtime data-flow scout in parallel.
3. Integrator writes the failing test using their reports.
4. Integrator implements the minimal visibility fix.
5. Adversarial reviewer inspects the diff.
6. Run focused tests and prepare the upstream issue.
7. Start Patch 2 and Patch 3 research tracks in parallel.