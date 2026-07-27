# Code-mode completion can lose live session handles

A code-mode cell can start nested terminal commands, keep only their output, and discard the returned session IDs while the processes remain live in the session-level unified-exec manager.

The final result can then report `Script completed` without showing the handles needed to inspect, continue, or terminate those commands.

## Relationship to #34866

[#34866](https://github.com/openai/codex/issues/34866) covers the broader mismatch between wrapper completion and nested-process state and discusses richer lifecycle representation.

This report isolates one compatibility-preserving case: recover discarded manager-owned handles in the existing completion status without changing lifecycle policy, JavaScript result fields, or protocol shapes.

## Proposed direction

- retain the originating typed code-mode `CellId` on manager-owned process entries;
- query the existing manager for processes created by the exact terminal cell whose manager-observed state remains live;
- report their logical session IDs deterministically in the existing status text;
- leave ordinary `Yielded` responses unchanged.

## Important boundary

Local handles can expose process exit directly. Exec-server-backed handles rely on exit already reflected in manager state, so a recently exited remote process could appear until cached state advances.

## Exploratory work

The [exploratory implementation and tests](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-ids) demonstrate exact-cell attribution, exited-entry filtering, deterministic formatting, and the discarded-handle end-to-end case.

The [technical deep dive](deep-dive.md) records my implementation reasoning, validation boundary, limitations, and alternatives considered.
