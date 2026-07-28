# Legacy snapshot: first 220 reviewed Codex issues

This file preserves the aggregate and conclusions from the first 220 systematically reviewed `openai/codex` issues. It is no longer the navigation entry point.

Use the canonical index instead:

[`issues/README.md`](issues/README.md)

The canonical index adds the newer 20-issue range #35731–#35753, tracks known coverage gaps, and defines the current/new versus historical-backfill boundaries.

## Aggregate score distribution at the 220-issue snapshot

| Band | Count |
|---|---:|
| S | 26 |
| A | 47 |
| B | 45 |
| C | 48 |
| D | 32 |
| E | 11 |
| F | 11 |
| **Total** | **220** |

These counts do not include the canonical #35731–#35753 range. Current combined counts are maintained in [`issues/README.md`](issues/README.md).

## Legacy catalogue files

- [`issue-quality-catalog.md`](issue-quality-catalog.md) — first 20 detailed reviews, #35616 through #35637.
- [`issue-quality-catalog-pass-002-006.md`](issue-quality-catalog-pass-002-006.md) — next 100 reviews, #35502 through #35615.
- [`issue-quality-catalog-pass-007-011.md`](issue-quality-catalog-pass-007-011.md) — next 100 reviews, #35400 through #35501.
- [`issue-quality-score-ledger.md`](issue-quality-score-ledger.md) — authoritative calibrated scores for the first 120.
- [`issue-quality-highlights.md`](issue-quality-highlights.md) and [`issue-quality-highlights-pass-007-011.md`](issue-quality-highlights-pass-007-011.md) — legacy highlight indexes.

New work uses one file per 20 issues under [`issues/`](issues/).

## Conclusions preserved from this snapshot

1. **The median issue is usable, not excellent.** B and C form the centre of this sample.
2. **Triage cost is often created by sophisticated writers.** Architecture documents, product programmes and forensic overproduction can be more expensive than short weak reports.
3. **Damage magnitude and report quality are separate.** Severe resource or process incidents can still be weakly isolated.
4. **Controlled comparisons dominate.** The best reports compare one state, version, execution path or surface with a closely matched control.
5. **Small protocol and state invariants outperform broad redesigns.** Exact mismatches, stale pointers and lifecycle transitions create efficient next actions.
6. **The process-lifecycle cluster contains multiple distinct layers.** Ownership, missing handles, UI state, deleted-open logs, process reaping and resource ceilings should not be collapsed into one bug.
7. **#35613 is a 30/30 exemplar.** It proves one lost-handle invariant, bounds the correction and carries a 5/5 working implementation contribution.

## Historical boundary

Historical backfill continues immediately below **#35400**. Current/new collection continues above the latest range recorded in [`issues/README.md`](issues/README.md).
