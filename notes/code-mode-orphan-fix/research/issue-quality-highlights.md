# Codex issue-quality highlights

This index marks the most memorable entries from the first 120 reviewed `openai/codex` issues. These flags are independent of the numeric quality score.

- **🏆 ULTRA** — exceptional issue-writing exemplar; normally an `S` report at `29–30/30`.
- **🔎 INTERESTING** — technically unusual, analytically instructive, or a useful counterexample/anti-pattern.
- **🎭 ENTERTAINING** — unusually memorable, odd, funny, or spectacular to inspect. This is not a quality endorsement.

An issue may carry more than one flag. There is no quota. Future chronological passes should put the applicable plain-text flags directly beside the score—such as `29/30 · S · ULTRA · INTERESTING`—and append newly notable cases here.

Detailed observations and roasts remain in [`issue-quality-catalog.md`](issue-quality-catalog.md) and [`issue-quality-catalog-pass-002-006.md`](issue-quality-catalog-pass-002-006.md). The authoritative scores are in [`issue-quality-score-ledger.md`](issue-quality-score-ledger.md).

## 🏆 ULTRA — exemplary reports

| Issue | Score | Why it is exemplary |
|---|---:|---|
| [#35620](https://github.com/openai/codex/issues/35620) | 29/30 · S | Baseline/failure controls, clean-state tests, raw model-output boundary evidence, quantified transitions, and disciplined uncertainty. |
| [#35629](https://github.com/openai/codex/issues/35629) | 29/30 · S | Carries the failure from visible symptom to persisted stale pointer, rules out obvious controls, and gives a narrowly successful recovery. |
| [#35599](https://github.com/openai/codex/issues/35599) | 29/30 · S | A specialised terminal-input bug reduced to exact CSI-u packets, active/base layout characters, and a parser-level reproduction. |
| [#35614](https://github.com/openai/codex/issues/35614) | 29/30 · S | Dependency advisories, reachability analysis, validated upgrade, and unusually careful non-overstatement of exploitability. |
| [#35576](https://github.com/openai/codex/issues/35576) | 29/30 · S | Clean viewport-versus-User-Agent mismatch with a minimal SSR reproduction and a precise expected browser invariant. |
| [#35583](https://github.com/openai/codex/issues/35583) | 29/30 · S | Crisp MCP protocol contract, runtime tool-addition reproduction, and an obvious next interoperability test. |
| [#35555](https://github.com/openai/codex/issues/35555) | 29/30 · S | Demonstrates that a telemetry database lock gates CLI boot, with the locking process, timeout behaviour, and retry deficiency isolated. |
| [#35527](https://github.com/openai/codex/issues/35527) | 29/30 · S | Platform encoding failure reduced to Unicode review output, CP-1252 subprocess decoding, and the exact bundled fetcher boundary. |
| [#35534](https://github.com/openai/codex/issues/35534) | 29/30 · S | Exact unsupported enum value, selected model capability mismatch, and a bounded validation/fallback requirement. |
| [#35545](https://github.com/openai/codex/issues/35545) | 29/30 · S | Missing `WINDIR` isolated from `SystemRoot`, with a self-contained WPF crash and environment comparison. |
| [#35505](https://github.com/openai/codex/issues/35505) | 29/30 · S | Exceptional MSIX/AppX forensic: Code Integrity event, regression window, packaged/unpackaged controls, and GPU hypothesis falsification. |
| [#35510](https://github.com/openai/codex/issues/35510) | 29/30 · S | Tiny, exact key-injection contract: tool reports success while Pygame receives no Return event. |
| [#35517](https://github.com/openai/codex/issues/35517) | 29/30 · S | Realtime transcript duplication expressed as an explicit event-order race with the authoritative handoff boundary identified. |

## 🔎 INTERESTING — unusually instructive cases

| Issue | Score | Why it is worth opening |
|---|---:|---|
| [#35613](https://github.com/openai/codex/issues/35613) | 28/30 · A | Distinguishes a handle that never becomes model-visible from adjacent process-lifecycle and model-memory failures. |
| [#35619](https://github.com/openai/codex/issues/35619) | 23/30 · C | Possibly the strongest raw forensics in the sample, while also demonstrating how live corrections and massive detail can damage triage usability. |
| [#35604](https://github.com/openai/codex/issues/35604) | 27/30 · A | An 82-second renderer block traced to synchronous Markdown parsing over roughly 49 million title characters. |
| [#35553](https://github.com/openai/codex/issues/35553) | 18/30 · D | High-stakes macOS keybag incidents with substantial evidence, but a dangerous causal leap toward the Locked Use plugin. |
| [#35554](https://github.com/openai/codex/issues/35554) | 17/30 · D | A completed response allegedly appeared in a different terminal while rollout records remained isolated—a fascinating, low-repeatability anomaly. |
| [#35528](https://github.com/openai/codex/issues/35528) | 17/30 · D | A technically serious “faithful residual” research paper that combines several legitimate loss paths into an unmanageably broad umbrella ticket. |
| [#35582](https://github.com/openai/codex/issues/35582) | 26/30 · B | Completed recurring automations retaining live `node_repl` workers; directly adjacent to the orphan-process research cluster. |
| [#35549](https://github.com/openai/codex/issues/35549) | 24/30 · B | Explicit local allowlisting loses to a central site-status safety block, creating a real product-policy versus user-consent boundary. |
| [#35626](https://github.com/openai/codex/issues/35626) | 18/30 · D | A polished, implementation-aware feature specification for behaviour already available through `/title`. |
| [#35630](https://github.com/openai/codex/issues/35630) / [#35632](https://github.com/openai/codex/issues/35632) | 23/30 · C / 12/30 · E | A good crash report followed two minutes later by a near-verbatim copy from another account. |
| [#35566](https://github.com/openai/codex/issues/35566) | 14/30 · E | An AI-shaped duplicate containing an unfinished “insert GPU info here” style placeholder beside stronger reports of the same crash cluster. |
| [#35546](https://github.com/openai/codex/issues/35546) | 14/30 · E | The title `Permission issue` followed by an enormous unfiltered `codex doctor` dump: a pure diagnostic-landfill specimen. |
| [#35618](https://github.com/openai/codex/issues/35618) | 17/30 · D | A valid source-level tool-policy observation buried under a giant personal prompt and several competing product changes. |
| [#35533](https://github.com/openai/codex/issues/35533) | 17/30 · D | A deeply internal Deep Scan recovery contract whose sophistication makes ownership and the smallest viable change harder to identify. |
| [#35542](https://github.com/openai/codex/issues/35542) | 18/30 · D | A careful cross-surface protocol proposal that shows how prior-art awareness can still turn into overbuilt scope. |
| [#35568](https://github.com/openai/codex/issues/35568) | 17/30 · D | A complete source-level memory governance subsystem—classification, CAS revisions, provenance, revocation, and explanation—presented as one feature issue. |
| [#35586](https://github.com/openai/codex/issues/35586) | 14/30 · E | A full human-agent social-network vision deck filed in the Codex issue tracker. |
| [#35512](https://github.com/openai/codex/issues/35512) | 15/30 · D | Starts with a bounded browser-workspace idea, then expands toward tabs, passkeys, and Codex as the user's default general browser. |

## 🎭 ENTERTAINING — memorable specimens

| Issue | Score | Why it is memorable |
|---|---:|---|
| [#35552](https://github.com/openai/codex/issues/35552) | 0/30 · F | Title and subscription field are both profanity; essentially no technical report survives underneath. |
| [#35570](https://github.com/openai/codex/issues/35570) | 4/30 · F | Titled `clusterf*ck of epic proportions`, with `latest`, `max`, and `sol` standing in for usable environment data. |
| [#35577](https://github.com/openai/codex/issues/35577) | 22/30 · C | A coherent request for multiple simultaneous desktop pets, optionally bound to separate tasks. |
| [#35586](https://github.com/openai/codex/issues/35586) | 14/30 · E | Proposes a Human–Agent Social Graph, friends, groups, public projects, and persistent collaborative assets. |
| [#35626](https://github.com/openai/codex/issues/35626) | 18/30 · D | An impressively elaborate design document defeated by the existing `/title` menu. |
| [#35630](https://github.com/openai/codex/issues/35630) / [#35632](https://github.com/openai/codex/issues/35632) | 23/30 · C / 12/30 · E | The same highly specific Browser-call crash report appears from two accounts within about two minutes. |
| [#35558](https://github.com/openai/codex/issues/35558) | 20/30 · C | A real malformed-property bug framed around the visible gibberish being spam-like and gambling-related. |
| [#35618](https://github.com/openai/codex/issues/35618) | 17/30 · D | A useful policy observation is followed by a prompt dump large enough to become the dominant object in the ticket. |
| [#35546](https://github.com/openai/codex/issues/35546) | 14/30 · E | `Permission issue` plus nearly the full diagnostic universe, with the actual denied operation struggling for oxygen. |
| [#35622](https://github.com/openai/codex/issues/35622) | 7/30 · F | A hostile release-quality complaint bundles localisation, menus, project movement, and general dissatisfaction while calling the expected behaviour self-evident. |
| [#35600](https://github.com/openai/codex/issues/35600) | 5/30 · F | A “significant regression” whose operative evidence is essentially `response off mark`. |
| [#35580](https://github.com/openai/codex/issues/35580) | 7/30 · F | `Random stopping mid-task`: almost the platonic form of a report that names the symptom and supplies none of the boundary. |
| [#35556](https://github.com/openai/codex/issues/35556) | 8/30 · F | `menu left Proyects missing` then pivots into cross-computer project/chat syncing. |

## Future-pass rule

For every newly reviewed issue, assign zero or more of these flags after scoring:

- **ULTRA** only for genuine exemplars, normally `29–30/30`.
- **INTERESTING** when the issue teaches a new technical pattern, quality anti-pattern, or useful counterexample.
- **ENTERTAINING** when it is unusually memorable to inspect, regardless of score.

Do not inflate the flags. A routine strong report needs no marker. Add a one-line reason whenever a marker is assigned.