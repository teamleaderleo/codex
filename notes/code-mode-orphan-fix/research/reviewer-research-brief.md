# Reviewer brief: compare recent Codex issues and triage outcomes

Please conduct a structured compare-and-contrast study of recent `openai/codex` issues. This is an execution brief, not another wording review of [#35613](https://github.com/openai/codex/issues/35613).

Treat the protocol below as approved unless data access reveals a concrete blocker. When the methodology is feasible, state **Methodology is ready** and continue directly into the survey in the same task. Do not stop after the readiness statement.

Do not post comments to #35613 or any related public issue during this research.

## Purpose

The study should determine:

- how recent issues are formatted;
- how often they receive bot, unverified-human/community, or verified-maintainer responses;
- which report characteristics are associated with useful triage;
- which apparently strong reports remain unanswered;
- what kinds of submissions create noise or are difficult to act on;
- whether #35613 is appropriately scoped and presented for this repository.

Do not assume that an unanswered issue is poor. Maintainer capacity, priority, roadmap fit, timing, duplication, and issue type can all affect the outcome. Use “associated with engagement,” not “caused engagement,” unless a thread supplies direct evidence.

## Data-access preflight

Before sampling, verify that the available data source can provide:

1. a complete issue frame beyond GitHub Search's 1,000-result cap;
2. issue title, body, author, creation time, labels, state, state reason, reactions, and closure time;
3. all issue comments with timestamps, commenter identity, account type, and `author_association` where available;
4. linked fixes or pull requests and, where available, timeline actions such as labels, assignment, milestones, closure, reopening, locking, and transfer.

Comment-level access is required for the engagement classifications and time-to-maintainer-response measurements. Do not substitute comment count for comment content or commenter identity. If full comments cannot be read, return **Methodology needs the following concrete correction**, identify the missing read capability, and request or use an approved read-only source before running the headline response analysis.

If comments are readable but some timeline actions are unavailable, continue with the issue study, mark the unavailable fields, and omit or narrow only the affected triage-action metric. Never silently treat unavailable data as absence.

## Fixed observation point and saved artifacts

Before collecting data, freeze one exact UTC observation timestamp, `T`.

Evaluate issue state, comments, labels, assignments, reactions, linked fixes, and closure information as they existed at `T`. Do not mix later observations into the coded dataset.

Save enough information to reproduce the study:

- `study-config.json` containing `T`, date bounds, sample sizes, random seeds, sampling algorithm, and coding version;
- the complete deduplicated mature and freshness frames;
- the selected issue IDs;
- the coded issue table;
- the deep-read selections and stratum assignments;
- unavailable fields, API limitations, and collection failures.

## Cohorts

### Mature issue cohort

Build a frame of all non-PR issues satisfying:

- repository: `openai/codex`;
- `created_at >= 2026-04-01T00:00:00Z`;
- `created_at <= T - 30 days`;
- state: open or closed.

Calculate the upper bound from the exact timestamp. If tooling supports only whole dates, use a conservative whole-day cutoff that guarantees 30 complete days of observation.

Sample exactly 300 issues without replacement when at least 300 are eligible. If fewer are eligible, use the complete frame and report the smaller denominator.

### Freshness cohort

Build a separate frame of all non-PR issues satisfying:

- `created_at > T - 30 days`;
- `created_at <= T`;
- state: open or closed.

Sample exactly 50 issues without replacement when at least 50 are eligible. Use this cohort only to identify changes in templates, labels, bots, and triage practice. Do not include it in mature-cohort response rates.

### Complete-frame construction and deterministic sampling

Do not rely on one GitHub Search result set. Construct each complete frame through the paginated Issues API or through date partitions small enough to remain below every retrieval cap. Verify partition counts, subdivide any capped partition, deduplicate by repository and issue number, exclude records containing pull-request metadata, and sort the final frame by issue number.

Use a recorded integer seed and deterministic sampling:

1. sort eligible issue numbers ascending;
2. initialise Python `random.Random(seed)`;
3. call `sample(issue_numbers, n)` without replacement;
4. sort selected IDs ascending for storage and review.

Use separately recorded seeds or a documented deterministic seed derivation for mature, freshness, deep-read, reliability, and PR samples.

## Observation windows

Use two engagement views and do not mix them:

- **30-day engagement:** comments and bot activity occurring from issue creation through `created_at + 30 days`. Use this view for response rates, issue-type comparisons, quality-band comparisons, and the main engagement-by-outcome table.
- **Engagement as of `T`:** all activity visible by the snapshot. Use this only for supplemental current-state descriptions and qualitative case selection.

Record whether the first verified maintainer response occurred after day 30 as `late_maintainer_response`.

Code outcome from the issue's state and evidence as of `T`. When crossing 30-day engagement with current outcome, label the different horizons explicitly: engagement is censored at 30 days; outcome is current at `T`.

## Actor and maintainer identification

Identify automated actors before considering repository association. Use account type, a recognised bot identity, or an explicit `[bot]` marker. A bot's association does not make it a human maintainer response.

For humans:

- count `OWNER`, `MEMBER`, or `COLLABORATOR` as verified maintainer associations;
- treat `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR`, `FIRST_TIMER`, `NONE`, and missing association as unverified human/community unless separate authority evidence exists;
- allow separate authority evidence only when a visible repository action demonstrates write authority, such as assigning another user, applying or removing labels, setting a milestone, locking, transferring, or closing/reopening an issue the actor did not open;
- do not treat an author's closure of their own issue as maintainer evidence;
- record the authority evidence used.

Do not infer authority from tone, profile text, apparent employment, code familiarity, or contribution history. Describe verified-maintainer response rates as conservative where private organisation membership or missing association data could hide maintainer status.

## Response and outcome coding

Do not combine engagement and disposition into one category. Code them on separate axes and retain event-level flags.

### Engagement axis

Assign the highest human-engagement level reached within 30 days, and separately the highest level reached by `T`:

1. **Author-only/no external human response** — no human comment other than the issue author's own follow-up.
2. **Unverified human/community response** — at least one external human comment, but no verified maintainer comment.
3. **Maintainer acknowledgement** — verified maintainer receipt or classification without analysis or a request for information.
4. **Maintainer information request** — request for reproduction, logs, versions, clarification, or narrower scope.
5. **Substantive maintainer response** — diagnosis, workaround, source reference, design discussion, confirmation, prioritisation, or concrete next step.

Record bot activity separately for both windows. Retain Boolean flags for community response, acknowledgement, information request, substantive response, and bot response even when the highest category is used in tables.

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

Measure from issue creation to the first verified maintainer human comment. Report proportions receiving one within 24 hours, 7 days, and 30 days. Also record time to first visible triage action when timeline data permits.

For the mature cohort, every issue has a full 30-day observation period. Code no verified maintainer comment within 30 days as a censored non-event for the 30-day rate, not as zero response time. Preserve later responses separately.

## Issue-type controls

Assign one primary issue type before inspecting response and outcome variables. Use this precedence when several apply:

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

Add optional secondary tags such as performance, resource safety, sandbox, model behaviour, regression, or documentation. Duplicate or already-tracked status belongs on the outcome axis.

Issue-type rates are descriptive. Report denominators and confidence intervals where practical, but make no between-type inferential claim from this sample. Do not publish a standalone rate for a primary-type cell with fewer than 20 issues; pool it into a clearly named broader group or mark it sparse. Present issue-type and quality-band rates as separate stratifications unless cross-classified cells are adequately populated.

## Quality scoring

Score all sampled mature issues. This supports cohort-level quality-band rates and avoids selecting strong unanswered reports through subjective pre-judgement.

Where practical, score title and body before viewing comments, labels, reactions, state, closure, linked work, or author identity. Record whether scoring was blinded.

Use the issue version immediately before the first verified maintainer response when edit history permits. Otherwise use the version available at `T`, record whether it was edited after feedback, and flag uncertainty. Do not present an edited-after-response score as an unqualified predictor of engagement.

For every dimension use:

- `0` — absent, materially unclear, or misleading;
- `1` — present but incomplete, indirect, or difficult to use;
- `2` — clear, specific, and decision-useful;
- `N/A` — genuinely inapplicable to that issue type, with a reason.

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

Store the normalised score and applicable-dimension count. Fix bands before analysing outcomes:

- high: `>= 0.80`;
- medium: `>= 0.55` and `< 0.80`;
- low: `< 0.55`.

Calibrate the rubric on a small subset before full coding. With multiple reviewers, independently double-code at least 10% of the mature sample and report agreement before reconciliation. With one reviewer, randomly select and blindly re-code at least 10% after the first coding pass, preserve both ratings, and report within-rater agreement or disagreement.

Also record body word count, code-block count, external-link count, template usage, proposed-fix/source-analysis presence, fork/prototype presence, post-feedback edits, labels, state, closure reason, reactions, and linked PRs where available. Do not treat length, source analysis, or a prototype as automatically good or bad.

## Low-signal indicators

Record concrete indicators rather than assigning a general “bad issue” label:

- no reproducible behaviour where reproduction is relevant;
- no actual/expected distinction;
- unsupported root-cause certainty;
- multiple unrelated requests;
- feature request presented as a regression;
- enormous unfiltered logs;
- screenshot-only evidence;
- outdated or unspecified version where relevant;
- vague title;
- hostile or accusatory framing;
- general product support request;
- duplicate with no material distinction;
- redesign far broader than the demonstrated failure;
- external link required to understand the basic report;
- verbosity that adds no evidence.

## Deep-read sample

Select up to 72 distinct issues from the mature 300 after quality scoring, targeting 12 per stratum. Draw without replacement and use this precedence:

1. **Maintainer-engaged and completed/fixed** — completed/fixed by `T` and a verified maintainer comment by `T`.
2. **Maintainer-engaged but unresolved** — open unresolved at `T` and a verified maintainer comment by `T`.
3. **Rejected or redirected** — duplicate, expected behaviour, unsupported/support redirect, not planned, automated closure, or other closure, excluding strata 1 and 2.
4. **High-quality without maintainer engagement** — no verified maintainer comment by `T` and a high quality score.
5. **Unverified human/community discussion** — external unverified-human comments by `T`, no verified maintainer comment, excluding stratum 4.
6. **No human response and little visible interest** — no external human comment by `T`, excluding stratum 4, and no more than one non-author reaction where identity is available; otherwise no more than one total reaction, with the limitation flagged.

When a stratum has more than 12 eligible issues, sample 12 deterministically using a recorded stratum seed. When it has fewer, include all and report the underfill. Do not silently backfill. Record each selected issue's 30-day engagement as well as its at-`T` stratum.

The deep-read sample is qualitative. Do not use its unweighted stratum proportions as cohort response-rate estimates.

## Required counterexamples

Include examples of:

- strong issues with no maintainer response;
- weak issues that received maintainer attention;
- well-written duplicates;
- high-reaction issues that were not acted on;
- low-reaction issues that led to fixes;
- bot duplicate suggestions that appear semantically related but technically unrelated.

## Related-process cluster

Compare these five focal reports by failure layer:

- [#35613](https://github.com/openai/codex/issues/35613) — nested code-mode JavaScript can discard the result containing `session_id` before the handle becomes model-visible; manager entries lack creator-cell provenance for recovery.
- [#34866](https://github.com/openai/codex/issues/34866) — broader wrapper completion versus nested-process state mismatch.
- [#33816](https://github.com/openai/codex/issues/33816) — the model receives a live handle, later loses ownership, and attempts a duplicate command.
- [#35482](https://github.com/openai/codex/issues/35482) — a child process remains active and causes a severe deleted-open-file disk incident; broader process-group, sandbox, cleanup, and resource-safety scope.
- [#35035](https://github.com/openai/codex/issues/35035) — general task incompleteness and false completion claim; likely semantic duplicate-bot noise rather than the same runtime path.

The cluster map also contains a wake-up-after-exit layer. That layer is deliberately contextual rather than a sixth focal report in this pass. Note it as a possible adjacent scheduling mechanism, but do not expand the five-report comparison unless new evidence or the user requests it.

For each focal report, identify:

1. where in the chain the demonstrated failure occurs;
2. whether a session handle was exposed to JavaScript, exposed to the model, later lost, or never surfaced model-side;
3. whether manager ownership is demonstrated, contradicted, or unknown;
4. whether the demonstrated problem is model behaviour, wrapper semantics, process ownership, process-group handling, sandbox observability, cleanup, or resource safety;
5. product surface and execution backend, using `unknown` where the thread does not establish app/CLI/cloud or local/exec-server execution;
6. what #35613 could address;
7. what #35613 definitely would not address;
8. whether a cross-link comment would add new issue-specific evidence or only noise.

Keep demonstrated facts separate from plausible relationships. Do not infer that #35482 used nested code-mode dispatch, a discarded handle, or a particular backend unless the thread supplies that evidence.

Do not post comments to these issues as part of the research.

## Optional pull-request appendix

Keep PRs separate from all issue statistics.

If run, use the same snapshot `T` and build a complete frame of non-draft PRs created from `T - 90 days` through `T`, including open, closed, and merged PRs. Use paginated collection or capped date partitions, deduplicate by PR number, and save the frame.

Target 60 PRs, up to 15 from each mutually exclusive origin stratum:

1. **Maintainer-authored** — author has verified repository authority under the actor rules above.
2. **Automated** — author is a bot.
3. **Coordinated external** — affirmative public evidence shows invitation, prior agreement, linked issue assignment, or maintainer-requested work.
4. **Unknown external** — external human without affirmative public coordination evidence.

Do not label a PR “unsolicited” merely because coordination is not public. When a stratum exceeds 15, sample deterministically without replacement. When it underfills, include all and report the underfill rather than backfilling.

Record merge state, linked issue, review response, time to first verified maintainer review or comment, change size, tests described, and contribution-policy discussion.

## Deliverables

Return:

1. Executive summary.
2. Methodology, capability preflight, snapshot, sampling procedure, and limitations.
3. Quantitative 30-day engagement-by-current-outcome table.
4. Supplemental engagement-as-of-`T` table.
5. Issue-type distribution.
6. Mature-cohort 30-day response rates separately by primary issue type and quality band.
7. Timing to first verified maintainer human comment and first visible triage action where available.
8. Qualitative taxonomy of actionable and low-signal reports.
9. Positive, negative, and counterexample cases.
10. Failure-layer comparison of the five focal reports.
11. Comparison of #35613 against the fixed rubric.
12. Publication or follow-up recommendations.
13. Machine-readable frames, samples, and coded table or CSV.
14. Optional separate PR appendix.

Report denominators for every rate. Do not use the freshness or deep-read samples as simple random mature-cohort samples. Mark sparse cells and unavailable fields explicitly.

## Execution discipline

Do not recommend edits to #35613 based on one memorable issue. Do not propose additional public comments unless the research identifies new, issue-specific evidence.

Before data collection, check only for a concrete feasibility or methodological blocker. If none exists:

1. state **Methodology is ready**;
2. immediately build the frames and run the study;
3. return the deliverables above.

Return **Methodology needs the following concrete correction** only when a specific blocker would make measurements invalid or irreproducible. Identify the smallest correction, apply it to the working protocol where possible, and continue when feasible rather than turning the task into another wording review.

After completing the research, distinguish factual findings, measured associations, interpretation, uncertainty, and recommended action.
