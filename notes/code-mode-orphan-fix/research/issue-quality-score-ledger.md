# Codex issue-quality score ledger

This ledger recalibrates the first 120 reviewed `openai/codex` issues using the 30-point scale adopted after the initial letter-only passes. The score is primary; the letter is a compact band. Scores were derived from the completed issue-body reviews and their written evidence notes. No forced distribution or curve was applied.

## Scale

Each issue receives 0–5 points for: clarity, scope discipline, reproduction/current-state verification, evidence, context/environment, and repository actionability/diagnosis discipline.

| Band | Score | Meaning |
|---|---:|---|
| S | 29–30 | Exceptional exemplar; essentially no material triage defect |
| A | 27–28 | Excellent; immediately actionable with only minor defects |
| B | 24–26 | Strong; actionable but meaningfully improvable |
| C | 20–23 | Usable or mixed; notable missing evidence, scope cost, or owner uncertainty |
| D | 15–19 | Weak/costly; substantial reconstruction or narrowing required |
| E | 10–14 | Severely deficient, duplicate, or badly mis-scoped |
| F | 0–9 | Non-report, near-content-free complaint, or unusable submission |

## Recalibrated distribution — 120 issues

**S 13** · **A 21** · **B 26** · **C 27** · **D 19** · **E 7** · **F 7**

The original broad A bucket is retired. Existing prose judgements remain useful, but this ledger supersedes their old letter labels.

## Block 001 — #35616–#35637

Detailed observations: [`issue-quality-catalog.md`](issue-quality-catalog.md)

S 2 | A 4 | B 4 | C 4 | D 3 | E 2 | F 1

| Issue | Score | Band | Catalogue tag |
|---|---:|:---:|---|
| [#35616](https://github.com/openai/codex/issues/35616) | 15/30 | D | polished but likely wrong venue |
| [#35617](https://github.com/openai/codex/issues/35617) | 27/30 | A | controlled cross-surface comparison |
| [#35618](https://github.com/openai/codex/issues/35618) | 17/30 | D | valid observation buried in prompt dump |
| [#35619](https://github.com/openai/codex/issues/35619) | 23/30 | C | excellent evidence, excessive cognitive load |
| [#35620](https://github.com/openai/codex/issues/35620) | 29/30 | S | benchmark model-behaviour report |
| [#35622](https://github.com/openai/codex/issues/35622) | 7/30 | F | archetypal low-signal bundle |
| [#35624](https://github.com/openai/codex/issues/35624) | 22/30 | C | usable crash report, weak diagnostics |
| [#35625](https://github.com/openai/codex/issues/35625) | 27/30 | A | high-value forensic crash report |
| [#35626](https://github.com/openai/codex/issues/35626) | 18/30 | D | high-effort unnecessary request |
| [#35627](https://github.com/openai/codex/issues/35627) | 26/30 | B | concise actionable feature request |
| [#35628](https://github.com/openai/codex/issues/35628) | 22/30 | C | strong request, overdesigned body |
| [#35629](https://github.com/openai/codex/issues/35629) | 29/30 | S | benchmark persisted-state report |
| [#35630](https://github.com/openai/codex/issues/35630) | 23/30 | C | strong report, duplicate-channel noise |
| [#35631](https://github.com/openai/codex/issues/35631) | 14/30 | E | polished speculative product programme |
| [#35632](https://github.com/openai/codex/issues/35632) | 12/30 | E | literal duplicate submission |
| [#35633](https://github.com/openai/codex/issues/35633) | 26/30 | B | compact controlled report |
| [#35634](https://github.com/openai/codex/issues/35634) | 28/30 | A | benchmark controlled comparison |
| [#35635](https://github.com/openai/codex/issues/35635) | 26/30 | B | evidence-rich crash report |
| [#35636](https://github.com/openai/codex/issues/35636) | 24/30 | B | focused configuration request |
| [#35637](https://github.com/openai/codex/issues/35637) | 27/30 | A | strong thread-state forensic report |

## Block 002

Detailed observations: [`issue-quality-catalog-pass-002-006.md`](issue-quality-catalog-pass-002-006.md)

S 3 | A 4 | B 4 | C 4 | D 2 | F 2

| Issue | Score | Band | Catalogue tag |
|---|---:|:---:|---|
| [#35589](https://github.com/openai/codex/issues/35589) | 26/30 | B | compact UI interaction report |
| [#35592](https://github.com/openai/codex/issues/35592) | 25/30 | B | focused API gap |
| [#35593](https://github.com/openai/codex/issues/35593) | 22/30 | C | useful case, broad conclusion |
| [#35596](https://github.com/openai/codex/issues/35596) | 26/30 | B | strong CLI contract bug |
| [#35598](https://github.com/openai/codex/issues/35598) | 22/30 | C | good boundary, weak trigger |
| [#35599](https://github.com/openai/codex/issues/35599) | 29/30 | S | benchmark input report |
| [#35600](https://github.com/openai/codex/issues/35600) | 5/30 | F | almost content-free model complaint |
| [#35601](https://github.com/openai/codex/issues/35601) | 27/30 | A | strong schema mismatch |
| [#35602](https://github.com/openai/codex/issues/35602) | 27/30 | A | high-value scheduling forensic |
| [#35603](https://github.com/openai/codex/issues/35603) | 26/30 | B | strong crash/state report |
| [#35604](https://github.com/openai/codex/issues/35604) | 27/30 | A | excellent forensic performance report |
| [#35605](https://github.com/openai/codex/issues/35605) | 21/30 | C | credible one-off state anomaly |
| [#35606](https://github.com/openai/codex/issues/35606) | 17/30 | D | high-impact bundle |
| [#35609](https://github.com/openai/codex/issues/35609) | 21/30 | C | clear but thin UI report |
| [#35610](https://github.com/openai/codex/issues/35610) | 8/30 | F | serious claim, weak evidence |
| [#35611](https://github.com/openai/codex/issues/35611) | 24/30 | B | focused UX request |
| [#35612](https://github.com/openai/codex/issues/35612) | 17/30 | D | reasonable problem, vague owner |
| [#35613](https://github.com/openai/codex/issues/35613) | 28/30 | A | benchmark bounded systems report |
| [#35614](https://github.com/openai/codex/issues/35614) | 29/30 | S | benchmark dependency advisory |
| [#35615](https://github.com/openai/codex/issues/35615) | 26/30 | B | controlled cross-device report |

## Block 003

Detailed observations: [`issue-quality-catalog-pass-002-006.md`](issue-quality-catalog-pass-002-006.md)

S 3 | A 5 | B 4 | C 3 | D 2 | E 1 | F 2

| Issue | Score | Band | Catalogue tag |
|---|---:|:---:|---|
| [#35568](https://github.com/openai/codex/issues/35568) | 17/30 | D | architecture document disguised as issue |
| [#35569](https://github.com/openai/codex/issues/35569) | 25/30 | B | compact visual bug |
| [#35570](https://github.com/openai/codex/issues/35570) | 4/30 | F | pure triage hostility |
| [#35571](https://github.com/openai/codex/issues/35571) | 16/30 | D | plausible bug, weak isolation |
| [#35572](https://github.com/openai/codex/issues/35572) | 21/30 | C | clear severe trigger, limited diagnostics |
| [#35574](https://github.com/openai/codex/issues/35574) | 20/30 | C | common error, weak differentiation |
| [#35575](https://github.com/openai/codex/issues/35575) | 27/30 | A | excellent tiny bug |
| [#35576](https://github.com/openai/codex/issues/35576) | 29/30 | S | benchmark web compatibility report |
| [#35577](https://github.com/openai/codex/issues/35577) | 22/30 | C | coherent whimsical request |
| [#35578](https://github.com/openai/codex/issues/35578) | 13/30 | E | wrong-venue support request |
| [#35579](https://github.com/openai/codex/issues/35579) | 28/30 | A | strong Linux input report |
| [#35580](https://github.com/openai/codex/issues/35580) | 7/30 | F | classic vague stoppage report |
| [#35581](https://github.com/openai/codex/issues/35581) | 26/30 | B | strong metadata mismatch |
| [#35582](https://github.com/openai/codex/issues/35582) | 26/30 | B | strong process-lifecycle report |
| [#35583](https://github.com/openai/codex/issues/35583) | 29/30 | S | benchmark MCP protocol report |
| [#35584](https://github.com/openai/codex/issues/35584) | 27/30 | A | strong cross-filesystem reproduction |
| [#35585](https://github.com/openai/codex/issues/35585) | 22/30 | C | useful persistence evidence |
| [#35586](https://github.com/openai/codex/issues/35586) | 14/30 | E | vision deck in issue form |
| [#35587](https://github.com/openai/codex/issues/35587) | 20/30 | C | specific symptom, thin measurements |
| [#35588](https://github.com/openai/codex/issues/35588) | 21/30 | C | credible crash, crowded cluster |

## Block 004

Detailed observations: [`issue-quality-catalog-pass-002-006.md`](issue-quality-catalog-pass-002-006.md)

S 1 | A 6 | B 5 | C 4 | D 2 | E 1 | F 1

| Issue | Score | Band | Catalogue tag |
|---|---:|:---:|---|
| [#35547](https://github.com/openai/codex/issues/35547) | 25/30 | B | focused environment diagnostic |
| [#35548](https://github.com/openai/codex/issues/35548) | 22/30 | C | reasonable UI exposure request |
| [#35549](https://github.com/openai/codex/issues/35549) | 24/30 | B | strong policy-boundary report |
| [#35550](https://github.com/openai/codex/issues/35550) | 27/30 | A | strong distributed-write contract |
| [#35551](https://github.com/openai/codex/issues/35551) | 26/30 | B | strong startup hang report |
| [#35552](https://github.com/openai/codex/issues/35552) | 0/30 | F | non-report |
| [#35553](https://github.com/openai/codex/issues/35553) | 18/30 | D | strong evidence, dangerous attribution |
| [#35554](https://github.com/openai/codex/issues/35554) | 17/30 | D | important anomaly, low repeatability |
| [#35555](https://github.com/openai/codex/issues/35555) | 29/30 | S | benchmark local-state lock report |
| [#35556](https://github.com/openai/codex/issues/35556) | 8/30 | F | confused support report |
| [#35558](https://github.com/openai/codex/issues/35558) | 20/30 | C | real bug with sensational framing |
| [#35559](https://github.com/openai/codex/issues/35559) | 21/30 | C | clear cosmetic report |
| [#35560](https://github.com/openai/codex/issues/35560) | 26/30 | B | strong launch-crash report |
| [#35561](https://github.com/openai/codex/issues/35561) | 27/30 | A | excellent localisation report |
| [#35562](https://github.com/openai/codex/issues/35562) | 20/30 | C | simple but under-argued feature |
| [#35563](https://github.com/openai/codex/issues/35563) | 25/30 | B | strong sandbox capability report |
| [#35564](https://github.com/openai/codex/issues/35564) | 21/30 | C | useful safety false-positive |
| [#35565](https://github.com/openai/codex/issues/35565) | 21/30 | C | clear request, weak prior art |
| [#35566](https://github.com/openai/codex/issues/35566) | 14/30 | E | AI-shaped duplicate with unfinished fields |
| [#35567](https://github.com/openai/codex/issues/35567) | 26/30 | B | strong multimodal boundary report |

## Block 005

Detailed observations: [`issue-quality-catalog-pass-002-006.md`](issue-quality-catalog-pass-002-006.md)

S 4 | A 2 | B 5 | C 2 | D 4 | E 3

| Issue | Score | Band | Catalogue tag |
|---|---:|:---:|---|
| [#35522](https://github.com/openai/codex/issues/35522) | 21/30 | C | good symptom, uncertain owner |
| [#35526](https://github.com/openai/codex/issues/35526) | 10/30 | E | screenshot-only generic error |
| [#35527](https://github.com/openai/codex/issues/35527) | 29/30 | S | benchmark platform-encoding bug |
| [#35528](https://github.com/openai/codex/issues/35528) | 17/30 | D | research paper as umbrella ticket |
| [#35529](https://github.com/openai/codex/issues/35529) | 28/30 | A | excellent small UI report |
| [#35531](https://github.com/openai/codex/issues/35531) | 16/30 | D | real symptom, little diagnosis |
| [#35532](https://github.com/openai/codex/issues/35532) | 26/30 | B | strong persisted-state bug |
| [#35533](https://github.com/openai/codex/issues/35533) | 17/30 | D | deep internal recovery design |
| [#35534](https://github.com/openai/codex/issues/35534) | 29/30 | S | benchmark value-validation bug |
| [#35535](https://github.com/openai/codex/issues/35535) | 15/30 | D | three tickets wearing one title |
| [#35536](https://github.com/openai/codex/issues/35536) | 27/30 | A | strong config-to-wire report |
| [#35538](https://github.com/openai/codex/issues/35538) | 17/30 | D | clear pain, weak measurements |
| [#35539](https://github.com/openai/codex/issues/35539) | 21/30 | C | usable auth symptom |
| [#35540](https://github.com/openai/codex/issues/35540) | 26/30 | B | focused lifecycle contract |
| [#35541](https://github.com/openai/codex/issues/35541) | 25/30 | B | strong precursor report |
| [#35542](https://github.com/openai/codex/issues/35542) | 18/30 | D | careful but overbuilt proposal |
| [#35543](https://github.com/openai/codex/issues/35543) | 26/30 | B | strong device-UI bug |
| [#35544](https://github.com/openai/codex/issues/35544) | 26/30 | B | strong serialization report |
| [#35545](https://github.com/openai/codex/issues/35545) | 29/30 | S | benchmark environment report |
| [#35546](https://github.com/openai/codex/issues/35546) | 14/30 | E | diagnostic landfill |

## Block 006

Detailed observations: [`issue-quality-catalog-pass-002-006.md`](issue-quality-catalog-pass-002-006.md)

S 5 | A 5 | B 5 | C 2 | D 2 | E 1

| Issue | Score | Band | Catalogue tag |
|---|---:|:---:|---|
| [#35502](https://github.com/openai/codex/issues/35502) | 25/30 | B | concise visual workflow request |
| [#35503](https://github.com/openai/codex/issues/35503) | 28/30 | A | benchmark source-aware feature request |
| [#35504](https://github.com/openai/codex/issues/35504) | 22/30 | C | well-scoped ambition, large delivery |
| [#35505](https://github.com/openai/codex/issues/35505) | 29/30 | S | benchmark platform forensic |
| [#35506](https://github.com/openai/codex/issues/35506) | 27/30 | A | strong model-boundary control |
| [#35507](https://github.com/openai/codex/issues/35507) | 17/30 | D | real invariant, avoidable hostility |
| [#35508](https://github.com/openai/codex/issues/35508) | 22/30 | C | good experiential reproduction |
| [#35509](https://github.com/openai/codex/issues/35509) | 27/30 | A | excellent small feature request |
| [#35510](https://github.com/openai/codex/issues/35510) | 29/30 | S | benchmark key-injection report |
| [#35511](https://github.com/openai/codex/issues/35511) | 27/30 | A | strong bug plus fix |
| [#35512](https://github.com/openai/codex/issues/35512) | 15/30 | D | product vision, not a ticket |
| [#35513](https://github.com/openai/codex/issues/35513) | 17/30 | D | disciplined but low-signal singleton |
| [#35514](https://github.com/openai/codex/issues/35514) | 28/30 | A | strong destructive-config report |
| [#35515](https://github.com/openai/codex/issues/35515) | 21/30 | C | strong symptom, sparse evidence |
| [#35516](https://github.com/openai/codex/issues/35516) | 16/30 | D | policy concern without incident detail |
| [#35517](https://github.com/openai/codex/issues/35517) | 29/30 | S | benchmark event-order report |
| [#35518](https://github.com/openai/codex/issues/35518) | 21/30 | C | clear auth-state symptom |
| [#35519](https://github.com/openai/codex/issues/35519) | 25/30 | B | focused configuration UI bug |
| [#35520](https://github.com/openai/codex/issues/35520) | 21/30 | C | useful trigger, weak forensics |
| [#35521](https://github.com/openai/codex/issues/35521) | 27/30 | A | strong enterprise Windows report |
