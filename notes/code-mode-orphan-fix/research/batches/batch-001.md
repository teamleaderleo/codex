# Batch 001 — mixed recent and mature Codex issues

- Review date: 2026-07-27
- Batch size: 5 issues
- Selection mode: recency-weighted purposive comparison
- Public comments posted: none

## Selection

Recent candidate search:

- repository: `openai/codex`
- query: `is:issue created:>=2026-07-01`
- sort: newest first
- candidate issue numbers returned in the inspected page: `35636, 35635, 35634, 35633, 35632, 35631, 35630, 35629, 35628, 35627, 35626, 35625`

Selected recent issues:

- #35634 — current desktop sandbox/workspace bug with a controlled old-task/new-task comparison;
- #35628 — current CLI feature request with unusually detailed scope and prior-art distinctions;
- #35635 — current Windows crash report with correlated system and application logs.

Selected comparison issues:

- #25939 — June compaction failure, now closed as completed;
- #16377 — April compaction failure, now closed as completed.

The older pair was selected because both eventually received the same architectural-resolution explanation despite different report styles.

## Comparison table

| Issue | Age class | Primary type | Quality | Engagement | Outcome | Research value |
|---|---|---|---:|---|---|---|
| #35634 | same-day/new | reproducible bug | 0.94 high | bot-only | open, immature | strong current bug; duplicate-bot test case |
| #35628 | same-day/new | feature request | 0.94 high | author-only | open, immature | detailed feature-request benchmark |
| #35635 | same-day/new | reproducible bug | 0.94 high | bot-only | open, immature | evidence-rich crash report; broad duplicate suggestions |
| #25939 | 30–120 days | reproducible bug | 0.89 high | bot then substantive human response; maintainer authority unverified by connector | completed | concise report resolved by broader architecture change |
| #16377 | 90+ days | reproducible bug | 0.83 high | bot then substantive human response; maintainer authority unverified by connector | completed | less polished report resolved by the same architecture change |

Comment timestamps and commenter `author_association` were not exposed by the connector in this pass. Response latency was therefore not calculated. The `etraut-openai` account supplied substantive resolution comments on #25939 and #16377, but repository permission could not be verified through the available integration, so the human engagement is not counted as a verified-maintainer rate observation.

## Issue reviews

### #35634 — Codex Desktop: adding a Source folder does not update workspace permissions for existing tasks

- URL: https://github.com/openai/codex/issues/35634
- Created: 2026-07-27T15:13:11Z
- State: open
- Labels: `bug`, `sandbox`, `app`
- Surface/backend: Codex Desktop on macOS Apple Silicon; execution backend unknown
- Comments: one duplicate-suggestion bot comment, pointing to #35260
- Primary type: reproducible bug
- Secondary tags: sandbox, permissions, stale task state

Quality dimensions:

| Dimension | Score | Note |
|---|---:|---|
| Title specificity | 2 | Names the exact UI action and stale-permission effect. |
| User impact | 2 | Existing tasks silently cannot use a newly added source folder. |
| Actual vs expected | 2 | Both behaviours are explicit. |
| Reproduction | 2 | Eight-step old-task/new-task comparison. |
| Environment | 1 | Platform is present, but the exact app version was not captured. |
| Evidence | 2 | Controlled comparison includes effective roots, permissions, and an actual file-read result. |
| Scope | 2 | One independently actionable stale-state problem. |
| Prior art | N/A | No prior-art claim in the body; the bot suggestion was added afterward and was not evaluated in this batch. |
| Diagnosis discipline | 2 | The snapshot-at-task-creation explanation is explicitly marked as a hypothesis. |
| First-screen readability | 2 | The failure and comparison are immediately clear. |

Normalized score: `17 / 18 = 0.94`.

Strongest feature: the report isolates the variable by comparing an existing task with a newly created task in the same project.

Smallest useful addition: exact app version and whether reopening or restarting the existing task refreshes its permissions.

Engagement/outcome: bot-only; open and far too new for a mature no-response judgement.

Research value: strong current bug and a future test of whether #35260 is a meaningful duplicate or only a semantic match.

### #35628 — Render Mermaid fenced code blocks in the Codex CLI TUI

- URL: https://github.com/openai/codex/issues/35628
- Created: 2026-07-27T15:05:35Z
- State: open
- Labels: `enhancement`, `TUI`, `CLI`
- Surface/backend: Codex CLI TUI 0.145.0; rendering backend not applicable/unknown
- Comments: none
- Primary type: feature request
- Secondary tags: rendering, Markdown, terminal UX

Quality dimensions:

| Dimension | Score | Note |
|---|---:|---|
| Title specificity | 2 | States the requested input format and surface. |
| User impact | 2 | Explains the cost of mentally parsing or externally rendering diagrams. |
| Actual vs expected | 2 | Raw source today versus terminal-native rendering. |
| Reproduction | N/A | A feature request; the included Mermaid block demonstrates the current surface adequately. |
| Environment | 2 | Exact CLI version and TUI surface are stated. |
| Evidence | 1 | The example is useful, but there is no screenshot or transcript of current rendering. |
| Scope | 2 | Mermaid fenced blocks in one surface, with explicit fallbacks. |
| Prior art | 2 | Four related issues are distinguished by surface and scope. |
| Diagnosis discipline | 2 | Streaming and implementation concerns are framed as design considerations, not established facts. |
| First-screen readability | 2 | The request is clear before the longer design discussion. |

Normalized score: `17 / 18 = 0.94`.

Strongest feature: it distinguishes the requested invariant, graceful fallback, streaming boundary, and neighbouring issues.

Smallest useful improvement: a shorter opening summary before the long implementation discussion. The additional detail is relevant, but the body is longer than needed to establish the request.

Engagement/outcome: author-only; open and newly filed. No conclusion about triage interest is possible.

Research value: a high-quality feature-request benchmark showing that actionable scope is possible without a bug reproduction.

### #35635 — Windows desktop exits when in-app browser GPU process loads vk_swiftshader.dll

- URL: https://github.com/openai/codex/issues/35635
- Created: 2026-07-27T15:19:03Z
- State: open
- Labels: `bug`, `windows-os`, `app`, `browser`
- Surface/backend: Windows Codex desktop app and embedded Chromium browser; command-execution backend unknown
- Comments: one duplicate-suggestion bot comment pointing to #35352, #35411, #35475, #35505, and #35625
- Primary type: reproducible bug
- Secondary tags: crash, browser, code integrity, GPU process

Quality dimensions:

| Dimension | Score | Note |
|---|---:|---|
| Title specificity | 2 | Names the build, trigger, process, and DLL. |
| User impact | 2 | OAuth activity terminates the desktop session. |
| Actual vs expected | 2 | Crash sequence and desired recovery/signing behaviour are explicit. |
| Reproduction | 2 | Concrete OAuth-flow reproduction on two services. |
| Environment | 2 | OS, package build, prior build, and DLL version are given. |
| Evidence | 2 | Application logs, Code Integrity event, and signature inspection correlate at the crash time. |
| Scope | 1 | The main crash is clear, but a possibly separate sandbox recovery failure is included. |
| Prior art | N/A | The body does not make a prior-art claim; five bot suggestions were added afterward and were not evaluated here. |
| Diagnosis discipline | 2 | The separate sandbox failure is qualified, and remediation language remains conditional. |
| First-screen readability | 2 | The summary exposes the complete observed chain. |

Normalized score: `17 / 18 = 0.94`.

Strongest feature: multiple independent logs are connected to the same crash timestamp.

Smallest useful improvement: move the later `CreateProcessWithLogonW` failure into a follow-up report unless evidence establishes that it is part of the same failure chain.

Engagement/outcome: bot-only; open and newly filed. The relevance of the five suggested duplicates is unknown.

Research value: evidence-rich current crash report and a useful test of whether duplicate automation clusters by shared words such as “Windows”, “app exits”, and package health rather than execution path.

### #25939 — Compact fails using Azure OpenAI if not using v1 endpoint

- URL: https://github.com/openai/codex/issues/25939
- Created: 2026-06-02T21:04:02Z
- Closed: 2026-06-29T17:25:45Z
- State reason: completed
- Labels: `bug`, `azure`, `context`, `app`, `config`
- Surface/backend: Codex app using an Azure OpenAI provider; compaction architecture described in the closing response
- Comments: duplicate bot suggestion, followed by a substantive human explanation that compaction had moved from a separate remote endpoint to the normal local flow
- Primary type: reproducible bug
- Secondary tags: Azure, provider configuration, compaction

Quality dimensions:

| Dimension | Score | Note |
|---|---:|---|
| Title specificity | 2 | Names Azure, compaction, and the endpoint condition. |
| User impact | 2 | Compaction terminates with a misleading disconnect. |
| Actual vs expected | 2 | Failure versus working compaction is explicit. |
| Reproduction | 2 | Supplies the relevant provider configuration and trigger. |
| Environment | 2 | App version, platform, subscription/provider are included. |
| Evidence | 1 | Behaviour and configuration are concrete, but the exact error output is paraphrased rather than captured. |
| Scope | 2 | One provider/compaction incompatibility. |
| Prior art | N/A | No prior-art claim in the body. |
| Diagnosis discipline | 1 | The cause and preferred fix are asserted more strongly than the supplied evidence establishes. |
| First-screen readability | 2 | The failure and workaround condition are easy to understand. |

Normalized score: `16 / 18 = 0.89`.

Strongest feature: a compact configuration-level reproduction identifies the condition that changes the result.

Smallest useful improvement: link the mentioned PR, quote the exact error, and mark local fallback as a proposed remedy rather than the only established fix.

Engagement/outcome: bot suggestion followed by substantive human explanation; closed completed after Codex moved compaction to a more robust local path. Maintainer authority of the commenter was not technically verifiable in this connector session.

Research value: a concise, imperfect report that was eventually covered by a broader architectural change.

### #16377 — compact execution failed

- URL: https://github.com/openai/codex/issues/16377
- Created: 2026-04-01T00:24:52Z
- Closed: 2026-06-29T17:19:36Z
- State reason: completed
- Labels: `bug`, `context`
- Surface/backend: Codex CLI using remote compaction at the time of the report
- Comments: duplicate bot suggestions, followed by the same substantive human explanation that compaction moved away from the separate remote path
- Primary type: reproducible bug
- Secondary tags: context, remote compaction, stream disconnect

Quality dimensions:

| Dimension | Score | Note |
|---|---:|---|
| Title specificity | 1 | Names compaction failure only generically. |
| User impact | 2 | Automatic and manual compaction fail, blocking execution. |
| Actual vs expected | 2 | Error and desired successful compaction are present. |
| Reproduction | 1 | Supplies an uploaded thread ID but few standalone trigger steps. |
| Environment | 2 | CLI version, subscription, model, platform, and terminal are present. |
| Evidence | 2 | Detailed TUI and log errors include token and request context. |
| Scope | 2 | One compaction failure. |
| Prior art | N/A | No prior-art claim in the original body. |
| Diagnosis discipline | 2 | Reports observations without overclaiming a cause. |
| First-screen readability | 1 | The generic title and large log block make the core condition slower to extract. |

Normalized score: `15 / 18 = 0.83`.

Strongest feature: high-value diagnostic logs and a reproducible uploaded thread compensate for weak prose structure.

Smallest useful improvement: use a title naming remote compaction stream disconnection and add a minimal description of the context-window condition before the logs.

Engagement/outcome: bot suggestions followed by substantive human explanation; closed completed after the same compaction architecture change. Maintainer authority of the commenter was not technically verifiable in this connector session.

Research value: a counterexample to the idea that first-screen polish is required for eventual useful triage or resolution.

## Batch synthesis

### Factual observations

- All three same-day issues are high-quality-looking reports, but two have only duplicate-bot activity and one has no comments. Their age makes the absence of human response non-informative.
- The duplicate bot appeared on four of the five issues in this batch.
- #25939 and #16377 received materially identical closing explanations and were completed after Codex changed its compaction architecture.
- The two mature compaction reports differ in presentation: #25939 is short and configuration-focused; #16377 is log-heavy with a generic title.

### Interpretation

1. **Recency must be represented, not filtered out.** Current issues expose present templates, surfaces, and report norms, but they cannot answer mature-response questions by themselves.
2. **Bot activity is not evidence of human triage.** The duplicate bot is common even on highly specific reports, and its suggestions need separate technical evaluation.
3. **Resolution may be roadmap-driven.** Both older issues were covered by a broader compaction redesign. Their eventual completion does not demonstrate that one report style caused engagement.
4. **Actionability has multiple forms.** Controlled comparisons, correlated logs, configuration-level reproductions, and careful prior-art distinctions can all make a report useful. Length by itself is not a reliable quality signal.
5. **Weak presentation does not imply weak evidence.** #16377's generic title and log-heavy body still contain enough diagnostic value to connect it to the eventual architecture change.

### Counterexamples and tensions

- #35628 is very polished and currently unanswered; this is expected for a same-day issue, not evidence that polish fails.
- #16377 is less readable than the other reports but still reached a substantive completed outcome.
- #25939 asserts a fix more strongly than its evidence supports, yet its core reproduction is concise and actionable.
- #35635 is unusually evidence-rich but may weaken its scope slightly by including a separate recovery failure.

### Implication for #35613

This batch gives no reason to broaden #35613. The strongest current reports make their value through a precise invariant, controlled evidence, or explicit scope boundaries. The prevalence of semantic duplicate suggestions reinforces the value of clearly distinguishing failure layers and related issues. No wording or public-comment change should be made from this batch alone.

### Next batch composition

Choose five issues that test the first hypotheses:

1. one recent low-signal or ambiguous report;
2. one mature issue closed as duplicate;
3. one thread containing a maintainer information request;
4. one community-only discussion;
5. one high-reaction issue that remains unresolved or was not acted on.

At least one case should permit direct evaluation of whether the duplicate bot's suggested issue is technically related.

### Confidence and limitations

- Confidence is high in the report-quality comparisons because full issue bodies were available.
- Confidence is moderate in engagement classification because comment bodies and actors were visible.
- Verified-maintainer identity and response-time calculations are unavailable for the two older human responses because the connector omitted commenter associations/timestamps and denied collaborator-permission verification.
- This purposive five-issue batch maps patterns; it cannot estimate repository-wide rates.