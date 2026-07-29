# Effective tool-surface checkpoint experiment

Research date: 2026-07-29

Research owner: Lantern

Canonical programme: `teamleaderleo/stensibly#544`

Related lanes:

- source map: `teamleaderleo/stensibly#552`
- reproduction study: `teamleaderleo/stensibly#553`
- upstream synthesis: `teamleaderleo/stensibly#554`
- active ChatGPT/Stensibly incident: `teamleaderleo/stensibly#490`

## Write boundary

This record and any experiment stay in `teamleaderleo/codex`. `openai/codex` remains read-only until the human explicitly approves publication.

The branch currently starts at owned fork head `2b7b93081361b77f8ddaceaf362a09765b4153bf`. The inspected upstream source pin is `3725f02cf38d856bc82bb46dd68ab61bb96ec6fc`; the fork is 93 commits behind that pin and carries five unrelated temporary CI workflow commits. Rebase or recreate the experiment branch from the selected upstream revision before implementing runtime changes.

## Confirmed source seams at the upstream pin

- Startup Responses WebSocket prewarm creates a startup turn, captures a `StepContext`, builds a prompt from its `ToolRouter`, and returns a session-scoped client to the first normal turn.
- Normal sampling captures one request-scoped `StepContext` so model advertisement and executable dispatch share a router.
- WebSocket request reuse compares tool payloads.
- Host dynamic tools and selected capability roots can be restored from rollout `SessionMeta` on resume and fork.
- Public `thread/resume` and `thread/fork` inputs contain no fresh `dynamicTools` or `selectedCapabilityRoots` fields equivalent to `thread/start`.
- MCP and app tools are rebuilt from current auth, connector snapshots, selected roots, required servers, policy, and current binding.
- A step can receive an empty MCP binding when no current binding satisfies required servers after refresh.
- Deferred tool families require a functioning discovery route.

## First experimental slice

### Privacy-safe checkpoint

Add a trace/test-only `EffectiveToolSurfaceCheckpoint` with:

- request kind: prewarm, compact, normal turn, retry;
- thread and turn digests;
- model/profile and transport;
- native/core count and digest;
- code-mode or `additional_tools` count and digest;
- host dynamic count and digest;
- app/connector count and digest;
- configured MCP count and digest;
- discovery presence and mode;
- selected capability-root count and digest;
- required-server count and digest;
- registered router digest;
- model-visible digest;
- executable dispatch digest;
- prior checkpoint digest and lifecycle transition.

Exclude descriptions, schemas, arguments, prompts, credentials, connector payloads, local paths, and server results.

### Prewarm versus first turn

Compare the checkpoint used by startup prewarm with the first normal turn that consumes the prewarmed client. Record typed differences. In the experiment, force a fresh client or HTTP fallback when the difference removes executable capability.

### Deferred/discovery invariant

Add a focused assertion and regression test: every deferred dynamic, app, or configured MCP family has an executable discovery route in the same model-visible request. Include a model/profile A/B case.

### Same-history transport regression

Create compacted replacement history with benign tool-call/result continuity. Send the next request through Responses HTTP and WebSocket. Assert equivalent usable native/code-mode surfaces and successful benign execution.

### Resume/fork stale-host diagnostic

Create a fixture where saved `SessionMeta.dynamic_tools` and selected roots differ from the current host catalogue. Record provenance and digest differences. Keep refresh semantics behind a test-only switch until the host contract is confirmed.

### MCP stub-to-real transition

Start with a harmless MCP binding exposing one stub tool. Replace it with a larger real catalogue, refresh, and assert that registered, model-visible, and executable digests converge. This targets the stale startup catalogue reported in `openai/codex#26196`.

## Acceptance criteria

- The implementation branch starts from an explicit upstream revision.
- Checkpoints contain counts and digests without sensitive content.
- Prewarm and first-turn surfaces compare deterministically.
- Deferred tools without discovery fail a focused test.
- The same compacted history gets equivalent usable surfaces over HTTP and WebSocket.
- Resume/fork reports saved-versus-current host capability divergence.
- MCP stub-to-real transition detects or repairs a stale binding.
- Focused `codex-core` tests pass.
- Upstream receives zero writes.

## Exact next action

Rebase this branch onto the chosen upstream pin. Add the checkpoint type behind test/trace visibility and write the prewarm-versus-first-turn test before changing runtime behavior.
