# Patch 2 handoff: subagent completion with live cells

## Goal

Define and prototype safe behaviour when a hidden subagent or completed turn still owns yielded code-mode cells or live unified-exec sessions.

This work begins after Patch 1 establishes reliable detection and reporting of live nested sessions.

## Problem statement

Background terminals are intentionally persistent because development servers, watchers, and interactive processes may need to survive across turns. Hidden subagents create a harder ownership case: the user may have no obvious way to discover or stop terminals retained by a subagent that has already completed.

The observed incident completed a turn after a code-mode cell had returned live nested session IDs. Those sessions were later orphaned after runtime ownership was lost.

## Questions to answer

- What entity owns a live session: code cell, turn, subagent thread, parent thread, or whole conversation?
- Does hidden-subagent completion currently trigger any code-mode or unified-exec cleanup?
- Can ownership be transferred to the parent agent without losing control APIs?
- How are legitimate dev servers created by subagents represented today?
- Which completion states should differ: completed, interrupted, errored, closed, evicted, or runtime shutdown?
- Can the user see and control retained subagent terminals through existing UI or protocol events?

## Candidate policies

### A. Automatic termination

Terminate all yielded cells and live sessions owned by a hidden subagent when it completes.

Strengths:

- simple ownership rule;
- prevents invisible retained work;
- easiest to test.

Risks:

- breaks intentional server/watch processes started by subagents;
- requires reliable ownership attribution.

### B. Explicit persistence opt-in

Default subagent sessions to terminate on completion unless the command or cell explicitly requests persistence.

Strengths:

- safe default;
- preserves intentional workflows.

Risks:

- new API and model behaviour;
- compatibility and migration questions;
- persistence intent may be requested too late.

### C. Parent ownership transfer

Transfer live cells and sessions to the parent agent at subagent completion and surface them there.

Strengths:

- preserves background work;
- gives the parent a chance to manage it.

Risks:

- complex lifecycle and protocol changes;
- parent may also complete immediately;
- ownership transfer across runtime boundaries may be incomplete.

### D. Block completion

Prevent hidden-subagent completion until all live cells are terminated, completed, or explicitly persisted.

Strengths:

- forces an explicit decision;
- no silent retained work.

Risks:

- deadlock or repeated model loops;
- can stall the parent task;
- requires strong prompting and timeout behaviour.

### E. Warning only

Surface live sessions prominently but preserve current completion behaviour.

Strengths:

- smallest behavioural change;
- Patch 1 may already provide much of this.

Risks:

- does not prevent orphaning;
- hidden-subagent warnings may never reach the user.

## Recommended research order

1. Trace exact ownership from nested tool invocation through subagent completion.
2. Add a test that completes a hidden subagent while one deterministic session remains live.
3. Confirm whether the parent can enumerate or terminate that session.
4. Prototype automatic termination as a reference implementation.
5. Prototype ownership transfer only if existing abstractions support it cleanly.
6. Compare impact on dev-server workflows.

## Likely code areas

- `codex-rs/core/src/agent/control/residency.rs`
- `codex-rs/core/src/thread_manager.rs`
- `codex-rs/core/src/tasks/mod.rs`
- `codex-rs/core/src/session/handlers.rs`
- `codex-rs/core/src/tools/code_mode/*`
- `codex-rs/core/src/unified_exec/process_manager.rs`
- multi-agent integration tests

## Test matrix

Cover at least:

- hidden subagent completes normally with one live session;
- hidden subagent errors with one live session;
- hidden subagent is interrupted;
- parent remains active;
- parent completes immediately after child;
- intentional persistent server case;
- direct parent-owned background process remains unaffected;
- runtime shutdown still terminates all sessions.

## Deliverable

A design report should recommend one policy and include:

- ownership model;
- state transition table;
- user-visible behaviour;
- compatibility analysis;
- test plan;
- smallest prototype diff;
- reasons rejected alternatives are unsuitable.

Do not merge this work into Patch 1.