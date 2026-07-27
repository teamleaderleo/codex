# Reviewer brief: iterative Codex issue and triage research

Please conduct an iterative compare-and-contrast study of public `openai/codex` issues. This is a research task, not another wording review of [#35613](https://github.com/openai/codex/issues/35613).

The default workflow is **chat-native qualitative review in batches of five issues**. Do not turn this into a prerequisite 300-row data-collection project. Read a small batch, analyse it closely, save the notes, and repeat.

Do not post comments to #35613 or any related public issue during this research.

## Purpose

Build a grounded understanding of:

- how current Codex issues are written;
- what makes reports easy or difficult to act on;
- how bots, community members, and maintainers respond;
- which strong-looking reports remain unanswered;
- which weak or incomplete reports still receive attention;
- how current issue and triage practice differs from older examples;
- whether #35613 is appropriately scoped and presented for this repository.

Do not assume that an unanswered issue is poor. Maintainer capacity, priority, timing, duplication, roadmap fit, product surface, and issue type can all affect the outcome. Use “associated with engagement,” not “caused engagement,” unless the thread supplies direct evidence.

## Default unit of work: one chat batch

Review **five issues per batch**. A batch should usually contain:

- **three recent issues**, normally created within the last 30 days;
- **two comparison issues**, normally 30–120 days old.

This is an intentional recency weighting, not a probability sample. Current reports receive more weight because templates, product surfaces, models, labels, bots, and maintainer practice can change quickly. Older reports remain useful for observing mature outcomes and avoiding conclusions based only on threads that have had little time to develop.

The 30-day boundary is **not an exclusion rule**. Issues newer than 30 days are valid and important research material. Record their age and avoid interpreting a lack of response as a mature outcome.

A user may instead paste five issues directly into the chat. Analyse the supplied batch even when it contains extraneous text or does not match the preferred age mix. Preserve the supplied order unless another ordering materially helps comparison.

## Batch selection

When selecting issues rather than receiving them from the user:

1. Include both open and closed issues over successive batches.
2. Rotate issue types and product surfaces rather than selecting five near-duplicates.
3. Include ordinary, weak, ambiguous, and high-quality-looking reports—not only memorable successes.
4. Prefer at least one apparent counterexample per batch when available, such as a strong unanswered report or a weak report that received useful attention.
5. Exclude pull requests from issue batches. Review PRs in separate batches.
6. Do not repeatedly sample the same prolific reporter or one narrow label unless the batch is explicitly thematic.
7. Save the search date, query or browsing route, candidate issue numbers, selected issue numbers, and selection rationale.

This is a transparent purposive sample for landscape mapping. Do not report repository-wide response rates or causal claims from it.

## Per-issue review

For each issue, record:

### Basic facts

- issue number and canonical URL;
- title;
- creation date and age at review;
- open or closed state and stated closure reason;
- labels;
- product surface and execution backend where demonstrated, otherwise `unknown`;
- issue author association where available;
- comment count and visible reactions.

### Issue type

Assign one primary type and optional secondary tags:

- reproducible bug;
- intermittent bug;
- model-behaviour report;
- feature request;
- performance or resource problem;
- documentation request;
- support or usage question;
- security or privacy concern;
- meta or process issue;
- unclear or mixed request.

Duplicate or already-tracked status is an outcome, not an issue type.

### Report quality

Score each applicable dimension from 0 to 2. Use `N/A` where a dimension genuinely does not apply.

1. **Title specificity** — names an observable behaviour or concrete request.
2. **User impact** — explains what fails or why it matters.
3. **Actual versus expected behaviour** — both are distinguishable.
4. **Reproduction** — executable or otherwise credible.
5. **Environment** — provides the relevant version, platform, configuration, model, or backend.
6. **Evidence** — logs, outputs, screenshots, artifacts, or source references support the claim.
7. **Scope** — presents one independently actionable problem.
8. **Prior-art awareness** — distinguishes relevant reports instead of dumping links; use `N/A` when no relevant prior art is reasonably discoverable.
9. **Diagnosis discipline** — separates observation, hypothesis, and proposed solution.
10. **First-screen readability** — the core failure and requested invariant are quickly understandable.

Calculate a normalized score over applicable dimensions when useful, but do not let the aggregate number replace the written judgement. Note concrete strengths, weaknesses, and the smallest information improvement that would make the report more actionable.

### Engagement and outcome

Identify bots before considering association. Treat `OWNER`, `MEMBER`, and `COLLABORATOR` as verified maintainer associations. Treat other humans as unverified human/community unless visible repository-authority evidence supports a maintainer classification. Do not infer authority from tone or apparent employment.

Record engagement separately from outcome.

**Engagement:**

- author-only/no external human response;
- bot-only activity;
- unverified human/community response;
- maintainer acknowledgement;
- maintainer information request;
- substantive maintainer response.

Retain multiple event flags when a thread progresses through several stages. Record the highest human-engagement level reached and describe the sequence when it matters.

**Outcome:**

- open unresolved;
- completed/fixed;
- duplicate;
- expected behaviour;
- unsupported or support redirect;
- not planned;
- automated closure;
- other closure.

For recent issues, explicitly state that the outcome is immature when the thread has had little observation time. Time to first maintainer response at 24 hours, 7 days, and 30 days may be recorded as descriptive context, but it is not a gate on inclusion.

### Research value

State why the issue belongs in the landscape map. Examples:

- representative strong report;
- representative low-signal report;
- strong unanswered counterexample;
- weak report with maintainer attention;
- well-written duplicate;
- semantic duplicate-bot error;
- useful product-surface contrast;
- useful old-versus-current practice contrast.

## Batch synthesis

After the five issue reviews, return:

1. a compact comparison table;
2. the main patterns visible in this batch;
3. counterexamples and tensions;
4. what this batch suggests about #35613, without recommending edits from one batch alone;
5. what kinds of issues the next batch should include to test or challenge the emerging picture;
6. confidence and important missing data.

Separate factual observations, interpretation, and uncertainty.

## Saving the work

Store each completed batch in the fork under:

`notes/code-mode-orphan-fix/research/batches/batch-NNN.md`

Each file should contain:

- review date;
- selection method and candidate pool;
- the five issue numbers;
- per-issue coding and evidence notes;
- batch synthesis;
- new or revised hypotheses;
- proposed composition of the next batch.

Maintain a compact ledger at:

`notes/code-mode-orphan-fix/research/batches/ledger.csv`

The ledger should contain one row per issue with the batch number, issue number, dates, primary type, quality score or band, engagement, outcome, and a short research-value tag. Do not mirror full public threads into the repository; issue numbers and evidence references are sufficient.

## How many issues

There is no default requirement to exceed 300 issues.

Start with **six batches / 30 issues**. After every second batch, review whether the coding categories or main conclusions are still changing. Continue in batches of five while new major patterns, counterexamples, product surfaces, or triage behaviours are appearing.

A reasonable qualitative target is **40–80 issues**. Stop when two consecutive diverse batches add no major category or materially change the working conclusions. Record why saturation was judged sufficient.

Run a larger probability-sampled quantitative study only if the qualitative pass produces a specific question that requires a rate estimate. Keep that as a separate phase with its own sampling protocol.

## Related-process cluster

As a focused thematic batch, compare these five reports by failure layer:

- [#35613](https://github.com/openai/codex/issues/35613) — nested JavaScript can discard the result containing `session_id` before the handle becomes model-visible.
- [#34866](https://github.com/openai/codex/issues/34866) — wrapper completion versus nested-process state mismatch.
- [#33816](https://github.com/openai/codex/issues/33816) — a handle reaches the model and is later lost model-side.
- [#35482](https://github.com/openai/codex/issues/35482) — possible process-group, cleanup, sandbox-observability, and resource-safety failure.
- [#35035](https://github.com/openai/codex/issues/35035) — general task incompleteness and likely semantic duplicate-bot noise.

For each, identify:

1. the demonstrated failure point;
2. whether the handle reached JavaScript, reached the model, was later lost, or never surfaced model-side;
3. whether manager ownership is demonstrated, contradicted, or unknown;
4. product surface and execution backend, using `unknown` rather than inference;
5. what #35613 could address;
6. what it definitely would not address;
7. whether a public cross-link would add new evidence or only noise.

The wake-up-after-exit layer remains adjacent context rather than a sixth focal report unless a later batch specifically studies scheduling and notification failures.

## PR research

Keep PRs separate from issue batches. Review PRs in batches of five using the same chat workflow, rotating among maintainer-authored, automated, coordinated external, and unknown external submissions. Do not infer that an external PR was unsolicited merely because public coordination is absent.

## Execution discipline

When asked to run the research, begin with a five-issue batch and save the completed notes. Do not stop at another methodology review unless a concrete data-access problem prevents reading the selected issues or comments.

Do not post public comments as part of the research. Do not recommend changes to #35613 from one memorable comparison. Update conclusions cumulatively as batches accumulate.