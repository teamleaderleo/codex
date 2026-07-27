# Codex issue-quality summary — first 220 reviewed issues

This page is a navigation and distribution summary for the chronological qualitative catalogue. It does not claim repository-wide rates.

## Aggregate score distribution

| Band | Count |
|---|---:|
| S | 25 |
| A | 48 |
| B | 45 |
| C | 48 |
| D | 32 |
| E | 11 |
| F | 11 |
| **Total** | **220** |

The first 120 scores are in [`issue-quality-score-ledger.md`](issue-quality-score-ledger.md). The next 100 scores and judgements are in [`issue-quality-catalog-pass-007-011.md`](issue-quality-catalog-pass-007-011.md).

## Catalogue files

- [`issue-quality-catalog.md`](issue-quality-catalog.md) — first 20 detailed issue reviews.
- [`issue-quality-catalog-pass-002-006.md`](issue-quality-catalog-pass-002-006.md) — next 100 issue reviews.
- [`issue-quality-catalog-pass-007-011.md`](issue-quality-catalog-pass-007-011.md) — next 100 issue reviews, #35501 through #35400.
- [`issue-quality-highlights.md`](issue-quality-highlights.md) — highlights from the first 120.
- [`issue-quality-highlights-pass-007-011.md`](issue-quality-highlights-pass-007-011.md) — highlights from the newest 100.

## Working conclusions

1. **The median issue is usable, not excellent.** B and C are the centre of the catalogue; S is reserved for reports with unusually clean boundaries and evidence.
2. **Triage cost is often created by sophisticated writers.** Architecture documents, product programmes and forensic overproduction remain more common than pure one-line junk.
3. **Damage magnitude and report quality are separate.** Reports involving hundreds of gigabytes, machine lockout or lost processes can still score poorly when ownership and reproduction are weak.
4. **Controlled comparisons dominate.** The best reports compare one surface, state, version or execution path against a closely matched control.
5. **Small protocol and state invariants outperform broad redesigns.** Exact enum mismatches, missing environment values, stale pointers, lifecycle transitions and serialization failures produce the clearest next actions.
6. **The process-lifecycle cluster keeps expanding without collapsing into one bug.** Live-process ownership, missing handles, lost UI state, deleted-open logs, process reaping and resource ceilings occur at different layers.
7. **#35613 remains unusually well bounded.** It identifies one handle-visibility failure and does not claim to solve every orphan-process or lifecycle problem.

Next chronological boundary: immediately below #35400.