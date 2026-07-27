# Reviewer brief: chronological Codex issue-quality catalog

Review public `openai/codex` issues to build a cumulative catalogue of report quality, triage friction, recurring submission patterns, and useful counterexamples.

This is an execution task. Do not stop for another methodology review unless the selected public issues cannot be read.

Do not post comments or reactions to public issues during this research.

## Default workflow

Review **20 issues per chat pass**.

Use one contiguous chronological block of public issue numbers:

1. start immediately below the most recently completed block;
2. skip pull-request numbers but record that they were skipped;
3. read the full issue body rather than grading from a search snippet;
4. order the catalogue rows from oldest to newest inside the block;
5. save the completed block into the cumulative catalogue before moving on.

Twenty is a working default, not a hard limit. Reduce the batch only when several reports are exceptionally long or contain attachments that require separate inspection. Increase it only when the issues are short and the analysis remains substantive.

A user may instead paste a batch directly into chat. Analyse the supplied issues in the supplied order even when the pasted material contains extraneous metadata.

## Recency

There is **no 30-day inclusion cutoff**.

Recent reports are important because templates, product surfaces, models, labels, and issue-writing practices change quickly. Older reports are important because their outcomes have had time to develop.

For a chronological catalogue, record issue age and do not interpret same-day silence as evidence about report quality or maintainer interest.

## What to judge

Judge the submitted report, not whether the requested feature should be implemented.

Keep two concepts separate:

- **writing/evidence quality:** how clearly and credibly the issue presents its case;
- **repository actionability:** whether the Codex repository appears to be the right owner and whether the report creates an efficient next step.

A polished issue may still be low-value because it is a literal duplicate, asks for an existing feature, belongs to another product surface, or specifies a broad product programme without demonstrating a defect.

## Quality grades

Assign one overall grade and a short written justification.

- **A — strong/actionable:** the failure or request, affected surface, evidence, scope, and next investigative step are quickly identifiable.
- **B — usable:** the core issue is understandable and potentially actionable, but important evidence, scope control, or product fit is missing.
- **C — costly/mis-scoped:** there may be a real issue, but the submission creates substantial triage work through overbreadth, weak evidence, excessive solutioning, or poor repository fit.
- **D — weak/noisy:** vague, hostile, bundled, unsupported, or lacking enough information to investigate efficiently.

Add independent catalogue flags where applicable:

- literal duplicate submission;
- likely wrong repository or product owner;
- already-supported behaviour;
- multiple unrelated issues;
- excessive forensic detail;
- large prompt or proposed design burying the core issue;
- unsupported causal certainty;
- missing reproduction or environment;
- semantic duplicate-bot mismatch;
- unusually strong counterexample.

Do not reward length, source inspection, code suggestions, or a prototype automatically.

## Per-issue catalogue row

For every issue, record:

- issue number and canonical URL;
- creation time;
- title;
- primary issue type;
- open/closed state and explicit state reason when visible;
- overall grade;
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

## Detailed notes

Do not write a ten-dimension table for all twenty issues.

After completing the twenty concise rows, choose only the issues that materially teach something and add deeper notes. Normally this means three to six cases such as:

- the weakest submission;
- a polished but low-actionability submission;
- a strong concise report;
- a strong but excessively long report;
- a literal duplicate;
- a counterexample that challenges the current catalogue categories.

For those cases, examine title, impact, actual/expected distinction, reproduction, environment, evidence, scope, prior art, diagnosis discipline, and first-screen readability.

## Comments and outcomes

The main catalogue concerns issue-body quality. Do not fetch every comment thread by default.

Read comments when they are needed to determine:

- why an issue was closed;
- whether it was a literal or semantic duplicate;
- whether the requested behaviour already existed;
- whether a maintainer asked for missing information;
- whether the thread supplies a useful quality/outcome counterexample.

Identify bots before classifying human engagement. Do not infer maintainer authority from tone, username, apparent employer, or technical confidence.

Keep engagement and outcome separate. A good report can remain unanswered; a weak report can be fixed for roadmap reasons.

## Block synthesis

After each twenty-issue block, record:

1. grade distribution;
2. recurring forms of strong reporting;
3. recurring forms of avoidable triage cost;
4. literal duplicates or already-supported requests;
5. examples where writing quality and repository actionability diverge;
6. new catalogue categories or revisions to existing categories;
7. whether the block changes any conclusion about #35613;
8. the exact number interval for the next chronological block.

Separate factual observations from interpretation.

Do not report repository-wide percentages as if this were a probability sample. Counts within a reviewed chronological block are acceptable when clearly labelled as block counts.

## Storage

Maintain the primary output at:

`notes/code-mode-orphan-fix/research/issue-quality-catalog.md`

Append each chronological block to that file. Do not mirror full public issue bodies into the fork.

Optionally maintain a compact CSV ledger with one row per issue when the catalogue becomes too large to scan manually.

Avoid creating a separate tiny file for every five issues unless a thematic deep dive genuinely needs its own document.

## How far to continue

Begin with five chronological blocks: approximately **100 issues**.

After each block, ask whether new quality patterns or counterexamples are still appearing. Continue while the catalogue is changing materially. Stop when two consecutive diverse blocks add no important category and do not change the working conclusions.

A larger probability-sampled survey is a separate optional phase. Do not make it a prerequisite for getting the lay of the land.

## Relation to #35613

Use the catalogue to test whether #35613 is unusually strong, weak, overlong, mis-scoped, or likely to be confused with nearby reports.

Do not recommend broadening #35613 merely because other issues are broad. Its relevant comparison remains whether it states one demonstrated failure layer, separates observation from hypothesis, distinguishes related reports, and gives maintainers a bounded next step.

Do not post cross-links or edits to public issues as part of this research.