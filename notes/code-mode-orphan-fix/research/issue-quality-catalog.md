# Codex issue-quality catalog

This catalog reviews public `openai/codex` issues in contiguous chronological blocks. It evaluates the usefulness of the submitted report, not whether the underlying request should be implemented.

## Rating scale

- **A — strong/actionable:** a maintainer can quickly identify the failure or request, affected surface, evidence, and next investigative step.
- **B — usable:** the core issue is understandable and potentially actionable, but important evidence, scope control, or product fit is missing.
- **C — costly/mis-scoped:** there may be a real issue, but the submission creates substantial triage work through overbreadth, weak evidence, excessive solutioning, or poor repository fit.
- **D — weak/noisy:** vague, hostile, bundled, unsupported, or lacking enough information to investigate efficiently.
- **Duplicate/noise flag:** independent of prose quality; marks literal reposts, already-supported requests, or other avoidable catalog duplication.

The catalog also distinguishes **writing quality** from **repository actionability**. A polished submission can still be low-value if it belongs in another product channel, asks for an existing feature, or duplicates another report.

---

## Block 001 — issues #35616 through #35637

- Review date: 2026-07-27
- Selection: every public issue in the contiguous number interval, excluding pull requests #35621 and #35623
- Ordering: creation time, oldest to newest
- Total issues: 20
- Public comments posted: none

### Summary distribution

| Category | Count | Issues |
|---|---:|---|
| A — strong/actionable | 10 | #35617, #35620, #35625, #35627, #35629, #35633, #35634, #35635, #35636, #35637 |
| B — usable | 3 | #35624, #35628, #35630/#35632 as a single underlying report |
| C — costly or mis-scoped | 5 | #35616, #35618, #35619, #35626, #35631 |
| D — weak/noisy | 1 | #35622 |
| Duplicate submission | 1 extra catalog row | #35632 duplicates #35630 nearly verbatim |

This block is not mostly low-quality. It is, however, full of **triage friction that ordinary quality scores miss**: two near-identical submissions, one elaborate request for functionality already available, several reports far longer than necessary, and multiple requests whose natural owner may not be the Codex repository.

### Chronological catalog

| Time UTC | Issue | Type | Grade | Main value | Main defect / triage cost | Catalog tag |
|---|---|---|---:|---|---|---|
| 13:50 | [#35616](https://github.com/openai/codex/issues/35616) — Business workspace data export | feature request / data portability | C | Clear requested archive contents, owner permissions, machine-readable format, and business-continuity rationale. | Broad ChatGPT Business policy/product request rather than a demonstrated Codex repository defect. It specifies a large product programme without identifying the owning surface or an incremental Codex change. | polished but likely wrong venue |
| 13:57 | [#35617](https://github.com/openai/codex/issues/35617) — Android-created threads disappear after reconnect | reproducible bug | A | Excellent Android-created versus desktop-created control, completed-turn lifecycle evidence, database and app-server checks, and careful distinction from #22800. | A third-party launcher and custom provider add environmental complexity, although the report explicitly isolates the official app-server lifecycle. Long, but the detail is relevant. | controlled cross-surface comparison |
| 14:07 | [#35618](https://github.com/openai/codex/issues/35618) — Responses Lite round trips | performance / tool-policy report | C | Identifies the exact client policy disabling parallel tool calls and points to relevant source files and PR history. | The issue mixes an observable policy, an inferred usage-cost claim, a product request, and a huge personal prompt template. The pasted prompt overwhelms the defect and makes the requested change unclear. No quantitative round-trip or usage comparison is supplied. | valid observation buried in prompt dump |
| 14:11 | [#35619](https://github.com/openai/codex/issues/35619) — 934 rollout files missing | data-loss bug | C | Exceptional forensic work: exact counts, bounded incident window, process transition, ruled-out hypotheses, corrections to earlier claims, integrity checks, and preserved evidence. | Far too long for first-pass triage and carries two potentially different deletion scopes. The report repeatedly revises hypotheses inside the body. A concise incident summary plus an attached forensic appendix would be much more usable. | excellent evidence, excessive cognitive load |
| 14:12 | [#35620](https://github.com/openai/codex/issues/35620) — Agent V2 emits wrong tools | model-behaviour regression | A | Strong baseline/failure comparison, clean-state controls, raw-response boundary, quantitative transition counts, exact environment, and disciplined limits on root-cause certainty. | Longer than necessary, but nearly every section answers a plausible diagnostic question. The requested internal investigation is broad but clearly separated from established evidence. | benchmark model-behaviour report |
| 14:25 | [#35622](https://github.com/openai/codex/issues/35622) — macOS release complaints | mixed bug bundle | D | Supplies app version, platform, and a list of visible symptoms. | Generic title, hostile framing, four separate defects, no real reproduction, no prioritisation, and “self-evident” expected behaviour. A maintainer must split and reconstruct the report before investigating anything. | archetypal low-signal bundle |
| 14:56 | [#35624](https://github.com/openai/codex/issues/35624) — Work Mode crash makes app unrecoverable | reproducible crash | B | Severe impact, repeatability, exact app/OS, control with a new chat, recovery procedure, and an example task. | The triggering workload remains broad and nondeterministic, there are no logs or package-state observations, and the template’s expected-behaviour field is left empty despite prose elsewhere. Repeats the same account twice. | usable crash report, weak diagnostics |
| 14:57 | [#35625](https://github.com/openai/codex/issues/35625) — AppX NeedsRemediation after thread render | crash / package-health bug | A | Correlates Code Integrity, AppModel-Runtime, package status, AppX teardown, stable/beta controls, thread structure, and observed remediation. Avoids claiming the first correlated event is sufficient. | No safe minimal reproduction and the body ends with several causal questions rather than one requested invariant, but the evidence is strong enough to investigate. | high-value forensic crash report |
| 15:04 | [#35626](https://github.com/openai/codex/issues/35626) — named thread in terminal title | feature request | C | Carefully scoped default-behaviour proposal, implementation awareness, fallback semantics, tests, and related-issue distinctions. | The requested outcome was already available through `/title`; the author discovered this and closed the issue. The report is polished but represents avoidable discovery failure and substantial unnecessary writing. | high-effort unnecessary request |
| 15:04 | [#35627](https://github.com/openai/codex/issues/35627) — name-independent MCP allowlist | feature request / policy configuration | A | Short, focused statement of the matching limitation, concrete enterprise use case, comparison with other tools, and three acceptable solution shapes. | Does not name the exact Codex version or discuss the security semantics of wildcard/name-independent matching. Those are follow-up questions, not blockers. | concise actionable feature request |
| 15:05 | [#35628](https://github.com/openai/codex/issues/35628) — render Mermaid in TUI | feature request | B | Clear surface and desired invariant, graceful fallback, realistic streaming concern, constrained first version, and good prior-art distinctions. | Excessive implementation design for an initial feature request. The core ask is established early, but the later design material could bias or burden triage before maintainers decide whether the feature belongs. | strong request, overdesigned body |
| 15:07 | [#35629](https://github.com/openai/codex/issues/35629) — stale Voice thread pointer | reproducible state bug | A | Excellent symptom-to-state chain, exact persisted key, logs, failed controls, narrowly successful recovery, migration hypothesis marked as tentative, and explicit expected recovery behaviour. | Requires manual state inspection unavailable to ordinary users, but that strengthens rather than weakens this diagnostic report. | benchmark persisted-state report |
| 15:08 | [#35630](https://github.com/openai/codex/issues/35630) — unfinished Browser calls crash resumed thread | reproducible crash | B | Repeated deterministic failure, exact task-state condition, unmatched tool-call IDs, session size, timestamps, workaround, and cautious suspected cause. | Exposes a raw thread ID publicly and contains more local detail than needed. It was quickly closed as duplicate, and another nearly identical issue was posted two minutes later. | strong report, duplicate-channel noise |
| 15:10 | [#35631](https://github.com/openai/codex/issues/35631) — boosts should not overwrite entitlements | entitlement/product design | C | Clear invariant, examples, acceptance criteria, and distinction from one suggested duplicate. | No concrete reproducible account event or evidence is provided. It generalises from one asserted scenario into a cross-platform entitlement architecture and cites external billing systems. Likely wrong repository/product owner. | polished speculative product programme |
| 15:10 | [#35632](https://github.com/openai/codex/issues/35632) — unfinished Browser calls crash resumed thread | reproducible crash | B + duplicate | Same strengths as #35630 and adds an explicit workaround. | Near-verbatim duplicate of #35630 from a different account, posted roughly two minutes later. Whatever the underlying coordination, it creates pure catalog and triage duplication. | literal duplicate submission |
| 15:10 | [#35633](https://github.com/openai/codex/issues/35633) — explicit `gh` request sent to shell-less V8 | tool-routing bug | A | Very concise host/V8/Node-backed control comparison, exact observed globals, working route, expected routing invariant, and environment. | “May attempt” leaves frequency and determinism unclear, and the Codex app version is absent. Still immediately testable. | compact controlled report |
| 15:13 | [#35634](https://github.com/openai/codex/issues/35634) — Source folder does not update existing task permissions | reproducible state/permissions bug | A | Excellent existing-task/new-task controlled comparison, clear stale-state impact, executable steps, actual file-read check, and explicit separation of observation from hypothesis. | Exact app version is missing, and it would help to test whether thread restart/reopen refreshes permissions. | benchmark controlled comparison |
| 15:19 | [#35635](https://github.com/openai/codex/issues/35635) — SwiftShader/GPU crash | crash / package-integrity bug | A | Exact builds, deterministic OAuth path, correlated Codex and Windows Code Integrity logs, troubleshooting controls, and a bounded expected fallback. | Adds a later sandbox `CreateProcessWithLogonW` failure that may be a separate recovery issue; this slightly muddies scope. | evidence-rich crash report |
| 15:25 | [#35636](https://github.com/openai/codex/issues/35636) — no-auth Bedrock gateway mode | feature request / provider configuration | A | Concise incompatibility, exact errors, working custom-provider control, configuration example, lost-metadata tradeoff, and concrete enterprise use case. | Could be clearer about whether the desired change is a new auth mode, metadata reuse for custom providers, or both. Minor formatting damage in the body. | focused configuration request |
| 15:36 | [#35637](https://github.com/openai/codex/issues/35637) — persisted GitLab webview crashes one thread | reproducible crash | A | Strong affected-thread/other-thread controls, persistence across reinstall and profile reset, CLI control, repeated timestamped webview/GPU sequence, and disciplined treatment of plugin reconciliation as secondary. | Cannot reproduce creation of the bad state from a fresh thread, so the report identifies a deterministic recovery failure but not a minimal creation path. Long but coherent. | strong thread-state forensic report |

## What the “meh” submissions actually look like

The weak material is not only one-line complaints. Several recurring forms create substantial triage waste:

1. **Polished but wrong-owner requests** — #35616 and #35631 are coherent documents, but they ask the Codex repository to own broad ChatGPT Business/export or account-entitlement systems.
2. **Personal workflow pasted as product specification** — #35618 contains a useful source observation, then buries it under a very large custom prompt and several different requested remedies.
3. **Forensic overproduction** — #35619 may contain the strongest raw evidence in the block, yet its length, live corrections, and second possible deletion scope make first-pass comprehension unnecessarily difficult.
4. **Discovery failure disguised as a feature gap** — #35626 spent substantial effort specifying behaviour already available through `/title`.
5. **Literal duplicate posting** — #35630 and #35632 are nearly the same issue. High report quality does not cancel the triage cost of duplicated threads.
6. **Hostile multi-bug dumping** — #35622 combines localisation, menu actions, project movement, and general release-quality complaints without a usable reproduction.
7. **Solution architecture without incident evidence** — #35631 provides an entitlement design framework but no publicly verifiable event demonstrating the asserted overwrite.

## Strong patterns in this block

The best reports repeatedly use one of four structures:

- **controlled comparison:** old task versus new task (#35634), Android-created versus desktop-created thread (#35617), host shell versus V8 isolate (#35633);
- **state transition with a sharp boundary:** app-server restart and missing files (#35619), stale persisted Voice pointer (#35629);
- **raw boundary evidence:** wrong tool already present in streamed model output (#35620);
- **correlated independent logs:** Codex process events plus Windows Code Integrity/AppModel events (#35625, #35635, #35637).

These structures are more important than length or polish. A short report can be excellent when it isolates the variable; a long report can still be costly even when technically sophisticated.

## Early catalogue conclusions

- **10 of 20** are strongly actionable on the issue body alone.
- **6 of 20** create serious avoidable triage cost through wrong product fit, unnecessary length, already-supported behaviour, or weak bundling.
- **2 of 20** are duplicate representations of the same underlying report.
- The main quality problem in this slice is not lack of technical detail. It is **failure to control scope and information volume**.
- Very recent Codex issues appear unusually likely to include source inspection, local database analysis, raw logs, proposed implementation details, and extensive controls. That may reflect current model-assisted issue writing. It also means verbosity and confident diagnosis need to be judged more aggressively, not rewarded automatically.

## Next chronological block

Continue immediately below #35616, using the next 20 issue records in descending issue-number order while preserving chronological order inside the block. Track whether the unusually high technical sophistication in this block persists or whether it is a local cluster of model-assisted submissions.
