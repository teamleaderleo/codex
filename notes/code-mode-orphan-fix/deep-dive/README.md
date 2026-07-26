# Patch 1 deep-dive documentation workspace

Status: internal working material; not part of the upstream candidate and not automatically public.

This directory separates the concise maintainer-facing issue and pull request from the exhaustive engineering record. The public issue/PR should remain readable. Detailed evidence, investigation history, discarded paths, code walkthroughs, and validation archaeology belong here and may be linked selectively.

## Intended outputs

1. `human-synthesis.md`
   - The human author's own two-paragraph account of what was observed, why it matters, and why the selected fix is proportionate.
   - AI may help edit, but the voice and judgement remain explicitly human.

2. `agent-1-investigation-reconstruction.md`
   - Chronological reconstruction of how the problem was discovered.
   - Log/JSONL evidence, scripts and filters used, hypotheses tested, false leads, state-model discoveries, and the transition from symptom to executable reproduction.
   - Every concrete claim should cite a commit, note, code location, log excerpt, script, or preserved artifact when available.
   - Clearly distinguish preserved evidence from recollection and inference.

3. `agent-2-test-validation-archaeology.md`
   - Why the repository's aggregate test convention matters.
   - Why the standalone target was rejected, how cleanup and deterministic exit handling evolved, exact `just test` conventions, broad-suite differential reasoning, and discarded validation approaches.
   - Include commands, result summaries, and citations to repository convention comments and test code.

4. `agent-3-code-walkthrough.md`
   - A Rust-beginner-friendly walkthrough of the complete production and test diff.
   - Explain the runtime path from code-mode cell to nested unified exec, process storage, liveness query, and terminal status rendering.
   - Explain ownership, `Option<CellId>`, `Arc`, `Weak`, mutex scope, async boundaries, test fixtures, and why each changed field/function exists.
   - Include code links and line-level references.
   - Include a section titled “What this patch does not do.”

5. `agent-3-design-decisions.md`
   - Decision record for the chosen visibility-only fix.
   - Alternatives considered or surfaced during review, including lifecycle cleanup, generic process-origin modelling, JavaScript-schema changes, call-ID parsing, a second registry, display capping, event/wake-up changes, process recovery, and broader signal APIs.
   - For each: why it was considered, why it was rejected or deferred, and what evidence would be needed to reopen it.

6. `agent-4-publication-architecture.md`
   - A three-layer publication design:
     1. concise human synthesis;
     2. maintainers' technical issue/PR body;
     3. collapsible exhaustive appendix/evidence index.
   - Audit the current titles and bodies for overclaim, TMI, unexplained brevity, repetition, weak evidence, missing code citations, and maintainer relevance.
   - Propose more descriptive titles and selective `<details>` sections without turning the issue into a research dump.

7. `evidence-index.md`
   - Canonical links to commits, branches, notes, reproductions, tests, validation receipts, external reviews, related issues, and any preserved log/script artifacts.
   - State access/privacy limitations for any material that is not suitable for immediate publication.

8. `external-review-packet.md`
   - Later-stage packet for independent Codex/Claude review of the deep-dive record and public copy.
   - Review questions should separate factual correctness, Rust/code quality, severity framing, publication quality, and provenance/evidence quality.

## Shared rules

- Do not call this a literal memory leak unless evidence shows unreachable allocated memory. Preferred terms are “orphaned live process”, “resource leak risk”, “lost control-handle visibility”, or “background-process lifecycle hazard”, depending on the claim.
- Do not assign a security severity without a security-impact argument. Operational impact can still be substantial: live processes may retain CPU, memory, file descriptors, sockets, locks, subprocesses, or filesystem state.
- State that background-process persistence is intentional. Patch 1 restores model-visible session IDs; it does not terminate or prevent persistent work.
- Distinguish code-mode emitted-output truncation from later global conversation-history limits.
- Distinguish tests that compile and exercise `codex-core` from building and running every Codex product surface.
- Do not publish chat transcripts, private logs, machine paths, or raw user data by default. Summarise and cite scrubbed evidence; make raw material opt-in.
- Use GitHub `<details>` blocks only for genuinely optional depth, not to hide essential reproduction steps or the core fix contract.
- Record uncertainty and discarded ideas honestly. Do not retrofit a cleaner story than the evidence supports.

## Ownership

- Agent 1: discovery and investigation reconstruction.
- Agent 2: testing, validation, and CI archaeology.
- Agent 3: code walkthrough, design decisions, synthesis and factual gatekeeping.
- Agent 4: publication architecture, copy audit, titles, layered formatting, and evidence presentation.
- Human coordinator: final first-person synthesis, severity judgement, disclosure choices, and publication approval.

## Publication principle

The exhaustive record is evidence for the public copy, not a requirement that every detail appear in the issue. The issue should make the problem and expected behaviour obvious. The PR should make the design and validation reviewable. The deep-dive should preserve the full reasoning trail for maintainers or researchers who choose to expand it.
