# Codex issue-quality catalog — pass 007–011

Review date: 2026-07-28. This pass covers the 100 public issues in the contiguous repository-number interval **#35501 through #35400**, excluding pull requests [#35414](https://github.com/openai/codex/pull/35414) and [#35408](https://github.com/openai/codex/pull/35408). Full issue bodies were reviewed; comments were consulted only when needed for interpretation. No upstream comments or reactions were posted.

Scores use the 30-point rubric in `reviewer-research-brief.md`. The number is primary; the band is a compact summary. Flags are independent of score.

**Distribution:** S 12 · A 27 · B 19 · C 21 · D 13 · E 4 · F 4

## Block 007 — #35501 through #35484

| Issue | Score / flags | Judgement |
|---|---|---|
| [#35501](https://github.com/openai/codex/issues/35501) — original 8-bit terminal pet | 23/30 · C · ENTERTAINING | Well-bounded asset proposal with a completed atlas, but still a novelty catalogue request rather than a product defect. |
| [#35500](https://github.com/openai/codex/issues/35500) — text task cannot switch to live Voice | 25/30 · B | Clear current-versus-desired behaviour and user impact; needs a sharper account/model support boundary. |
| [#35499](https://github.com/openai/codex/issues/35499) — Browser Use and Mobile Remote stopped after update | 21/30 · C | Useful multi-machine/version contrast, but combines two integrations and leaves the actual update boundary uncertain. |
| [#35498](https://github.com/openai/codex/issues/35498) — Work/Codex voice missing in API-key mode | 25/30 · B | Compact authentication-mode comparison with a crisp UI inconsistency; limited protocol evidence. |
| [#35497](https://github.com/openai/codex/issues/35497) — Brave selected but native-host manifest not repaired | 28/30 · A · INTERESTING | Excellent unsupported-browser inconsistency report: detection, installer and manifest verification disagree in a testable way. |
| [#35496](https://github.com/openai/codex/issues/35496) — intraline diff highlighting | 27/30 · A | Strong source-aware feature proposal with bounded fallback and contribution-policy awareness; modestly overdesigned. |
| [#35495](https://github.com/openai/codex/issues/35495) — Remote controller WebSocket ignores system proxy | 29/30 · S · ULTRA · INTERESTING | Exceptional network-boundary report with direct/proxied controls, exact failing surface and a narrow proxy invariant. |
| [#35494](https://github.com/openai/codex/issues/35494) — “how long update codex cli?” | 1/30 · F · ENTERTAINING | A one-line release-status question filed as an issue; no defect, environment or requested repository change. |
| [#35493](https://github.com/openai/codex/issues/35493) — duplicate Terra entries in model picker | 26/30 · B | Specific metadata mismatch with cache evidence, though it overlaps the nearby hidden-model exposure report. |
| [#35492](https://github.com/openai/codex/issues/35492) — Arch Linux near-bricking narrative | 11/30 · E · INTERESTING · ENTERTAINING | A real safety concern buried in an uncontrolled full-access anecdote, confused platform claims and unsafe passwordless sudo. |
| [#35491](https://github.com/openai/codex/issues/35491) — no Browser/Chrome access in WSL mode | 19/30 · D | Understandable capability gap, but sparse reproduction and no distinction between intended WSL limitations and regression. |
| [#35490](https://github.com/openai/codex/issues/35490) — Realtime V3 sideband blocked by Cloudflare | 29/30 · S · ULTRA · INTERESTING | Excellent protocol/network isolation with related-report distinctions, endpoint evidence and User-Agent controls. |
| [#35489](https://github.com/openai/codex/issues/35489) — browser forces dark theme | 21/30 · C | Clear visual symptom and easy reproduction, but expected colour-scheme semantics and website controls are thin. |
| [#35488](https://github.com/openai/codex/issues/35488) — Dock icon position resets on update | 27/30 · A | Focused macOS lifecycle regression with exact bundle identity and repeatable update boundary. |
| [#35487](https://github.com/openai/codex/issues/35487) — model menu overwrites custom-provider profile | 27/30 · A | Strong config-before/after report with a precise destructive state transition. |
| [#35486](https://github.com/openai/codex/issues/35486) — PR approval for Transport Closed bug | 18/30 · D | Potentially useful contribution request, but overclaims all-platform reproducibility and uses an old version without a clean current case. |
| [#35485](https://github.com/openai/codex/issues/35485) — `node_repl` leak, one per thread | 29/30 · S · ULTRA · INTERESTING | Benchmark lifecycle report: counts, parentage, idle CPU, per-thread growth and the exact app-server exit boundary. |
| [#35484](https://github.com/openai/codex/issues/35484) — separate ChatGPT and Codex account sessions | 20/30 · C · INTERESTING | Coherent request, but usage-balancing across user accounts creates policy/ownership ambiguity beyond a normal repository change. |

## Block 008 — #35483 through #35466

| Issue | Score / flags | Judgement |
|---|---|---|
| [#35483](https://github.com/openai/codex/issues/35483) — lower-cost browser/computer usage | 18/30 · D | Clear economic complaint but primarily billing/product policy, with no measured accounting or repository-owned mechanism. |
| [#35482](https://github.com/openai/codex/issues/35482) — lost child process and 205 GB deleted log | 28/30 · A · INTERESTING | High-value process/resource forensic with a dramatic observed chain; slightly too broad and hazardous to reproduce cleanly. |
| [#35481](https://github.com/openai/codex/issues/35481) — Codex Diff “Oops” error | 17/30 · D | Generic visible failure with basic environment data, but little trigger isolation, error detail or component boundary. |
| [#35480](https://github.com/openai/codex/issues/35480) — custom live activity indicator | 22/30 · C | Plausible extension point with examples, but mixes user customisation and ecosystem integration without proving demand. |
| [#35479](https://github.com/openai/codex/issues/35479) — Antigravity proposed-API incompatibility | 26/30 · B · INTERESTING | Good rollback control and exact compatibility boundary; third-party IDE ownership limits repository actionability. |
| [#35478](https://github.com/openai/codex/issues/35478) — Chrome extension disappears while host remains | 24/30 · B | Useful component isolation and recurrence description, but the uninstall/removal trigger remains unknown. |
| [#35477](https://github.com/openai/codex/issues/35477) — “Sol 5.6 Bug” | 6/30 · F · ENTERTAINING | “The new one” plus a broad quality and credit complaint supplies no representative task, output or controlled comparison. |
| [#35476](https://github.com/openai/codex/issues/35476) — SMB/UNC workspaces fail in both sandboxes | 27/30 · A | Strong cross-mode Windows reproduction with exact share semantics and failure contrasts. |
| [#35475](https://github.com/openai/codex/issues/35475) — quarantine failed browser state on restore | 26/30 · B · INTERESTING | Strong recovery-oriented crash report; substantial solution design slightly outruns the demonstrated minimum defect. |
| [#35474](https://github.com/openai/codex/issues/35474) — Voice disconnects after 15–20 seconds | 25/30 · B | Sharp timing, exact transport error and useful text-path control; network and repeated-session controls could be stronger. |
| [#35473](https://github.com/openai/codex/issues/35473) — Projects cannot create/move chats on Mac | 25/30 · B | Good web-versus-desktop control and concrete missing actions, though likely a broader ChatGPT product-surface issue. |
| [#35472](https://github.com/openai/codex/issues/35472) — partial plugin materialisation causes uninstall | 29/30 · S · ULTRA · INTERESTING | Exceptional failure chain: partial copy failure is treated as authoritative and destructive reconciliation runs on focus. |
| [#35471](https://github.com/openai/codex/issues/35471) — PowerShell crashes in `ConsoleControl` | 25/30 · B | Specific process failure and environment evidence, but triggering command and repeatability are not as clean as the diagnosis. |
| [#35470](https://github.com/openai/codex/issues/35470) — image copied 150,000 times, 400 GiB | 22/30 · C · INTERESTING · ENTERTAINING | Spectacular resource incident with concrete scale, but likely entangles model behaviour, task instructions and missing guardrails. |
| [#35469](https://github.com/openai/codex/issues/35469) — Japanese IME stuck in alphanumeric mode | 28/30 · A | Excellent platform/input report with a simple another-tab recovery control and exact locale/terminal context. |
| [#35468](https://github.com/openai/codex/issues/35468) — sandbox setup refresh errors block edits | 20/30 · C | Clear blocker and exact error, but sparse setup details and no comparison across sandbox modes or fresh workspace state. |
| [#35467](https://github.com/openai/codex/issues/35467) — colour labels for projects/chats | 23/30 · C | Well-explained navigation need and concrete UI proposal; more product preference than verified usability defect. |
| [#35466](https://github.com/openai/codex/issues/35466) — persistent project-aware voice navigation | 16/30 · D · INTERESTING | Thoughtful voice vision that expands into routing, agents, mobile-first design and autonomy rather than one deliverable. |

## Block 009 — #35465 through #35450

| Issue | Score / flags | Judgement |
|---|---|---|
| [#35465](https://github.com/openai/codex/issues/35465) — disappearance, residual processes, GPU and AppX failures | 20/30 · C · INTERESTING | Rich incident evidence across builds, but several failure layers are bundled into one sprawling reliability report. |
| [#35464](https://github.com/openai/codex/issues/35464) — existing conversations crash GPU process | 27/30 · A | Strong old-versus-new conversation control and exact package/GPU context; crowded duplicate cluster lowers novelty. |
| [#35463](https://github.com/openai/codex/issues/35463) — subagents drain weekly quota overnight | 17/30 · D | Severe usage claim with environment context, but weak accounting evidence and no per-agent or task-level measurement. |
| [#35462](https://github.com/openai/codex/issues/35462) — add Flint as file-open destination | 24/30 · B | Focused ecosystem integration request with command semantics and line/column behaviour; modest adoption uncertainty. |
| [#35461](https://github.com/openai/codex/issues/35461) — completed subagents remain Active after reboot | 27/30 · A · INTERESTING | Excellent persisted-state versus backend-liveness mismatch with a clean reboot boundary and visible impact. |
| [#35460](https://github.com/openai/codex/issues/35460) — typed Hugging Face Jobs lifecycle operation | 17/30 · D · INTERESTING | Sophisticated connector contract derived from one bounded measurement, but highly solution-owned and difficult to triage. |
| [#35459](https://github.com/openai/codex/issues/35459) — Meta Ads MCP returns `Sse(None)` | 28/30 · A | Strong interoperability report with exact transport, endpoint, authentication and handshake boundary. |
| [#35458](https://github.com/openai/codex/issues/35458) — screenshots amplified to 165 GiB of session storage | 29/30 · S · ULTRA · INTERESTING | Exceptional storage-amplification forensic with measured rates, file composition, compaction/fork mechanics and silent-risk impact. |
| [#35457](https://github.com/openai/codex/issues/35457) — CSP resources blocked and Statsig warnings | 25/30 · B | Disciplined low-severity report that separates cosmetic console noise from working core control. |
| [#35456](https://github.com/openai/codex/issues/35456) — changed and broke sudo password | 12/30 · E · INTERESTING · ENTERTAINING | Potentially serious unsafe action, but random reproduction, full-access credentials and screenshots cannot isolate policy or command generation. |
| [#35455](https://github.com/openai/codex/issues/35455) — history trimming stops early | 29/30 · S · ULTRA | Benchmark source-level bug: exact loop defect, reproducible consequence and bounded correction. |
| [#35454](https://github.com/openai/codex/issues/35454) — concise reasoning summaries overridden | 27/30 · A | Precise config-to-effective-value mismatch with rollout evidence and a narrow expected invariant. |
| [#35453](https://github.com/openai/codex/issues/35453) — stale CDP session leaves turn active | 25/30 · B · INTERESTING | Strong lifecycle symptom and exact channel failure, but external browser-session involvement complicates ownership. |
| [#35452](https://github.com/openai/codex/issues/35452) — Voice creates projectless temporary task | 27/30 · A | Excellent project-association regression with a simple product-level reproduction. |
| [#35451](https://github.com/openai/codex/issues/35451) — MCP meta failure drops sandbox state | 28/30 · A · INTERESTING | Strong source-level correctness and safety report with exact fallback consequence and affected locations. |
| [#35450](https://github.com/openai/codex/issues/35450) — unbounded MCP pagination can OOM | 28/30 · A | Clear adversarial pagination reproduction and source anchors; suggested fixed page limit is somewhat arbitrary. |

## Block 010 — #35449 through #35433

| Issue | Score / flags | Judgement |
|---|---|---|
| [#35449](https://github.com/openai/codex/issues/35449) — `apply_patch` hangs while shell works | 22/30 · C | Useful tool-specific control, but limited logs, trigger detail and recurrence data. |
| [#35448](https://github.com/openai/codex/issues/35448) — disabled MCP config breaks third-party discovery | 26/30 · B · INTERESTING | Strong cross-tool configuration leakage case with exact invalid-path mechanism and recovery failure. |
| [#35447](https://github.com/openai/codex/issues/35447) — actionable Desktop Pets task strip | 16/30 · D · ENTERTAINING | A lovingly detailed pet control-surface redesign sprawling across execution, approvals, snoozing and context display. |
| [#35446](https://github.com/openai/codex/issues/35446) — Windows 10 Computer Use bitmap deadlock | 29/30 · S · ULTRA · INTERESTING | Exceptional frame-pipeline isolation down to the synchronous wait inside `FrameArrived`. |
| [#35445](https://github.com/openai/codex/issues/35445) — 100 ms attestation timeout blocks compaction | 26/30 · B | Strong source-aware timing hypothesis, but needs measured latency distribution and direct reproduction. |
| [#35444](https://github.com/openai/codex/issues/35444) — Calendar plugin cannot create all-day events | 28/30 · A | Excellent connector-schema mismatch with the exact upstream semantic requirement and clearly wrong workaround. |
| [#35443](https://github.com/openai/codex/issues/35443) — Ghostty exit leaves raw keyboard fragment | 29/30 · S · ULTRA · INTERESTING | Tiny, exact terminal restoration bug with versions, protocol fragment and shell-visible outcome. |
| [#35442](https://github.com/openai/codex/issues/35442) — custom pet idle animation overridden | 27/30 · A · ENTERTAINING | Clean pet-animation state-precedence bug with an executable atlas-level reproduction. |
| [#35441](https://github.com/openai/codex/issues/35441) — output preview crashes on null dirname | 29/30 · S · ULTRA | Excellent cross-device control and exact null-path boundary after a package update. |
| [#35440](https://github.com/openai/codex/issues/35440) — Dodo Payments crashes GPU process | 27/30 · A · INTERESTING | Strong URL-specific crash with DOM-ready timing, driver control and normal-Chrome comparison. |
| [#35439](https://github.com/openai/codex/issues/35439) — Printify/Cloudflare page crashes app | 20/30 · C | Credible trigger and severe symptom, but “latest” versioning and limited evidence make it weaker than cluster peers. |
| [#35438](https://github.com/openai/codex/issues/35438) — cursor jumps and IME quotes disappear | 20/30 · C | Two distinct terminal/input defects bundled together; environment is solid but the issue should be split. |
| [#35437](https://github.com/openai/codex/issues/35437) — permissions profile makes sandbox abort | 29/30 · S · ULTRA | Benchmark model-free reproduction with baseline/control commands, exact SIGABRT boundary and feature interaction. |
| [#35436](https://github.com/openai/codex/issues/35436) — WSL mode missing bundled `bwrap` | 27/30 · A | Focused startup failure with a clear missing dependency and handshake symptom. |
| [#35435](https://github.com/openai/codex/issues/35435) — `close_agent` can leak MCP resources | 26/30 · B · INTERESTING | Strong teardown-path analysis, though framed as a follow-on and somewhat implementation-heavy. |
| [#35434](https://github.com/openai/codex/issues/35434) — show credit limit in status icon | 10/30 · E · ENTERTAINING | Single-sentence feature request with no use case, current-state verification or display semantics. |
| [#35433](https://github.com/openai/codex/issues/35433) — background child exhausts system memory | 18/30 · D · INTERESTING | Exceptionally disciplined uncertainty, but no exact build, parent proof or safe reproduction; the proposed contract exceeds the evidence. |

## Block 011 — #35432 through #35400

| Issue | Score / flags | Judgement |
|---|---|---|
| [#35432](https://github.com/openai/codex/issues/35432) — extension switches to another VS Code workspace | 21/30 · C | Important cross-instance symptom, but intermittent trigger and evidence remain weak. |
| [#35431](https://github.com/openai/codex/issues/35431) — long thread restores an old message | 26/30 · B | Strong repeatable viewport-state report with thread-shape context and deep-link exclusion. |
| [#35430](https://github.com/openai/codex/issues/35430) — account-synced Personal Skills | 23/30 · C | Clear cross-device problem and sync model, but broad product scope and security semantics remain unresolved. |
| [#35429](https://github.com/openai/codex/issues/35429) — Remote loses project write access | 20/30 · C | Core failure is understandable, but version/platform details and controls are sparse. |
| [#35428](https://github.com/openai/codex/issues/35428) — `apply_patch` split-root failure | 26/30 · B | Good tool-specific control and exact sandbox error across IDEs. |
| [#35427](https://github.com/openai/codex/issues/35427) — sandbox setup parameter error and app hang | 22/30 · C | Clear Windows blocker and UAC boundary, but uses “latest” and lacks helper diagnostics. |
| [#35426](https://github.com/openai/codex/issues/35426) — annotations expose raw Markdown | 23/30 · C · INTERESTING | Interesting source-versus-rendered-text mismatch, but a locally patched app and custom provider materially confound it. |
| [#35425](https://github.com/openai/codex/issues/35425) — empty browser keep-list terminates backend | 27/30 · A · INTERESTING | Strong exact-call lifecycle report with a crisp success-then-process-loss sequence. |
| [#35424](https://github.com/openai/codex/issues/35424) — cyber-policy false positive on PS5 compiler work | 22/30 · C | Plausible false positive and concrete domain, but policy evidence and a minimal benign reproduction are incomplete. |
| [#35423](https://github.com/openai/codex/issues/35423) — Archive entire ChatGPT Projects | 21/30 · C | Straightforward product request, but largely a ChatGPT surface rather than a repository-level defect. |
| [#35422](https://github.com/openai/codex/issues/35422) — full file content fails in non-Git workspaces | 28/30 · A | Excellent Git-versus-non-Git control, file-size/encoding exclusions and precise review-surface failure. |
| [#35421](https://github.com/openai/codex/issues/35421) — shell discards output beyond 1 MiB | 29/30 · S · ULTRA · INTERESTING | Exceptional two-stage loss accounting with exact source/version anchors and model-visible evidence. |
| [#35420](https://github.com/openai/codex/issues/35420) — OneDrive degradation correlates with disconnects | 16/30 · D · INTERESTING | Carefully labelled correlation, but the bridge from OneDrive billing state to remote stream failure remains weak. |
| [#35419](https://github.com/openai/codex/issues/35419) — IDE context disables in WSL2 | 22/30 · C | Clear context failure with exact environment, but likely combines state toggling and attachment transport. |
| [#35418](https://github.com/openai/codex/issues/35418) — no plain-text paste for long code | 25/30 · B | Focused shortcut conflict with exact behaviour and a bounded alternative. |
| [#35417](https://github.com/openai/codex/issues/35417) — withdrawn Remote SSH request | 3/30 · F · ENTERTAINING | No remaining technical request; the entire issue is a withdrawal and apology for filing without owner approval. |
| [#35416](https://github.com/openai/codex/issues/35416) — reasoning-level changes cause cache misses | 28/30 · A · INTERESTING | Excellent measured sequence: first-use effort levels invalidate cache while returning levels do not; uncertainty is explicit. |
| [#35415](https://github.com/openai/codex/issues/35415) — expose web-search mode and results in JSON | 27/30 · A | Strong source-aware observability request with a real automation/provenance use case and bounded fields. |
| [#35413](https://github.com/openai/codex/issues/35413) — WSL shortcut-overlay snapshot regression | 28/30 · A | Strong regression-oriented source/test report with a precise prior-change boundary. |
| [#35412](https://github.com/openai/codex/issues/35412) — configurable voice keep-alive | 23/30 · C | Clear need and bounded setting options, but no measured current timeout or usage-cost analysis. |
| [#35411](https://github.com/openai/codex/issues/35411) — browser exits after SwiftShader integrity block | 27/30 · A | Strong repeated cluster report with exact Code Integrity event; less novel than the best cluster exemplar. |
| [#35410](https://github.com/openai/codex/issues/35410) — Skill plus conversation reference hangs | 27/30 · A · INTERESTING | Excellent one-reference-versus-other-reference control and pre-turn boundary. |
| [#35409](https://github.com/openai/codex/issues/35409) — thread goes missing and rejects messages | 15/30 · D | High-impact state loss with screenshot, but “latest”, no logs and little recovery or thread-shape evidence. |
| [#35407](https://github.com/openai/codex/issues/35407) — elevated setup repeats due to marker | 27/30 · A | Strong persisted-marker and repeated-setup diagnosis with exact package/runtime context. |
| [#35406](https://github.com/openai/codex/issues/35406) — sandbox cannot reach OpenSSH agent pipe | 28/30 · A | Excellent model-free endpoint-connectivity control separating signing failure from filesystem access. |
| [#35405](https://github.com/openai/codex/issues/35405) — “Prepare Quotation Documents” | 0/30 · F · ENTERTAINING | A user task—prepare three different quotations—mistakenly filed as a repository issue. |
| [#35404](https://github.com/openai/codex/issues/35404) — build failure with OpenSSL 4.0 | 25/30 · B | Standard actionable compatibility report with exact HEAD and reproduction, though limited root-cause analysis. |
| [#35403](https://github.com/openai/codex/issues/35403) — Windows-control connection unavailable | 17/30 · D | Repeated error and troubleshooting attempts, but no task boundary, logs or exact plugin/server state. |
| [#35402](https://github.com/openai/codex/issues/35402) — tasks do not sync and wrong home opens | 17/30 · D | Two unrelated desktop behaviours bundled together with limited reproduction and ownership clarity. |
| [#35401](https://github.com/openai/codex/issues/35401) — plugin cache writes ~65 GB/day | 29/30 · S · ULTRA · INTERESTING | Exceptional measurement, byte-identical rewrite proof, mechanism separation and a clear cache-invalidation defect. |
| [#35400](https://github.com/openai/codex/issues/35400) — one plan consumed ~100 credits | 11/30 · E · ENTERTAINING | Potential billing anomaly with rough environment data, but no task transcript, usage ledger or controlled baseline. |

## Synthesis after 220 reviewed issues

1. **Resource disasters are not automatically S-tier reports.** Several incidents involve hundreds of gigabytes, system memory exhaustion or destructive credential changes. The score depends on ownership evidence, controls and reproducibility—not the size of the damage.
2. **The strongest new cluster is lifecycle/resource accounting.** #35485, #35482, #35458, #35453, #35435, #35433 and #35421 show different forms of invisible or lossy ownership across processes, output and durable state.
3. **Small protocol-boundary reports remain dominant.** #35443, #35444, #35446, #35451, #35455 and #35495 are easier to act on than broad product or architecture proposals.
4. **Product-policy requests continue to score lower despite polished writing.** Separate-account usage balancing, lower-cost Computer Use and cross-product voice layers are coherent but not bounded repository tickets.
5. **The entertainment category remains independent of quality.** This pass includes a fully built terminal pet, a 400 GiB copy storm, a one-line CLI-update question, a withdrawn apology, and an ordinary work request accidentally filed as an issue.
6. **#35613 still compares well.** The nearby lifecycle reports reinforce the value of naming exactly where ownership or visibility fails rather than treating every live-process symptom as one umbrella bug.

Next chronological boundary: immediately below [#35400](https://github.com/openai/codex/issues/35400).