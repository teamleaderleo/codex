# Reviewer brief: compare recent Codex issues and triage outcomes

Please conduct a structured compare-and-contrast study of recent `openai/codex` issues. This is an execution brief, not another wording review of [#35613](https://github.com/openai/codex/issues/35613).

Treat the protocol below as approved unless data access reveals a concrete methodological blocker. When the methodology is feasible, state **Methodology is ready** and continue directly into the survey in the same task. Do not stop after the readiness statement.

Do not post comments to #35613 or any related public issue during this research.

## Purpose

The goal is to understand:

- how recent issues are formatted;
- how often they receive bot, unverified-human/community, or verified-maintainer responses;
- which report characteristics are associated with useful triage;
- which apparently strong reports remain unanswered;
- what kinds of submissions create noise or are difficult to act on;
- whether #35613 is appropriately scoped and presented for this repository.

Do not assume that an unanswered issue is poor. Maintainer capacity, priority, roadmap fit, timing, duplication, and issue type can all affect the outcome.

Use “associated with engagement,” not “caused engagement,” unless a thread supplies direct evidence.

## Fixed observation point and saved artifacts

Before collecting data, freeze one exact UTC observation timestamp, `T`.

Evaluate issue state, comments, labels, assignments, reactions, linked fixes, and closure information as they existed at `T`. Do not mix observations collected after `T` into the coded dataset.

Save enough information to reproduce the study:

- `study-config.json` containing `T`, date bounds, sample sizes, random seed, sampling algorithm, and coding version;
- the complete deduplicated issue frame;
- the selected mature and freshness issue IDs;
- the coded issue table;
- the deep-read selections and their stratum assignments;
- any unavailable fields or API limitations.

## Cohorts

### Mature issue cohort

Build a frame of all non-PR issues that satisfy:

- repository: `openai/codex`;
- `created_at >= 2026-04-01T00:00:00Z`;
- `created_at <= T - 30 days`;
- state: open or closed.

The upper bound must be calculated from the exact timestamp rather than inferred from calendar dates. If collection tooling can operate only on whole dates, use a conservative whole-day cutoff that guarantees 30 complete days of observation.

Sample exactly 300 issues without replacement when at least 300 are eligible. If fewer are eligible, use the complete frame and report the smaller denominator.

### Freshness cohort

Build a separate frame of all non-PR issues satisfying:

- `created_at > T - 30 days`;
- `created_at <= T`;
- state: open or closed.

Sample exactly 50 issues without replacement when at least 50 are eligible. Use this cohort only to identify changes in templates, labels, bots, and triage practice. Do not include it in the mature cohort’s 30-day response or no-response rates.

### Complete-frame construction and deterministic sampling

Do not rely on one GitHub Search API result set. Search results are capped and can omit most of a large cohort.

Construct each complete frame through the paginated Issues API or through date partitions small enough to remain below every retrieval cap. Deduplicate by repository and issue number, exclude records that contain pull-request metadata, and sort the final frame by issue number before sampling.

Use a recorded integer seed and a specified deterministic algorithm. The default procedure is:

1. sort eligible issue numbers ascending;
2. initialise Python `random.Random(seed)`;
3. call `sample(issue_numbers, n)` without replacement;
4. sort the selected IDs ascending for storage and review.

Use the same recorded procedure for the mature and freshness samples, with separately recorded seeds or deterministic seed derivations.

## Actor and maintainer identification

Identify automated actors before considering repository association. Use account type, a recognised bot identity, or an explicit `[bot]` account marker. A bot’s `author_association` does not make it a human maintainer response.

For human actors:

- count `OWNER`, `MEMBER`, or `COLLABORATOR` as verified maintainer associations;
- allow another authority classification only when repository authority is separately documented and record the evidence;
- classify every other human as **unverified human/community**;
- when association data is unavailable, preserve that uncertainty rather than assuming community or maintainer status.

Do not infer authority from tone, profile text, apparent employment, code familiarity, or contribution history. Describe maintainer-response rates as conservative where private organisation membership or missing association data could hide maintainer status.

Apply the same identity rules to comments and to visible triage actions such as assignment, closure, and label changes.

## Response and outcome coding

Do not combine engagement and disposition into one category. Code them on separate axes and retain event-level flags when several kinds of engagement occur.

### Engagement axis

Assign one highest human-engagement level by the following order:

1. **Author-only/no external human response** — no human comment other than the issue author’s own follow-up.
2. **Unverified human/community response** — at least one external human comment, but no verified maintainer comment.
3. **Maintainer acknowledgement** — verified maintainer receipt or classification without analysis or a request for new information.
4. **Maintainer information request** — verified maintainer request for reproduction, logs, versions, clarification, or narrower scope.
5. **Substantive maintainer response** — diagnosis, workaround, source reference, design discussion, confirmation, prioritisation, or a concrete next step.

Record bot activity separately as `bot_response_present`. An author-only issue with a bot duplicate suggestion is therefore not treated as human engagement.

Retain Boolean event flags for acknowledgement, information request, substantive response, community response, and bot response even when the highest engagement category is used in summary tables.

### Outcome axis

Assign one disposition as of `T`:

- **open unresolved**;
- **completed/fixed** — linked fix, merged PR, confirmed release, or closure as completed;
- **duplicate**;
- **expected behaviour**;
- **unsupported or support redirect**;
- **not planned**;
- **automated closure** — stale or another automation-driven closure without a substantive disposition;
- **other closure**.

Use explicit issue state, state reason, closing comment, linked PR, or release evidence. Do not infer a fix solely because a similar code change exists elsewhere.

Record labels, assignments, closure, reopening, and linked fixes separately as triage actions. They are not substitutes for a verified maintainer human comment.

### Timing measures

Measure from issue creation to the first verified maintainer human comment. Report the proportions receiving one within:

- 24 hours;
- 7 days;
- 30 days.

Also record time to first visible triage action separately. If no verified maintainer comment exists by `T`, code the comment time as right-censored rather than zero or missing-at-random.

## Issue-type controls

Assign one primary issue type before inspecting response and outcome variables. Use this precedence when several types apply:

1. security or privacy concern;
2. documentation request;
3. support or usage question;
4. feature request;
5. model-behaviour report;
6. performance or resource problem;
7. reproducible bug;
8. intermittent bug;
9. meta or process issue;
10. unclear or mixed request.

Add optional secondary tags such as performance, resource safety, sandbox, model behaviour, regression, or documentation when useful. Treat reproducibility as a quality/evidence property as well as a possible bug subtype.

Duplicate or already-tracked status belongs on the outcome axis, not in the primary issue type.

Do not compare raw response rates across primary types without stratifying or otherwise noting the category differences.

## Quality scoring

Score all mature-cohort sampled issues, not only the deep-read cases. This is required for cohort-level response rates by quality band and for selecting strong unanswered counterexamples without circular judgement.

Where practical, score the issue title and body before viewing comments, labels, reactions, state, closure, linked work, or author identity. Preserve a `scoring_blinded` field indicating whether this was achieved.

Use the issue version that existed immediately before the first verified maintainer response when edit history permits. Otherwise use the version available at `T`, record whether it was edited after feedback, and flag `pre_response_text_uncertain`. Do not present an edited-after-response score as an unqualified predictor of engagement.

For every dimension use:

- `0` — absent, materially unclear, or misleading;
- `1` — present but incomplete, indirect, or difficult to use;
- `2` — clear, specific, and decision-useful;
- `N/A` — genuinely inapplicable to that issue type, with a short reason.

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Title specificity | Vague complaint or solution-only title | Names an area or symptom but not a clear observable failure | States a specific observable behaviour or requested change |
| User impact | No consequence stated | Consequence is implied or generic | Concrete failure, risk, or blocked workflow is explained |
| Actual versus expected | Not distinguishable | One side is incomplete or scattered | Actual and expected behaviour are both clear |
| Reproduction | None or not credible | Partial steps, intermittent description, or missing key condition | Minimal executable steps or another credible reproduction path |
| Environment | Relevant context absent | Some version/platform/configuration data | All environment details needed to interpret the report |
| Evidence | Assertion only | Limited or weakly connected evidence | Useful logs, outputs, screenshots, artifacts, or source references tied to the claim |
| Scope | Several unrelated requests or unclear ask | Main problem exists but includes avoidable adjacent scope | One independently actionable problem with boundaries |
| Prior-art awareness | Relevant links are misleading or undifferentiated | Related work is mentioned without a clear distinction | Relevant prior reports are accurately distinguished; use `N/A` when none is reasonably discoverable |
| Diagnosis discipline | Speculation presented as established cause | Observation and hypothesis are partly mixed | Observation, hypothesis, limitation, and proposed solution are separated |
| First-screen readability | Core issue cannot be identified quickly | Core issue is recoverable with substantial reading | Failure, impact, and requested invariant are quickly understandable |

Calculate:

`quality_score = earned_points / (2 * applicable_dimensions)`

Store both the normalised score and the number of applicable dimensions. Define quality bands before analysing outcomes; default bands are:

- high: `>= 0.80`;
- medium: `>= 0.55` and `< 0.80`;
- low: `< 0.55`.

Before full coding, calibrate the rubric on a small shared subset. If more than one reviewer codes issues, independently double-code at least 10% of the mature sample, reconcile disagreements after recording them, and report an agreement measure or disagreement rate.

Also record:

- body word count;
- code-block count;
- external-link count;
- template usage;
- presence of a proposed fix or source analysis;
- presence of a fork or prototype;
- whether the issue was edited after feedback;
- labels, state, closure reason, reactions, and linked PRs where available.

Do not treat length, source analysis, or a prototype as automatically good or bad.

## Low-signal indicators

Record concrete indicators rather than applying a general “bad issue” label:

- no reproducible behaviour where reproduction is relevant;
- no actual/expected distinction;
- unsupported root-cause certainty;
- multiple unrelated requests;
- feature request presented as a regression;
- enormous unfiltered logs;
- screenshot-only evidence;
- outdated or unspecified version where version is relevant;
- vague title;
- hostile or accusatory framing;
- general product support request;
- duplicate with no material distinction;
- redesign far broader than the demonstrated failure;
- external link required to understand the basic report;
- verbosity that adds no evidence.

## Deep-read sample

Select up to 72 distinct issues from the mature 300 after quality scoring, targeting 12 per stratum. Draw without replacement and use this precedence so every issue belongs to at most one stratum:

1. **Maintainer-engaged and completed/fixed** — outcome is completed/fixed and engagement includes a verified maintainer comment.
2. **Maintainer-engaged but unresolved** — outcome is open unresolved and engagement includes a verified maintainer comment.
3. **Rejected or redirected** — outcome is duplicate, expected behaviour, unsupported/support redirect, not planned, automated closure, or other closure, excluding strata 1 and 2.
4. **High-quality without maintainer engagement** — no verified maintainer comment and a high quality score; select this stratum before the remaining no-maintainer strata.
5. **Unverified human/community discussion** — external unverified-human comments, no verified maintainer comment, excluding stratum 4.
6. **No human response and little visible interest** — no external human comment, no verified maintainer comment, excluding stratum 4, and no more than one non-author reaction where reaction identity is available; otherwise use no more than one total reaction and flag the limitation.

When a stratum has more than 12 eligible issues, sample 12 deterministically from issue numbers using a recorded stratum seed. When it contains fewer than 12, include all eligible issues and report the underfill. Do not silently backfill from another stratum.

For the high-quality/no-maintainer stratum, use the fixed quality band rather than selecting reports because they subjectively “look strong.”

The deep-read sample is for qualitative comparisons and counterexamples. Do not use its unweighted stratum proportions as cohort response-rate estimates.

## Required counterexamples

Include examples of:

- strong issues with no maintainer response;
- weak issues that received maintainer attention;
- well-written duplicates;
- high-reaction issues that were not acted on;
- low-reaction issues that led to fixes;
- bot duplicate suggestions that appear semantically related but technically unrelated.

## Related-process cluster

As a focused qualitative exercise, compare these reports by failure layer:

- [#35613](https://github.com/openai/codex/issues/35613) — nested code-mode JavaScript can discard the result containing `session_id` before the handle becomes model-visible; manager entries lack creator-cell provenance for recovery.
- [#34866](https://github.com/openai/codex/issues/34866) — broader wrapper completion versus nested-process state mismatch.
- [#33816](https://github.com/openai/codex/issues/33816) — the model receives a live handle, later loses ownership, and attempts a duplicate command.
- [#35482](https://github.com/openai/codex/issues/35482) — a child process remains active and causes a severe deleted-open-file disk incident; broader process-group, sandbox, cleanup, and resource-safety scope.
- [#35035](https://github.com/openai/codex/issues/35035) — general task incompleteness and false completion claim; likely semantic duplicate-bot noise rather than the same runtime path.

For each, identify:

1. where in the chain the demonstrated failure occurs;
2. whether a session handle was exposed to JavaScript, exposed to the model, later lost, or never surfaced model-side;
3. whether manager ownership is demonstrated, contradicted, or unknown;
4. whether the demonstrated problem is model behaviour, wrapper semantics, process ownership, process-group handling, sandbox observability, cleanup, or resource safety;
5. what #35613 could address;
6. what #35613 definitely would not address;
7. whether a cross-link comment would add new issue-specific evidence or only noise.

Keep demonstrated facts separate from plausible relationships. Do not infer that #35482 used nested code-mode dispatch or a discarded handle unless the thread supplies that evidence.

Do not post comments to these issues as part of the research.

## Optional pull-request appendix

Keep PRs separate from all issue statistics.

If this appendix is run, use the same snapshot `T` and build a complete frame of non-draft PRs created from `T - 90 days` through `T`, including open, closed, and merged PRs. Use paginated API collection or capped date partitions, deduplicate by PR number, and save the frame.

Target 60 PRs, up to 15 from each mutually exclusive origin stratum:

1. **Maintainer-authored** — author has verified repository authority under the actor rules above.
2. **Automated** — author is a bot.
3. **Coordinated external** — affirmative public evidence shows invitation, prior agreement, linked issue assignment, or maintainer-requested work.
4. **Unknown external** — external human without affirmative public coordination evidence.

Do not label a PR “unsolicited” merely because coordination is not public.

When a stratum exceeds 15, sample deterministically without replacement using a recorded seed. When it underfills, include all and report the underfill rather than silently reclassifying or backfilling.

Record merge state, linked issue, review response, time to first verified maintainer review or comment, change size, tests described, and contribution-policy discussion. The purpose is to understand what happens after maintainer alignment, not to imply that opening an uncoordinated PR is advisable.

## Deliverables

Return:

1. Executive summary.
2. Methodology, snapshot, sampling procedure, and limitations.
3. Quantitative engagement-by-outcome table.
4. Issue-type distribution.
5. Mature-cohort response rates by primary issue type and quality band.
6. Timing to first verified maintainer human comment and first visible triage action.
7. Qualitative taxonomy of actionable and low-signal reports.
8. Positive, negative, and counterexample cases.
9. Failure-layer comparison of the five related reports.
10. Comparison of #35613 against the fixed rubric.
11. Publication or follow-up recommendations.
12. Machine-readable frame, sample, and coded table or CSV.
13. Optional separate PR appendix.

Report denominators for every rate. Do not use the freshness or deep-read samples as though they were simple random mature-cohort samples.

## Execution discipline

Do not recommend edits to #35613 based on one memorable issue. Do not propose additional public comments unless the research identifies new, issue-specific evidence.

Before data collection, check only for a concrete feasibility or methodological blocker. If none exists:

1. state **Methodology is ready**;
2. immediately build the frames and run the study;
3. return the deliverables above.

Return **Methodology needs the following concrete correction** only when a specific blocker would make the measurements invalid or irreproducible. Identify the smallest correction, apply it to the working protocol where possible, and then continue when feasible rather than turning the task into another general wording review.

After completing the research, distinguish:

- factual findings;
- measured associations;
- interpretation;
- uncertainty;
- recommended action.
