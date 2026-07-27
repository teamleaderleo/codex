# Codex issue implementation-value lens

This lens reviews whether a public `openai/codex` issue contributes implementation work that could genuinely save maintainer time. It is independent of the 30-point issue-quality score.

A well-written issue may contain a weak or misleading fix. A poorly written issue may link an excellent tested patch.

## Scale

| Value | Meaning |
|---:|---|
| **5/5** | Inspectable tested implementation, or an exact previously merged fix that can be reapplied; substantial maintainer time plausibly saved. |
| **4/5** | Patch-ready proposal or claimed validated branch with exact source locations, invariants and tests; integration review remains. |
| **3/5** | Useful diagnosis and credible fix direction, but meaningful design, assembly or validation work remains. |
| **2/5** | Partial or speculative implementation idea; may save search time but not coding time. |
| **1/5** | Solution-shaped prose or technically questionable suggestion that may distract more than help. |
| **0/5** | No implementation contribution. |

Implementation type is recorded separately:

- **WORKING** — linked code, commit, branch or completed artefact;
- **KNOWN-GOOD** — identifies an exact prior merged implementation that fixes the same regression;
- **PATCH-READY** — no submitted code, but the change points, semantics and tests are sufficiently bounded;
- **DIAGNOSTIC** — source analysis helps locate the work, but the proposed correction is incomplete;
- **SOLUTIONEERING** — implementation language outruns the evidence or leaves the core engineering decision unresolved.

## Highest-value implementation contributions

| Issue | Issue score | Implementation value | Assessment |
|---|---:|---:|---|
| [#35486](https://github.com/openai/codex/issues/35486) — recover closed MCP transports | 18/30 · D | **5/5 · WORKING** | The linked commit was inspected. It rebuilds closed transports behind the recovery semaphore, shares recovery across concurrent callers, avoids replaying an interrupted tool call, preserves the HTTP 404 retry path, tracks replacement stdio processes for shutdown, and adds dedicated preclosed/concurrency/no-replay/process-cleanup regressions. The issue body overclaims environment coverage, but the code contribution is substantial and unusually complete. |
| [#35511](https://github.com/openai/codex/issues/35511) — resolve pasted image filenames through clipboard file list | 27/30 · A | **5/5 · WORKING** | The linked two-file commit was inspected. It adds a narrowly scoped clipboard fallback, consolidates image-extension checks, validates that the matching file is actually decodable, handles Windows filename case rules, and includes focused unit tests. Remaining review questions are small: duplicate basenames, synchronous clipboard/image probing, and lack of an end-to-end clipboard integration test. |
| [#35413](https://github.com/openai/codex/issues/35413) — WSL shortcut-overlay snapshot regression | 28/30 · A | **5/5 · KNOWN-GOOD** | It identifies the exact merged prior fix, [PR #9359](https://github.com/openai/codex/pull/9359), including the two-file test-time gate and focused WSL assertion. This is nearly the ideal regression report: maintainers can compare current code with a previously accepted implementation rather than rediscover the design. |
| [#35613](https://github.com/openai/codex/issues/35613) — code-mode live session IDs | 28/30 · A | **5/5 · WORKING** | The linked work was inspected. It contains an executable before-state regression; a coherent production path from `ToolCallSource::CodeMode` through typed `CellId`, `UnifiedExecContext`, `ProcessEntry`, exact-cell liveness lookup and terminal formatting; focused manager and formatter tests; five local acceptance cases; four Docker/exec-server cases; and two existing compatibility checks. It leaves lifecycle and protocol semantics unchanged and makes the remaining boundaries explicit. The prototype's 64-ID display cap should be removed because the manager cap is soft, validation spans related refs rather than one final SHA, and no broad workspace suite was completed. Those are final integration corrections, not missing investigation or implementation, so the contribution still meets the 5/5 time-saving definition. |
| [#35614](https://github.com/openai/codex/issues/35614) — `gix` advisory bump | 29/30 · S | **4/5 · WORKING** | Claims a validated branch containing the one-line dependency bump, lockfile updates and Bazel lock refresh, with `cargo check`, 28 package tests and lock verification. This likely saves real time, but the branch was not independently inspected during this review. |
| [#35501](https://github.com/openai/codex/issues/35501) — original terminal pet | 23/30 · C | **3/5 · WORKING ARTEFACT** | Supplies a completed 8×9 WebP atlas covering the existing pet state tracks. If the asset is accepted, the creative production work is already done. It saves less engineering time because product acceptance and catalogue integration are the main unresolved questions. |

## Strong patch-ready proposals

| Issue | Issue score | Implementation value | Why it saves time |
|---|---:|---:|---|
| [#35496](https://github.com/openai/codex/issues/35496) — intraline diff highlighting | 27/30 · A | **4/5 · PATCH-READY** | Names `diff_render.rs`, proposes a private module, reuses the already-pinned `similar` crate, separates range computation from styling, specifies Unicode and deadline bounds, and provides a broad but relevant test matrix. Maintainers still need to choose pairing/styling details. |
| [#35415](https://github.com/openai/codex/issues/35415) — expose web-search mode/results in exec JSONL | 27/30 · A | **4/5 · PATCH-READY** | Traces both missing fields through internal item types, event projection and public JSONL types. The proposed changes are additive and reuse existing opaque result data and `WebSearchMode`. It removes most code-discovery work, though compatibility and event-shape decisions remain. |
| [#35401](https://github.com/openai/codex/issues/35401) — plugin cache rewrite amplification | 29/30 · S | **4/5 · PATCH-READY** | Maps the unconditional writer, refresh scheduling, missing TTL and cross-version cache-key interaction. It orders four corrections from smallest local win to broader invalidation policy. No patch is supplied, but the implementation search space is already sharply reduced. |
| [#35527](https://github.com/openai/codex/issues/35527) — Windows CP-1252 Unicode crash | 29/30 · S | **4/5 · PATCH-READY** | Identifies the exact Python script and subprocess boundary, supplies the successful `PYTHONUTF8=1` control, and proposes explicit UTF-8 decoding, primary-error preservation and a Unicode fixture. The patch itself should be small; repository ownership for the bundled plugin is the main friction. |
| [#35444](https://github.com/openai/codex/issues/35444) — true all-day Calendar events | 28/30 · A | **4/5 · PATCH-READY** | Establishes the connector-schema mismatch against Google Calendar's `start.date`/`end.date` representation and proposes two bounded API shapes. The upstream semantic rule and exclusive end date are already captured; maintainers mainly need to choose the public schema. |
| [#35503](https://github.com/openai/codex/issues/35503) — provider-scoped 401 recovery budget | 28/30 · A | **4/5 · PATCH-READY** | Names the configuration field, default compatibility, HTTP and WebSocket paths, source anchors and five acceptance tests. It is implementation-oriented without requiring a broad authentication redesign. |

## Useful diagnosis, but not drop-in work

| Issue | Issue score | Implementation value | Limitation |
|---|---:|---:|---|
| [#35455](https://github.com/openai/codex/issues/35455) — history trimming stops early | 29/30 · S | **3/5 · DIAGNOSTIC** | Correctly identifies the blocking `break` and the desired skip behaviour. The shown `continue` is not a complete patch: the report itself notes that rewritten items must be reassembled at original positions. Good diagnosis, but maintainers still own the data-structure change and tests. |
| [#35450](https://github.com/openai/codex/issues/35450) — unbounded MCP pagination | 28/30 · A | **2/5 · DIAGNOSTIC** | The missing bound and affected loops are useful. The proposed `100`-page cap is arbitrary, mixes page and resource limits, and returns partial success after warning; maintainers must decide the protocol/error semantics and write the adversarial tests. |
| [#35445](https://github.com/openai/codex/issues/35445) — 100 ms attestation timeout | 26/30 · B | **2/5 · DIAGNOSTIC** | Points to the exact timeout and plausible blocking path, but lacks latency measurements and a controlled reproduction. Raising a constant may hide rather than solve the interaction. |
| [#35628](https://github.com/openai/codex/issues/35628) — Mermaid TUI rendering | 22/30 · C | **2/5 · SOLUTIONEERING** | Contains substantial renderer/fallback design, but product acceptance, dependency choice, streaming behaviour and terminal capability policy remain the hard work. The detail is useful context, not a ready patch. |

## Code-shaped proposals that do not save much time

| Issue | Issue score | Implementation value | Why not |
|---|---:|---:|---|
| [#35451](https://github.com/openai/codex/issues/35451) — MCP meta serialization | 28/30 · A | **1/5 · SOLUTIONEERING** | No concrete value that actually triggers serialization failure is supplied. The suggested code only logs the error and still drops `meta`, so it does not meet the stated goal of preserving sandbox state. The security consequence is asserted rather than demonstrated. |
| [#35618](https://github.com/openai/codex/issues/35618) — Responses Lite/tool policy | 17/30 · D | **1/5 · SOLUTIONEERING** | A real source observation is followed by multiple competing remedies and a giant personal prompt. It increases the decision surface instead of delivering a bounded implementation. |
| [#35528](https://github.com/openai/codex/issues/35528) — faithful residual contract | 17/30 · D | **1/5 · SOLUTIONEERING** | Defines a cross-cutting residual architecture spanning shell truncation, durable storage, compaction and Code Mode. It may be thoughtful systems design, but it does not save time on one independently mergeable change. |
| [#35460](https://github.com/openai/codex/issues/35460) — typed Hugging Face Jobs lifecycle operation | 17/30 · D | **1/5 · SOLUTIONEERING** | Proposes a highly specific connector-owned lifecycle protocol from one bounded measurement. Maintainers would still need to validate the product abstraction, provider contract and ownership before the code proposal becomes useful. |

## Main conclusion

The implementation lens changes the ranking materially:

- **#35486** is the clearest positive inversion: a weakly framed issue carrying a high-value tested patch.
- **#35613** is a top-tier implementation contribution whose linked artefacts must be inspected before grading; its remaining work is explicit integration cleanup, not rediscovery.
- **#35451** is the clearest negative inversion: a strong-looking source report carrying a weak proposed correction.
- Source anchors save investigation time only when they identify a real invariant and constrain the correction.
- Tests, compatibility behaviour, failure semantics and cleanup ownership are more valuable than the mere presence of a code block.
- Actual contributor code should be reviewed as code; it should not automatically increase the issue-quality score.

Future catalogue entries should record a separate implementation value only when the issue contains code, a linked artefact, source-level fix proposal, or a precise prior implementation. Routine issues should remain unmarked rather than receiving `0/5` noise.
