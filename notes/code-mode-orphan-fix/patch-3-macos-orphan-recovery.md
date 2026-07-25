# Patch 3 handoff: macOS orphan recovery

## Goal

Prevent or safely reclaim detached unified-exec process groups when their owning Codex runtime disappears on macOS.

This track is independent of the code-mode visibility fix. It addresses crash, force-quit, upgrade, and owner-loss cases where graceful Rust teardown does not run.

## Confirmed platform gap

Unified exec detaches Unix commands into their own session/process group. Linux configures a parent-death signal. The corresponding non-Linux implementation is currently a no-op, so macOS children can survive abrupt owner loss and be adopted by PID 1.

The observed Playwright groups had:

- group leader PID equal to PGID;
- no controlling terminal;
- parent PID 1 after owner loss;
- Codex Desktop environment attribution;
- no active network sockets at inspection time;
- persisted logical process records but no usable OS PID in the Desktop registry.

## Non-goals

- Do not change code-mode result wording in this track.
- Do not infer stale ownership from command names.
- Do not kill arbitrary PID-1 children.
- Do not rely on PID alone without identity validation.
- Do not assume graceful shutdown is sufficient.

## Candidate mechanisms

### A. Guardian process or death pipe

Create a small supervisor whose lifetime is tied to the owning runtime through a pipe. When the pipe closes unexpectedly, the guardian terminates registered process groups.

Strengths:

- acts immediately after owner loss;
- does not depend on next startup;
- can work on macOS without kernel parent-death support.

Risks:

- additional process and protocol;
- guardian itself must be supervised;
- registration races during spawn and shutdown.

### B. Persisted PGID registry and startup sweep

Persist process-group identity and ownership metadata. On startup, validate each record and terminate groups whose owner lease is stale.

Strengths:

- useful recovery after crashes and upgrades;
- supports diagnostics;
- simpler than a resident guardian.

Risks:

- orphan remains alive until next startup;
- PID/PGID reuse can kill unrelated processes unless identity checks are strong;
- concurrent app instances and stale writes complicate leases.

### C. Per-process owner lease

Pass a uniquely identifiable owner token or pipe to the spawned command wrapper. A lightweight wrapper monitors the owner and terminates its process group when the lease ends.

Strengths:

- localises ownership to each group;
- immediate cleanup;
- potentially simpler correctness model than a central guardian.

Risks:

- wrapper needed on every platform/backend;
- exec-server and sandbox interactions;
- wrapper must not interfere with signals, exit status, or TTY behaviour.

### D. Platform lifecycle APIs

Investigate macOS-specific process controls, launchd relationships, kqueue process monitoring, or other Darwin facilities.

Strengths:

- may avoid polling and custom persistence.

Risks:

- platform-specific complexity;
- may not provide a direct equivalent to Linux `PR_SET_PDEATHSIG`;
- sandbox and entitlement constraints.

## Safety requirements

Any recovery mechanism must validate more than a numeric PID or PGID. Candidate identity signals include:

- owner-generated random token;
- process start time;
- executable path;
- expected environment marker;
- conversation/thread ID;
- persisted spawn generation;
- process-group leader relationship.

The design must account for PID reuse, concurrent Codex instances, partial registry writes, system sleep, app updates, and manual user processes that happen to run similar commands.

## Research tasks

### Darwin process-semantics scout

- confirm available macOS APIs for parent/owner death detection;
- compare pipe EOF, kqueue `EVFILT_PROC`, and wrapper approaches;
- document behaviour across normal quit, force quit, crash, and SIGKILL;
- identify sandbox or entitlement constraints.

### Registry and identity scout

- map current Desktop and core process registries;
- identify where OS PID/PGID is known and where it is lost;
- propose durable record fields and atomic update behaviour;
- design identity validation that survives restart without risking unrelated processes.

### Prototype owner

Build one isolated proof of concept, preferably a death-pipe or wrapper design, using a deterministic helper process. Do not initially wire it through every exec backend.

### Adversarial reviewer

Attack:

- PID reuse;
- guardian crash;
- app restart while old instance still exits;
- two Codex instances using the same registry;
- failure between process spawn and guardian registration;
- failure during deregistration;
- group leader exits while children remain;
- commands that deliberately daemonise or create nested sessions.

## Test plan

A useful test harness should launch a helper that records its PID/PGID and remains alive. Then simulate:

- graceful session shutdown;
- owner task abort;
- owner process crash;
- owner process SIGKILL;
- application restart and stale sweep;
- concurrent live owner that must not be reclaimed;
- forged or reused PID record that must not be killed.

macOS-specific integration tests may be necessary, but core identity and registry logic should have platform-independent unit tests.

## Deliverable

Produce a design comparison with:

- recommended mechanism;
- threat and safety analysis;
- lifecycle diagrams;
- required persistent fields;
- prototype results;
- test strategy;
- rollout and compatibility concerns.

Keep any prototype on `fix/macos-orphan-recovery` or a `research/macos-*` scratch branch. Do not merge it into Patch 1.