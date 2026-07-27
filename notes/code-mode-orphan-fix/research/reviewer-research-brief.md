# Reviewer brief: compare recent Codex issues and triage outcomes

Please conduct a structured compare-and-contrast study of recent `openai/codex` issues. This is a research task, not another wording review of [#35613](https://github.com/openai/codex/issues/35613).

## Purpose

The goal is to understand:

- how recent issues are formatted;
- how often they receive bot, community, or maintainer responses;
- which report characteristics are associated with useful triage;
- which apparently strong reports remain unanswered;
- what kinds of submissions create noise or are difficult to act on;
- whether #35613 is appropriately scoped and presented for this repository.

Do not assume that an unanswered issue is poor. Maintainer capacity, priority, roadmap fit, timing, duplication, and issue type can all affect the outcome.

## Cohort

### Mature issue cohort

Use approximately 300 non-PR issues created from **April 1 through June 27, 2026**, evaluated as of the research date.

The June 27 cutoff gives each issue at least 30 days of observation as of July 27. Include both **open and closed** issues. Exclude pull requests from the issue cohort.

If more than 300 issues match, use a reproducible sample rather than hand-selecting memorable reports.

### Freshness check

Review approximately 50 issues created after June 27 separately. Use them only to identify changes in templates, labels, bots, or triage practice. Do not include them in the 30-day no-response rate.

### Deep-read sample

Select approximately 72 issues, roughly 12 from each group:

1. Maintainer-engaged and fixed or accepted.
2. Maintainer-engaged but unresolved.
3. Closed as duplicate, unsupported, expected behaviour, or not planned.
4. Community discussion without maintainer engagement.
5. No human response and little visible interest.
6. High-quality-looking reports with no maintainer response.

The sixth group is required so the study does not merely reverse-engineer superficial traits from successful outcomes.

## Response classification

Classify responses as:

- **No response:** no comment other than the author’s own follow-up.
- **Bot-only:** automated duplicate, labelling, or template response with no human engagement.
- **Community-only:** human comments, but no repository owner, member, or collaborator response.
- **Maintainer acknowledgement:** receipt or classification without substantive analysis.
- **Maintainer information request:** request for reproduction, logs, versions, clarification, or narrower scope.
- **Substantive maintainer response:** diagnosis, workaround, source reference, design discussion, confirmation, or concrete next step.
- **Resolved:** linked fix, merged PR, confirmed release, or closure as completed.
- **Rejected or redirected:** duplicate, unsupported, expected behaviour, support request, or not planned.

Use author association such as `OWNER`, `MEMBER`, or `COLLABORATOR` where available. Do not infer maintainer status solely from tone.

Measure time to first maintainer response at 24 hours, 7 days, and 30 days.

## Issue-type controls

Classify each issue before comparing outcomes:

- reproducible bug;
- intermittent bug;
- model-behaviour report;
- feature request;
- performance or resource problem;
- documentation request;
- support or usage question;
- security or privacy concern;
- meta or process issue;
- duplicate or already tracked issue;
- unclear or mixed request.

Do not compare raw response rates across these categories without noting the difference in issue type.

## Quality rubric

For the deep-read sample, score each dimension from 0 to 2:

1. **Title specificity** — observable behaviour rather than a vague complaint.
2. **User impact** — explains what fails or why it matters.
3. **Actual versus expected behaviour** — both are distinguishable.
4. **Reproduction** — minimal, executable, or otherwise credible.
5. **Environment** — relevant version, platform, configuration, or backend details.
6. **Evidence** — useful logs, outputs, screenshots, source references, or artifacts.
7. **Scope** — one independently actionable problem rather than several bundled requests.
8. **Prior-art awareness** — related issues are distinguished rather than dumped as links.
9. **Diagnosis discipline** — observations, hypotheses, and proposed solutions are separated.
10. **First-screen readability** — a maintainer can understand the failure and requested invariant quickly.

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

- no reproducible behaviour;
- no actual/expected distinction;
- unsupported root-cause certainty;
- multiple unrelated requests;
- feature request presented as a regression;
- enormous unfiltered logs;
- screenshot-only evidence;
- outdated or unspecified version;
- vague title;
- hostile or accusatory framing;
- general product support request;
- duplicate with no material distinction;
- redesign far broader than the demonstrated failure;
- external link required to understand the basic report;
- verbosity that adds no evidence.

## Required counterexamples

Include examples of:

- strong issues with no maintainer response;
- weak issues that received maintainer attention;
- well-written duplicates;
- high-reaction issues that were not acted on;
- low-reaction issues that led to fixes;
- bot duplicate suggestions that appear semantically related but technically unrelated.

Use “associated with engagement,” not “caused engagement,” unless the thread supplies direct evidence.

## Related-process cluster

As a focused qualitative exercise, compare these reports by failure layer:

- [#35613](https://github.com/openai/codex/issues/35613) — nested code-mode result discards `session_id`; manager entries lack creator-cell provenance for recovery.
- [#34866](https://github.com/openai/codex/issues/34866) — broader wrapper completion versus nested-process state mismatch.
- [#33816](https://github.com/openai/codex/issues/33816) — model receives a live handle, later loses ownership, and attempts a duplicate command.
- [#35482](https://github.com/openai/codex/issues/35482) — child process remains active and causes a severe deleted-open-file disk incident; broader process-group, sandbox, and resource-safety scope.
- [#35035](https://github.com/openai/codex/issues/35035) — general task incompleteness and false completion claim; likely semantic duplicate-bot noise rather than the same runtime path.

For each, identify:

1. where in the chain the failure occurs;
2. whether a session handle was exposed, lost, or never surfaced;
3. whether the process was still manager-owned;
4. whether the problem is model behaviour, wrapper semantics, process ownership, sandbox observability, cleanup, or resource safety;
5. what #35613 could address;
6. what #35613 definitely would not address;
7. whether a cross-link comment would add evidence or only noise.

Do not post comments to these issues as part of the research.

## Pull-request appendix

Keep PRs separate from the issue statistics. After the issue study, inspect 50–75 recent PRs split into:

- maintainer-authored;
- automated;
- invited or coordinated external;
- apparently unsolicited external.

Record merge state, linked issue, review response, time to first review, change size, tests described, and contribution-policy discussion. The purpose is to understand what happens after maintainer alignment, not to imply that opening an unsolicited PR is advisable.

## Deliverables

Return:

1. Executive summary.
2. Methodology and limitations.
3. Quantitative response-outcome table.
4. Issue-type distribution.
5. Response rates by issue type and quality band.
6. Qualitative taxonomy of actionable and low-signal reports.
7. Positive, negative, and counterexample cases.
8. Failure-layer comparison of the five related reports.
9. Comparison of #35613 against the fixed rubric.
10. Publication or follow-up recommendations.
11. Machine-readable coded table or CSV.
12. Optional separate PR appendix.

## Review discipline

Do not recommend edits to #35613 based on one memorable issue. Do not propose additional public comments unless the research identifies new, issue-specific evidence.

Before beginning the survey, return one of:

- **Methodology is ready**
- **Methodology needs the following concrete correction**

For every correction, identify the exact methodological problem and the smallest change needed.

After completing the research, distinguish:

- factual findings;
- measured associations;
- interpretation;
- uncertainty;
- recommended action.
