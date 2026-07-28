# Codex issue research index

This directory is the canonical home for public `openai/codex` issue-quality research.

Each new catalogue file covers **exactly 20 unique public issues**. The filename records the inclusive repository-number interval as `<low>-<high>.md`. Pull requests inside the interval are skipped and listed explicitly in the file header.

## Current canonical ranges

| Range file | Issues reviewed | Selection mode | Skipped PRs | Notes |
|---|---:|---|---|---|
| [`35731-35753.md`](35731-35753.md) | 20 | newest/current snapshot | #35738, #35742, #35744 | First file in the canonical format; includes inline quality scores, implementation value, flags, author map and synthesis. |

## Coverage map

### Systematically reviewed

| Repository-number coverage | Issue count | Storage | Status |
|---|---:|---|---|
| #35731–#35753 | 20 | [`35731-35753.md`](35731-35753.md) | Canonical format |
| #35616–#35637 | 20 | [`../issue-quality-catalog.md`](../issue-quality-catalog.md) plus [`../issue-quality-score-ledger.md`](../issue-quality-score-ledger.md) | Legacy format; calibrated ledger is authoritative for scores |
| #35502–#35615 | 100 | [`../issue-quality-catalog-pass-002-006.md`](../issue-quality-catalog-pass-002-006.md) plus [`../issue-quality-score-ledger.md`](../issue-quality-score-ledger.md) | Legacy format; calibrated ledger is authoritative for scores |
| #35400–#35501 | 100 | [`../issue-quality-catalog-pass-007-011.md`](../issue-quality-catalog-pass-007-011.md) | Legacy 100-issue file using the current numeric rubric |

### Known gaps and targeted reviews

- **#35638–#35730** has not been reviewed as one systematic range.
- #35683 received a targeted deep review because it blocks the Windows/Wine validation path for #35613.
- #35613 received a targeted implementation and validation audit beyond its catalogue entry.
- Historical backfill below **#35400** remains open.

Do not imply continuous coverage across the #35638–#35730 gap.

## Aggregate distribution — 240 systematically reviewed issues

| Band | Count |
|---|---:|
| S | 31 |
| A | 54 |
| B | 50 |
| C | 51 |
| D | 32 |
| E | 11 |
| F | 11 |
| **Total** | **240** |

These counts combine the legacy 220-issue catalogue and the canonical #35731–#35753 range. They describe the reviewed samples only, not the repository-wide issue population.

## Canonical range contents

Every range file should include:

1. collection/review date and selection mode;
2. inclusive repository-number interval;
3. skipped pull-request numbers;
4. score distribution and median;
5. one row per issue with author, type, `/30` score, flags, implementation value when applicable, strongest value and main triage cost;
6. curated ULTRA, INTERESTING and ENTERTAINING highlights;
7. an author activity map limited to observed public submissions;
8. batch synthesis and exact next boundaries.

Use [`TEMPLATE.md`](TEMPLATE.md) for new ranges and [`../reviewer-research-brief.md`](../reviewer-research-brief.md) for the full ruleset.

## Selection tracks

### Current/new issues

Use this when the user asks what has happened recently:

- collect the newest 20 unique public issues visible at the review snapshot;
- exclude pull requests and overlap with the last current range;
- record the collection cutoff and any repository-number gap;
- do not pretend the resulting range is a chronological continuation of historical backfill.

The next current batch begins **above #35753**.

### Historical backfill

Use this for continuous older coverage:

- continue immediately below the completed historical boundary;
- take the next 20 unique issues;
- record skipped pull requests;
- preserve the exact low/high interval in the filename.

The next historical batch begins **below #35400**.

## Cross-cutting files

- [`../reviewer-research-brief.md`](../reviewer-research-brief.md) — authoritative reviewer guide.
- [`../issue-implementation-value.md`](../issue-implementation-value.md) — curated implementation-value calibration examples; not an exhaustive ledger.
- [`../related-issue-cluster.md`](../related-issue-cluster.md) — process-lifecycle map around #35613.
- [`../issue-quality-highlights.md`](../issue-quality-highlights.md) and [`../issue-quality-highlights-pass-007-011.md`](../issue-quality-highlights-pass-007-011.md) — legacy highlight indexes.
- [`../issue-quality-summary-220.md`](../issue-quality-summary-220.md) — legacy 220-issue snapshot; current navigation lives here.

## GitHub link and notification behavior

Ordinary links to public issues or pull requests inside committed repository Markdown files do **not** create upstream issue timeline events or notify issue participants. These files are still public and discoverable.

Do not assume the same for references placed in issue/PR bodies, comments, reviews, or commit messages associated with upstream work; those surfaces can create cross-references or notifications. This research must not post upstream comments, reactions, reviews, labels or edits unless the user explicitly requests that separate action.

## Legacy policy

Legacy files remain in place as historical evidence. Do not rewrite all 220 older entries merely to match the new layout during a 20-issue pass. New work uses the canonical format, and older material can be migrated one 20-issue range at a time when specifically requested.
