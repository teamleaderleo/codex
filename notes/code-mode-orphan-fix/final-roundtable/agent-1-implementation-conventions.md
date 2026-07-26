Agent: 1
Lane: implementation conventions and clean-candidate construction
Reviewed base: `61a44880a85d2fd0d8770908dea5733495e571c8`
Reviewed candidate: `3778e1fae6e7e3d885252282a7c5ce67e06730ff`
Verdict: pass with notes

Concrete findings:
- `ExecCommandHandler` is the appropriate boundary for converting the existing `ToolCallSource::CodeMode` metadata into a typed `CellId`, because the source is still available there and unified exec should not infer ownership from call-ID text or JavaScript output.
- `UnifiedExecContext` is an appropriate carrier for creator-cell attribution during process creation. It already transports invocation-scoped state into unified exec without expanding a public protocol or JavaScript-visible result.
- `ProcessEntry` is the appropriate persistence point because the unified-exec process manager owns the live process after registration. Creator attribution therefore remains available for the lifetime of the manager-owned process even when JavaScript discards its copied session handle.
- `UnifiedExecProcessManager::live_process_ids_created_by_cell` is an appropriately narrow query: it uses exact typed identity, checks current process liveness, returns logical process IDs, and mutates no lifecycle state.
- The process-store lock is held only for bounded synchronous inspection and sorting; there is no nested `.await` while the lock is held.
- Naming and visibility are suitable: `creator_cell_id` and `live_process_ids_created_by_cell` are explicit, the query is `pub(crate)` only because code mode is a sibling module, and `ProcessEntry` remains private.
- Deterministic sorting in both the manager query and status formatter is redundant but harmless. The process set is bounded, and the formatter remains deterministic when tested independently.
- The one-commit clean candidate is appropriately organized. The visibility-only implementation and its focused unit and acceptance tests form one coherent reviewable change, while investigation and prototype ancestry remain outside the candidate.

Required code or test changes:
- none

Public-copy corrections:
- none

Likely maintainer concerns:
- A maintainer may ask whether generic unified-exec state should retain a broader origin type rather than `Option<CellId>`. The current narrower field is preferable for Patch 1 because it stores only the identity required by the query and does not retain unrelated code-mode bridge metadata.
- `UnifiedExecContext::with_creator_cell_id(Option<CellId>)` is a minor API-shape wart because repository guidance discourages ambiguous `Option` parameters. The current call passes a clearly named variable rather than a literal `None`, remains crate-private, and is not worth changing after validation. A maintainer-requested polish could instead call a setter accepting `CellId` only in the code-mode branch.
- The new 521-line acceptance file makes most of the diff volume. It is justified by the behavioural matrix and remains under the repository's overall change-size guidance, but maintainers may still ask whether shared test helpers can shorten it. No pre-emptive rewrite is recommended.

Deferred follow-ups:
- Patch 2 is a planning family for ownership and cleanup-policy questions, including hidden or subagent completion while live yielded work remains. It is not an approved or promised patch.
- Patch 3 is a planning family for runtime-loss and macOS orphan-recovery approaches, including durable process-group tracking, stale-process sweeps, guardians, or stronger termination reporting. It is not an approved or promised patch.
- Each deferred family requires its own executable reproduction, ownership statement, product-policy decision, issue, implementation review, and validation before becoming a concrete change.
- The delayed cross-turn dispatch concern remains separate and must not be described as reproduced without executable evidence.

Human decisions requested:
- none for implementation conventions
- publication and any broader validation remain explicit human decisions outside this review
