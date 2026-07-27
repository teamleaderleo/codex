# Reviewer brief: chronological Codex issue-quality catalog

Review public `openai/codex` issues to build a cumulative catalogue of report quality, triage friction, recurring submission patterns, and useful counterexamples.

This is an execution task. Do not stop for another methodology review unless the selected public issues cannot be read. Do not post comments or reactions to public issues.

## Default workflow

Review **100 unique issues per chat pass**, internally checkpointed as five groups of 20 so grading remains careful.

Use a contiguous chronological range of public issue numbers:

1. start immediately below the most recently completed boundary;
2. skip pull-request numbers and record them as skipped;
3. exclude repeated records returned at connector/search boundaries;
4. read the full issue body before grading;
5. preserve chronological order within each 20-issue checkpoint;
6. save the completed pass before continuing.

A user may instead paste a batch directly into chat. Analyse supplied issues in the supplied order even when the material includes extraneous metadata.

There is no 30-day inclusion cutoff. Recent issues are valuable for current writing practice; older issues are valuable for mature outcomes. Do not treat same-day silence as evidence about issue quality or maintainer interest.

## What is being judged

Judge the **submitted report**, not whether the requested feature should ultimately be implemented.

Keep separate:

- **writing/evidence quality** — how clearly and credibly the issue establishes its case;
- **repository actionability** — whether `openai/codex` appears to be the right owner and whether the report creates an efficient next step.

A polished issue can still score poorly when it is a literal duplicate, asks for existing behaviour, belongs to another product or support channel, or replaces a bounded issue with a broad architecture programme.

## 30-point scoring rubric

Score six dimensions from **0 to 5**. The total out of 30 is the primary result.

1. **Clarity** — the title and opening identify the observable failure or concrete request.
2. **Scope discipline** — one independently actionable problem; no avoidable bundling or umbrella design.
3. **Reproduction or current-state verification** — a bug has a credible trigger/control; a feature request establishes current versus desired behaviour and a real use case.
4. **Evidence** — logs, outputs, screenshots, measurements, source anchors, controls, or other support proportional to the claim.
5. **Context** — relevant version, platform, model/backend, configuration, prior art, and privacy-safe identifiers.
6. **Actionability and diagnosis discipline** — observations, hypotheses, and proposed solutions are separated; the likely repository owner and next step are reasonably clear.

Do not reward length, source inspection, code suggestions, a prototype, or polished formatting automatically.

### Grade bands

| Band | Score | Meaning |
|---|---:|---|
| **S** | 29–30 | Exceptional exemplar; essentially no material triage defect |
| **A** | 27–28 | Excellent; immediately actionable with only minor defects |
| **B** | 24–26 | Strong; actionable but meaningfully improvable |
| **C** | 20–23 | Usable or mixed; notable missing evidence, scope cost, or owner uncertainty |
| **D** | 15–19 | Weak/costly; substantial reconstruction or narrowing required |
| **E** | 10–14 | Severely deficient, duplicate, or badly mis-scoped |
| **F** | 0–9 | Non-report, near-content-free complaint, or unusable submission |

Do not force a curve. **S must remain rare**, and A is not the default label for every actionable report.

Record catalogue rows as, for example, `26/30 · B`. The number is primary; the letter is only a summary. Show component scores only for close calls, disputed grades, or deep-dive examples.

### Calibration rules

- A literal duplicate that adds no material evidence normally cannot exceed **E**.
- A support-only or clearly wrong-owner request normally cannot exceed **D** unless it identifies a concrete repository change.
- A report with no bounded symptom/request and no usable reproduction/current-state verification normally cannot exceed **E**.
- Hostile language is not an automatic cap when the technical report remains strong, but hostility that replaces facts lowers clarity and actionability.
- Excessive detail lowers the score only when it materially impedes scope, first-screen comprehension, or next-step identification.

## Per-issue catalogue entry

Record:

- issue number and canonical URL;
- creation time;
- title and primary type;
- open/closed state and explicit reason when visible;
- score out of 30 and band;
- strongest useful feature;
- main defect or triage cost;
- one short catalogue tag.

Use these primary types:

- reproducible bug;
- intermittent bug;
- model-behaviour report;
- performance or resource problem;
- feature request;
- documentation request;
- support or usage question;
- security or privacy concern;
- meta or process issue;
- unclear or mixed request.

Duplicate status is an outcome or catalogue flag, not an issue type.

## Comments and outcomes

The main catalogue concerns issue-body quality. Do not fetch every comment thread by default.

Read comments when needed to determine closure reason, literal or semantic duplication, existing functionality, a maintainer information request, or a useful quality/outcome counterexample.

Identify bots before classifying human engagement. Do not infer maintainer authority from tone, username, apparent employer, or technical confidence. Keep engagement and outcome separate.

## Pass synthesis

After each 100-issue pass, record:

1. score and band distribution;
2. median and notable score clusters;
3. recurring forms of strong reporting;
4. recurring forms of avoidable triage cost;
5. literal duplicates, wrong-owner requests, and already-supported behaviour;
6. cases where writing quality and repository actionability diverge;
7. new catalogue categories or revisions;
8. whether the pass changes any conclusion about #35613;
9. the exact next chronological boundary.

Do not present chronological-pass counts as repository-wide population estimates.

## Storage

Primary qualitative observations:

`notes/code-mode-orphan-fix/research/issue-quality-catalog*.md`

Primary calibrated scores:

`notes/code-mode-orphan-fix/research/issue-quality-score-ledger.md`

Do not mirror full public issue bodies into the fork.

## Relation to #35613

Use the catalogue to test whether #35613 is unusually strong, weak, overlong, mis-scoped, or likely to be confused with nearby reports.

Do not recommend broadening #35613 merely because other issues are broad. Its relevant comparison remains whether it states one demonstrated failure layer, separates observation from hypothesis, distinguishes related reports, and gives maintainers a bounded next step.

Do not post cross-links or edits to public issues as part of this research.
