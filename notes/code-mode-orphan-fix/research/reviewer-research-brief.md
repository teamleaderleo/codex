# Reviewer guide: Codex issue-quality research

Review public `openai/codex` issues to build a cumulative catalogue of report quality, triage friction, implementation value, recurring submission patterns, author activity and useful counterexamples.

This is an execution guide. Do not stop for another methodology discussion when the selected public issues can be read. Do not post comments, reactions, reviews, labels or edits to upstream issues or pull requests.

Canonical navigation and coverage live in [`issues/README.md`](issues/README.md). Use [`issues/TEMPLATE.md`](issues/TEMPLATE.md) for every new range.

## Default unit of work

Review **exactly 20 unique public issues per pass**.

One completed pass produces one canonical file:

```text
notes/code-mode-orphan-fix/research/issues/<low>-<high>.md
```

The filename uses the inclusive repository-number interval, not a pass number. Pull requests inside the interval are skipped and listed in the header.

Do not combine five ranges into one 100-issue file. Do not update a separate score ledger for new canonical ranges; the range file itself is authoritative.

## Selection modes

### Current/new snapshot

Use when the user asks for recent or newly filed material.

1. Search public `openai/codex` issues by creation time, newest first.
2. Collect the newest 20 unique issues visible at the snapshot.
3. Exclude pull requests and overlap with the prior current range.
4. Record the collection date, low/high issue numbers and skipped PRs.
5. State any gap between this range and older systematic coverage.

The current boundary is maintained in [`issues/README.md`](issues/README.md).

### Historical backfill

Use when continuing continuous older coverage.

1. Start immediately below the completed historical boundary.
2. Collect the next 20 unique public issues.
3. Skip pull requests and record them.
4. Preserve issue-number order inside the range.
5. Save the range before starting another.

### User-supplied set

When the user supplies specific issues, review those issues in the supplied order. Clearly label the file as a targeted set rather than pretending it is a contiguous systematic range.

## Source and reading rules

- Use `openai/codex` as the canonical source for issue bodies, state, labels and comments.
- Read the full current issue body before grading.
- Search snippets are discovery aids, not sufficient evidence for a score.
- Read comments only when needed for duplicate distinctions, closure reason, existing behavior, maintainer requests, implementation outcomes or a useful counterexample.
- Identify bots before classifying engagement.
- Do not infer maintainer authority from tone, username, employer appearance or technical confidence.
- Do not mirror complete public issue bodies into the fork.

## What is being judged

Judge the submitted report, not whether the requested feature should ultimately be implemented.

Keep three lenses separate:

1. **Issue quality** — clarity, evidence and triage usefulness.
2. **Repository actionability** — whether `openai/codex` appears to own an efficient next step.
3. **Implementation value** — whether code, artifacts or source analysis materially reduce remaining engineering work.

A polished issue can still score poorly when it is a literal duplicate, requests existing behavior, belongs to support or another product, or substitutes a broad architecture programme for one bounded issue.

## Issue-quality score: 30 points

Score six dimensions from **0 to 5**.

1. **Clarity** — title and opening identify an observable failure or concrete request.
2. **Scope discipline** — one independently actionable problem without avoidable bundling.
3. **Reproduction/current-state verification** — credible trigger and controls, or a demonstrated current-versus-desired feature gap.
4. **Evidence** — logs, outputs, screenshots, measurements, source anchors or controls proportional to the claim.
5. **Context** — relevant version, platform, model/backend, configuration, prior art and privacy-safe identifiers.
6. **Actionability/diagnosis discipline** — observations, hypotheses and proposals are separated; owner and next step are reasonably clear.

Do not reward length, code blocks, source inspection, a prototype or polished formatting automatically.

### Bands

| Band | Score | Meaning |
|---|---:|---|
| **S** | 29–30 | Exceptional exemplar; essentially no material triage defect |
| **A** | 27–28 | Excellent; immediately actionable with only minor defects |
| **B** | 24–26 | Strong; actionable but meaningfully improvable |
| **C** | 20–23 | Usable or mixed; notable evidence, scope or owner gaps |
| **D** | 15–19 | Weak/costly; substantial reconstruction or narrowing required |
| **E** | 10–14 | Severely deficient, duplicate or badly mis-scoped |
| **F** | 0–9 | Non-report, near-content-free complaint or unusable submission |

Do not force a curve. Record scores as `26/30 · B`. Show a six-component breakdown only for disputed grades, close calls or deliberate calibration examples.

### Calibration

- A literal duplicate adding no material evidence normally cannot exceed **E**.
- A support-only or clearly wrong-owner request normally cannot exceed **D** unless it identifies a concrete repository change.
- A report with no bounded symptom/request and no usable verification normally cannot exceed **E**.
- Hostility is not an automatic cap, but hostility replacing facts lowers clarity and actionability.
- Excess detail loses points only when it materially impedes first-screen comprehension, scope or the next step.
- An unresolved policy choice does not lower a score when the minimum demonstrated defect remains independently actionable.
- Do not deduct points merely to leave room below perfection. A defensible `5+5+5+5+5+5` is **30/30**.

## Implementation-value lens

Apply only when the issue contains linked code or artifacts, an explicit source-level proposal, a validated local implementation, or an exact prior implementation. Routine issues remain unmarked rather than receiving `0/5` noise.

| Value | Meaning |
|---:|---|
| **5/5** | Inspectable tested implementation or exact known-good merged fix; substantial maintainer time saved |
| **4/5** | Patch-ready proposal or validated but unlinked/uninspected implementation with exact locations, invariants and tests |
| **3/5** | Useful diagnosis and credible direction, but meaningful design, assembly or validation remains |
| **2/5** | Partial/speculative idea that may save search time but little coding time |
| **1/5** | Solution-shaped prose or questionable correction that may distract |

Types:

- **WORKING** — linked code, commit, branch or completed artifact.
- **KNOWN-GOOD** — exact prior merged implementation for the same regression.
- **PATCH-READY** — no inspectable submitted patch, but change points, semantics and tests are bounded.
- **DIAGNOSTIC** — source analysis locates the work but leaves meaningful correction design.
- **SOLUTIONEERING** — implementation language outruns evidence or leaves the core decision unresolved.

Judge what remains for a maintainer. Strong signals include before/after tests, narrow diffs, compatibility defaults, cleanup/concurrency semantics, validation commands and exact prior art.

Lower value for hypothetical reproduction, arbitrary constants, incomplete failure semantics, partial success without contract, broad architecture substitution, or code that does not satisfy the stated expected behavior.

Keep implementation value independent of the `/30` score. Example:

```text
18/30 · D · implementation 5/5 WORKING
```

The curated cross-range calibration file is [`issue-implementation-value.md`](issue-implementation-value.md). New range files remain authoritative for their own inline values.

## Highlight flags

Flags do not change scores.

- **ULTRA** — exceptional exemplar, normally an S report.
- **INTERESTING** — unusual technical pattern, useful counterexample or instructive anti-pattern.
- **ENTERTAINING** — memorable, strange or spectacular; not a quality endorsement.

There is no quota. Do not force a flag onto routine strong issues. Every flag needs a one-line reason in the highlights section.

## Canonical per-issue row

Record:

- creation time in UTC;
- issue number and canonical URL;
- public author handle;
- concise title;
- primary type;
- score, band and flags;
- implementation value/type only when applicable;
- strongest useful feature;
- main defect or triage cost.

Primary types:

- reproducible bug;
- intermittent bug;
- model-behavior report;
- performance/resource problem;
- feature request;
- documentation request;
- support/usage question;
- security/privacy concern;
- meta/process issue;
- unclear/mixed request.

Duplicate status is an outcome/flag, not a primary type.

## Author activity map

Every canonical range includes an author map.

- Use only the public handle and submissions observed in the reviewed range.
- State surfaces, technical focus and demonstrated submission pattern.
- Give more attention to repeated authors, because multiple submissions support stronger pattern statements.
- For a single submission, describe only that submission.
- Do not infer real identity, employer, coordination, use of AI, motives, expertise or bad faith.
- Do not describe near-simultaneous reports as coordinated without direct evidence.
- A future global author index should be built only from canonical range maps, not by guessing from legacy prose.

## Comments, duplicates and outcomes

Do not fetch every comment thread by default.

Read comments when necessary to determine:

- literal versus merely related duplication;
- already-supported behavior;
- closure reason;
- maintainer request for information;
- implementation acceptance/rejection;
- useful divergence between issue quality and outcome.

A bot duplicate suggestion is not a duplicate finding. Compare the actual failure layer, trigger and requested invariant.

Keep issue quality, engagement and outcome separate. Same-day silence is not negative evidence.

## Range synthesis

Each 20-issue file records:

1. distribution, median and optional mean;
2. strongest reporting structures;
3. recurring triage costs;
4. implementations and patch-ready proposals;
5. issue-quality/implementation-value inversions;
6. duplicates, existing behavior and owner ambiguity;
7. author patterns supported by the range;
8. new categories or rubric revisions;
9. whether the range changes the assessment of #35613;
10. exact current and historical next boundaries.

Do not present range rates as repository-wide population estimates.

## Storage and legacy material

Canonical new files:

```text
notes/code-mode-orphan-fix/research/issues/<low>-<high>.md
```

Canonical index:

```text
notes/code-mode-orphan-fix/research/issues/README.md
```

Legacy catalogue files remain historical snapshots. Do not migrate all old material during a normal 20-issue pass. Migrate one old 20-issue range at a time only when requested.

## GitHub links and notifications

Ordinary public issue/PR links inside committed repository Markdown files do **not** create upstream issue timeline events or notify participants. The repository files remain public and discoverable.

Do not assume the same for issue/PR bodies, comments, reviews or commit messages associated with upstream work; those can create cross-references or notifications.

This research does not post upstream references, comments, reactions, labels or edits unless the user explicitly requests a separate public action.

## Repository write safety

- Work only on the authorized fork branch.
- Before replacing or deleting an existing file, fetch its current blob SHA.
- Do not use issues as temporary storage.
- Do not create workflows or dispatch automation for this research.
- Preserve public links but never include private logs, tokens, account identifiers or personal paths.

## Relation to #35613

Use the catalogue to test whether #35613 is unusually strong, overlong, mis-scoped, confused with adjacent lifecycle reports, or unusually valuable as an implementation contribution.

Do not broaden #35613 merely because other reports are broad. Its comparator remains whether it states one demonstrated failure layer, separates observation from hypothesis, distinguishes related reports, gives maintainers a bounded next step and reduces implementation uncertainty.
