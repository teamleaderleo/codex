# Patch 1 testing and validation archaeology

Status: internal exhaustive engineering record. This file is not part of the upstream candidate and is not, by itself, approved public copy.

Date reconstructed: 2026-07-26

Owner: Agent 2 testing, validation, and CI archaeology

## 1. Scope and evidentiary standard

This document reconstructs how Patch 1 moved from an executable negative reproduction to a five-case acceptance contract, then through repository-convention review, test-only polish, repository-native focused validation, and a matched candidate/base project-suite differential.

The reconstruction follows four evidence rules:

1. **Immutable code and commit evidence takes priority.** Behaviour attributed to a test is cited to the commit or pinned file that contains it.
2. **Validation receipts describe commands actually reported as run.** They do not imply wider coverage than their filters selected.
3. **Environment failures are not silently rewritten as code failures.** Linker kills, missing binaries, sandbox aborts, timeouts, missing tools, and command-shape errors are classified separately.
4. **Absence of an observed failure is not proof of impossibility.** Repetition counts bound the flake evidence; they do not prove a race can never occur.

The deep-dive workspace itself asks for an honest record of evidence, discarded paths, limitations, and uncertainty rather than a retroactively clean story.[^deep-dive-readme]

## 2. Commit, branch, and platform map

| Role | Branch or ref | Commit | Meaning |
|---|---|---:|---|
| Investigation baseline | historical upstream | `20dafe201d91d4405eef05ecd1db0257f13a9ac8` | Base used for the early investigation implementation and first runtime report. |
| Negative reproduction | `research/code-mode-live-session-test` | `7298dcf44f61164ffc25b8bdf5f136281caeb9f5` | One passing test that demonstrates the hidden-live-session behaviour before the fix. |
| Acceptance lineage | `research/code-mode-live-session-acceptance` | `528171c72c06d8be3471752322b7755a1eac3ac8` → `0ba57a73ea5895883a21aeb88e923d75a74ed38d` → `89ffd99b81e872e3a961767e67fb8ec410df7eae` | Five behavioural cases, creator-cell correction, and large-output truncation correction. |
| Selected upstream base | exact upstream ref | `61a44880a85d2fd0d8770908dea5733495e571c8` | Base for the final clean candidate and matched project-suite comparison. |
| Clean production candidate before test polish | `fix/code-mode-live-session-summary-clean` | `3778e1fae6e7e3d885252282a7c5ce67e06730ff` | Production implementation plus then-current tests, before roundtable test-only revision. |
| Original aggregate-suite test polish | `review/code-mode-roundtable-test-polish` | `cc01596b75abb38335ecdfe07688f155b0dd15a9` | Standalone target removed; five cases moved into the aggregate suite; cleanup and deterministic-exit fixes. |
| Supplemental/final test polish | same branch, later consolidated | `760216784efaee1ba6a3b1250349f31d5f91c7ca` | Direct manager-query unit test, contract-level large-output assertion, and repository-native compatibility evidence. |
| Final clean candidate | `fix/code-mode-live-session-summary-clean` | `760216784efaee1ba6a3b1250349f31d5f91c7ca` | Three commits over selected upstream: production implementation followed by two test-only commits. |

The locally executed negative, focused, acceptance, and compatibility work ran on **Linux aarch64 under Lima**. The matched broad project-suite runs used **GitHub `ubuntu-latest`**, the repository's `.github/actions/setup-ci` action, `cargo-nextest 0.9.114`, `CARGO_BUILD_JOBS=4`, `CARGO_INCREMENTAL=1`, `CARGO_PROFILE_TEST_DEBUG=0`, and `RUST_BACKTRACE=1`.[^negative-handoff][^project-inventory]

The test-polish runner installed user-local prerequisites when they were absent. The retained output recorded `just 1.57.0`, DotSlash `0.5.9`, and `uv 0.11.32`; `cargo-nextest` was added later so the final focused rerun could use `just test`. These installations were runner preparation, not Patch 1 source changes.

## 3. How the negative reproduction was built

### 3.1 The test deliberately proved the bad state

The negative proof is commit `7298dcf44f61164ffc25b8bdf5f136281caeb9f5`, titled `test(core): reproduce hidden code-mode exec sessions`.[^negative-commit]

The test name was:

```text
code_mode_completion_does_not_surface_discarded_live_exec_sessions
```

Its JavaScript cell launched two nested unified-exec commands concurrently:

```javascript
const outputs = (await Promise.all([
  tools.exec_command({ cmd: "printf orphan-a; sleep 60", yield_time_ms: 250 }),
  tools.exec_command({ cmd: "printf orphan-b; sleep 60", yield_time_ms: 250 }),
])).map(({ output }) => output);
text(outputs.join("|"));
```

The important construction choices were:

- Both commands printed a stable marker and then remained alive for 60 seconds.
- `yield_time_ms: 250` forced each nested command to return a yielded/background-session response rather than wait for natural completion.
- JavaScript immediately mapped each result to `output`, deliberately discarding both copied `session_id` values.
- The cell itself then completed normally and emitted `orphan-a|orphan-b`.

After the turn, the Rust test queried `CodexThread::list_background_terminals()` and required two distinct registered terminals. It then inspected the outer code-mode tool result and required:

- a terminal `Script completed` status;
- the emitted `orphan-a|orphan-b` text;
- no session information in the status header.

That is why the negative test passed on the unfixed behaviour: it asserted the precise contradiction being investigated. The nested processes remained manager-owned and live, but the model-visible terminal result did not expose their control handles.[^negative-commit]

### 3.2 The negative proof was preserved rather than rewritten

The exact command retained in the Agent 2 handoff was:

```sh
RUST_MIN_STACK=8388608 \
CARGO_BUILD_JOBS=4 \
CARGO_INCREMENTAL=1 \
CARGO_PROFILE_TEST_DEBUG=0 \
CARGO_TARGET_DIR=/home/lima/.cache/codex-orphan-target \
RUST_BACKTRACE=1 \
cargo test -p codex-core \
  --test code_mode_orphan_sessions \
  code_mode_completion_does_not_surface_discarded_live_exec_sessions \
  -- --exact --nocapture
```

Result:

```text
test code_mode_completion_does_not_surface_discarded_live_exec_sessions ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
```

The preserved handoff explicitly says not to rewrite this assertion in place. Keeping the negative proof immutable provides an executable before-state rather than forcing reviewers to infer the bug from an acceptance test that only passes after the implementation exists.[^negative-handoff]

### 3.3 What the negative proof established—and did not

It established, on one Linux aarch64 Lima environment, that:

1. two nested commands could yield and stay live;
2. JavaScript could discard the copied session IDs;
3. the session manager still listed both terminals;
4. the outer cell could say `Script completed` without surfacing them;
5. cleanup could terminate all retained terminals after the assertion.

It did **not** establish:

- a literal memory leak;
- that every code-mode nested process is lost;
- that processes should be auto-terminated;
- cross-turn dispatch behaviour;
- macOS, Windows, remote-host, or complete product-surface behaviour;
- severity beyond the demonstrated visibility and lifecycle-control hazard.

## 4. How the five-case acceptance contract was built

The acceptance branch was based on the negative proof. Its lineage is recorded as:

- initial acceptance: `528171c72c06d8be3471752322b7755a1eac3ac8`;
- contract and two-cell correction: `0ba57a73ea5895883a21aeb88e923d75a74ed38d`;
- truncation assertion correction: `89ffd99b81e872e3a961767e67fb8ec410df7eae`.[^coordination]

The branch head contained five tests in `codex-rs/core/tests/code_mode_orphan_sessions.rs` before the aggregate-suite move.[^acceptance-file]

### 4.1 `code_mode_completion_surfaces_discarded_live_exec_sessions`

This inverted the negative proof into the primary acceptance contract. It retained the same two yielded commands and discarded JavaScript session IDs, but obtained the authoritative expected IDs from `list_background_terminals()`.

The test parsed those IDs as integers, sorted them numerically, checked they were distinct, and required the terminal status summary to contain every real ID exactly once and in numeric order. It did not hard-code sample IDs.[^acceptance-file]

This case covered:

- visibility of multiple surviving nested sessions;
- use of manager state rather than JavaScript return values;
- deterministic numeric ordering;
- preservation of emitted cell output.

### 4.2 `code_mode_completion_reports_only_surviving_nested_session`

The first form started:

```javascript
tools.exec_command({ cmd: "printf short; sleep 1", yield_time_ms: 250 })
tools.exec_command({ cmd: "printf survivor; sleep 60", yield_time_ms: 250 })
```

and then ran a separate two-second sleep before completing the cell. The expected terminal list contained only the long-lived survivor.[^acceptance-file]

The behavioural contract was correct: exited sessions must not appear merely because they were created by the completing cell. The mechanism was later rejected as timing-sensitive; section 8 explains the deterministic replacement.

### 4.3 `large_emitted_output_does_not_truncate_live_session_warning`

This case started one yielded background command and then emitted 65,536 `x` characters:

```javascript
await tools.exec_command({ cmd: "printf large; sleep 60", yield_time_ms: 250 });
text("x".repeat(65536));
```

The contract was not that all 65,536 characters survive. Code-mode output truncation is allowed. The contract was that the terminal status remains a separately represented header, still contains the live-session warning, and is not displaced by emitted-output truncation.[^acceptance-file]

An early assertion required the emitted item to start with a fixed run of `x` characters. That failed against a legitimate truncation representation. Commit `89ffd99...` corrected it to require a non-empty separate representation instead of one exact excerpt form.[^truncation-correction]

A later external review found one more over-specification—exactly two content items—which was removed in the supplemental commit; section 11 covers that change.

### 4.4 `yielded_cell_response_does_not_include_completion_session_warning`

This case started a yielded nested command and then left the outer cell itself pending forever:

```javascript
await tools.exec_command({ cmd: "sleep 60", yield_time_ms: 250 });
await new Promise(() => {});
```

The outer status therefore had to remain the ordinary:

```text
Script running with cell ID ...
```

It must not use the completion-only background-session summary path. This protected the policy boundary that Patch 1 reports surviving sessions only for terminal outcomes; ordinary `Yielded` remains neutral.[^acceptance-yielded]

### 4.5 `code_mode_completion_reports_only_sessions_created_by_current_cell`

The fifth case ran two completed cells in the same Codex session. Cell A left one live process. Cell B left a second live process. The completion output for cell B had to include only B's process ID and exclude A's still-live ID.[^acceptance-yielded]

This case was essential because “list all live processes” would have made the symptom visible while violating ownership isolation. The accepted implementation contract was exact creator-cell attribution plus current liveness, not a global terminal dump.

### 4.6 Cleanup in the acceptance lineage

Every case attempted panic-safe teardown by:

1. wrapping assertions in `AssertUnwindSafe(...).catch_unwind()`;
2. listing all registered background terminals;
3. parsing each process ID;
4. calling `terminate_background_terminal` for each;
5. requiring the final terminal list to be empty;
6. resuming an original assertion panic after cleanup.

That structure was valuable, but its placement was incomplete: the helper `run_code_mode_turn` submitted the turn before the guarded assertion future began. A submission error after creating a background process could therefore return through `?` and bypass cleanup. That gap drove the later preparation/submission split.[^roundtable-agent2]

## 5. Initial implementation-era validation

Before the final aggregate-suite polish, the published implementation-era runtime report recorded this Linux aarch64 Lima evidence on investigation head `73e5b9fc28de0815975fad3c3d70a6a0b38399b1`:

```text
cargo check -p codex-core --tests                         passed
focused code-mode library tests                          3 passed; 0 failed
focused unified-exec library tests                       3 passed; 0 failed
code_mode_orphan_sessions acceptance target              5 passed; 0 failed; 0 ignored
acceptance harness execution                             17.12s
skips/flakes                                             none
```

The three code-mode unit tests were:

```text
terminal_cell_id_excludes_yielded_responses
terminal_script_status_surfaces_sorted_live_background_sessions
yielded_script_status_does_not_surface_background_sessions
```

The three existing unified-exec tests were:

```text
unified_exec_persists_across_requests
multi_unified_exec_sessions
pruning_does_not_evict_live_process_while_exited_process_is_finalizing
```

The acceptance command was:

```sh
cargo test -p codex-core \
  --test code_mode_orphan_sessions \
  -- --test-threads=1 --nocapture
```

and all five named cases passed in 17.12 seconds.[^runtime-report]

This evidence remains useful, but it is not the final repository-native validation record because:

- the integration target was later moved;
- the test code itself changed;
- direct `cargo test` was superseded by the repository's `just test` recipe for the final focused rerun;
- the broad project suite was not green.

## 6. Why the standalone integration target conflicted with repository convention

### 6.1 The exact repository comments

The repository's `codex-rs/core/tests/all.rs` says:

> Single integration test binary that aggregates all test modules.

and then declares `mod suite;`.[^all-comment]

The corresponding `codex-rs/core/tests/suite/mod.rs` begins:

> Aggregates all former standalone integration tests as modules.

and already registers `mod code_mode;`.[^suite-comment]

Those are not inferred style preferences; they are explicit repository comments describing the intended harness shape.

### 6.2 Why a root-level file created a conflicting target

Under Cargo's integration-test layout, a Rust file directly under `tests/` is compiled as its own integration-test binary. Therefore:

```text
codex-rs/core/tests/code_mode_orphan_sessions.rs
```

created a second binary instead of joining the documented `all` binary.

The problem was not that standalone targets are impossible. The problem was local consistency and cost:

- the crate explicitly documents one aggregate binary;
- the aggregate suite already has a `code_mode` module;
- the new file was roughly 521 lines;
- compiling another integration target adds build/link work;
- the standalone target cannot naturally reuse private parent-module helpers;
- focused nextest filtering already supports running a child module inside the aggregate binary.

The accepted shape became:

```text
codex-rs/core/tests/suite/code_mode.rs
codex-rs/core/tests/suite/code_mode/orphan_sessions.rs
```

with `mod orphan_sessions;` registered from the existing `code_mode.rs` module.[^final-code-mode]

### 6.3 Why duplicated helpers were rejected

The standalone file redefined:

- `custom_tool_output_items`;
- `text_item`;
- code-mode test builder/configuration;
- SSE response mounting and turn submission.

The existing aggregate `code_mode.rs` already had equivalent response extraction and turn setup. Duplication was rejected for practical reasons:

1. Changes to output serialisation would require two helper implementations to remain aligned.
2. Model/config setup could drift between old and new code-mode tests.
3. Duplicate helpers obscured which behaviour was under test and which code was harness boilerplate.
4. The extra target paid compile/link cost for code already present in the aggregate binary.
5. Reusing parent helpers made the child module review smaller and tied it to established suite semantics.

The final parent module exposes private helpers to its child through normal Rust module visibility. It registers the child at line 75, retains `custom_tool_output_items` and `text_item`, and adds preparation helpers that mount the mocks without submitting the turn.[^final-code-mode]

## 7. Cleanup protection: what changed and why submission moved inside it

### 7.1 The original gap

In the standalone acceptance file, `run_code_mode_turn` did all of the following:

1. mount the first SSE response;
2. mount the follow-up response;
3. build `TestCodex`;
4. call `test.submit_turn(prompt).await?`;
5. return the test and response mock.

Only after that helper returned did each test enter `catch_unwind`.[^acceptance-file]

If `submit_turn` created one or more nested terminals and then returned an error, the test exited at `?` before installing its cleanup path. That is exactly the kind of failure path a background-process test must defend against.

### 7.2 The preparation/submission split

The aggregate parent gained:

```text
prepare_code_mode_turn
prepare_code_mode_turn_with_builder
```

These build the test and mount the response mocks but do not submit a turn. Existing callers that want the old convenience still use `run_code_mode_turn_with_builder`, which now delegates to preparation and then submits.[^final-code-mode]

The orphan-session child does this instead:

1. prepare `TestCodex` and mocks outside the guard, while no nested process exists;
2. enter `run_with_background_terminal_cleanup`;
3. call every process-creating `submit_turn` inside the guarded future;
4. perform assertions;
5. always run terminal cleanup on success, returned error, or panic.

The two-cell attribution test places both submissions inside the same cleanup-protected future.

### 7.3 Panic and error semantics

The final cleanup path preserves the most useful failure:

- On success or an ordinary returned error, cleanup runs and a cleanup failure is surfaced.
- On panic, cleanup still runs.
- If cleanup also fails during a panic, that cleanup error is logged but does not replace the original assertion panic.
- The original panic is resumed.

This is stronger than a simple “cleanup at the bottom” pattern because Rust `?` returns and assertion panics both cross the protected boundary.

It is still a test-local helper, not a general reusable guard in `core_test_support`. The roundtable explicitly deferred that broader refactor to avoid expanding Patch 1.[^roundtable-agent2]

## 8. Why the fixed sleep race was inadequate

The first one-survivor test relied on:

```text
short process: sleep 1
cell delay:    sleep 2
```

That asserted time passage, not the state transition the test cared about.

It was inadequate because:

- a loaded or paused runner can delay scheduling;
- process startup times and timer wake-ups are not guaranteed to preserve the intended one-second margin;
- a “long enough” sleep slows every successful run;
- increasing the delay reduces but never removes the race;
- failure output cannot distinguish “short process still alive” from unrelated scheduler delay;
- the cell can complete without an explicit handshake proving the short process is gone.

The review therefore required bounded polling or another deterministic completion mechanism rather than a larger sleep.[^roundtable-agent2]

## 9. How the PID/filesystem handshake works

The final one-survivor case uses a temporary directory and two paths:

```text
short.pid
release
```

### 9.1 Short process

The short shell command:

1. writes its actual shell PID (`$$`) to `short.pid`;
2. prints `short`;
3. loops until the `release` file exists.

Conceptually:

```sh
printf '%s' "$$" > short.pid
printf short
while [ ! -f release ]; do sleep 0.05; done
```

This process yields and remains registered, but its exit is now controlled by an explicit file transition.

### 9.2 Survivor process

A second nested command prints `survivor` and sleeps for 60 seconds. It is intentionally still live at cell completion.

### 9.3 Foreground completion command

A third nested `exec_command`:

1. creates the `release` file;
2. reads the recorded short-process PID;
3. polls `kill -0 PID` every 50 milliseconds;
4. prints `exited` and succeeds once the process no longer exists;
5. prints `timeout` and fails after 100 iterations, a five-second upper bound.

The JavaScript cell refuses to continue unless that command's output is exactly `exited`. Only then does it emit `short|survivor` and complete.

This handshake has three useful properties:

- **causal:** the cell completion is downstream of release and observed process exit;
- **bounded:** a broken transition fails within five seconds;
- **diagnosable:** timeout is an explicit state failure, not an arbitrary wall-clock assertion.

The long-lived command is then the only terminal expected in manager state and the only ID expected in the summary.[^original-polish-receipt]

## 10. Why numeric-token scanning was replaced by the named warning

The original yielded-neutrality helper split the whole status text on non-digits and treated every numeric token as a possible process ID.

That was unsafe because a yielded status necessarily contains a numeric **cell ID**:

```text
Script running with cell ID 1234
```

If a nested process ID happened to equal that cell ID, the test could report a false disclosure even though the completion-only session warning was absent. The assertion was testing incidental numeric coincidence rather than the user-visible contract.[^roundtable-agent2]

The final yielded case directly checks that the header does not contain:

```text
Background sessions still running:
```

That is the named completion-only behaviour Patch 1 adds. The direct check is both clearer and less coupled to unrelated numbers such as cell IDs or wall times.[^original-polish-receipt]

Numeric-token parsing remains appropriate in the terminal-summary cases where the test must prove specific process IDs appear exactly once and in sorted order. It was removed only from the yielded-absence contract.

## 11. Why the large-output test stopped requiring exactly two content items

The original and first-polished forms required:

```rust
assert_eq!(items.len(), 2)
```

That encoded one serialisation shape:

1. status header;
2. emitted text.

The actual product contract was narrower:

- the completion status must be a separate text item;
- that status must retain the live-session warning and correct IDs;
- some separate non-empty emitted-output representation must remain after truncation.

There can be legitimate reasons for more than one emitted-output item or for a future serialisation adjustment that does not violate those properties. Exact cardinality would create maintenance churn without detecting a user-visible regression.

The supplemental commit now:

1. searches the content items for a text item beginning with `Script completed\n`;
2. requires that item to contain `Background sessions still running:`;
3. validates the live ID summary;
4. requires at least one other non-empty text item.

It no longer pins the complete content-item count or the exact truncation excerpt.[^supplement-commit][^supplement-receipt]

This change does **not** weaken the warning-placement assertion. It makes the test stricter about the named header contract while looser only about unrelated serialization cardinality.

## 12. Why a direct manager-query unit test was added

The five acceptance cases exercise the full path, but the exact filtering behaviour of:

```text
live_process_ids_created_by_cell
```

was initially covered indirectly through shell processes, code-mode execution, response mocks, and integration assertions.

Agent 3's supplemental review requested a network-independent unit test using existing unified-exec fixtures. The final unit test is:

```text
live_process_ids_created_by_cell_filters_exited_and_sorts
```

It inserts five deterministic entries into the test process store:

| Process ID | Creator | Exited? | Expected? |
|---:|---|---|---|
| 3003 | target cell | no | yes |
| 1001 | target cell | no | yes |
| 2002 | other cell | no | no |
| 1000 | `None` | no | no |
| 1500 | target cell | yes | no |

The exact expected result is:

```text
[1001, 3003]
```

This single query proves exact-cell inclusion, other-cell exclusion, unattributed-entry exclusion, exited-process exclusion, and numeric sorting without a network skip or shell timing dependency.[^supplement-commit]

Why this mattered:

- it isolates the manager's policy from formatter and integration harness behaviour;
- failures point directly at query semantics;
- it covers `creator_cell_id: None`, which is awkward to produce through the code-mode acceptance path;
- it gives deterministic sorting evidence using deliberately out-of-order insertion;
- it does not require changing production visibility or adding a public test API.

## 13. Candidate/base compatibility repetitions

### 13.1 Tests selected

The external-review triage identified two existing aggregate code-mode tests as potentially exposed to an optional point-in-time background-session header:

```text
code_mode_can_run_multiple_yielded_sessions
code_mode_wait_can_terminate_and_continue
```

The concern was not a known failure. It was a race hypothesis: terminal completion might observe a still-live nested session at one scheduling point and no session at another, potentially making an old exact header expectation candidate-only flaky.

### 13.2 Repetition design

The final command was:

```sh
just test -p codex-core --test all \
  -E 'test(/suite::code_mode::(code_mode_can_run_multiple_yielded_sessions|code_mode_wait_can_terminate_and_continue)$/)' \
  --no-capture --no-tests=fail
```

It was run:

- ten times at exact upstream base `61a44880a85d2fd0d8770908dea5733495e571c8`;
- ten times at candidate `760216784efaee1ba6a3b1250349f31d5f91c7ca`;
- on the same Linux aarch64 Lima runner;
- with the same target cache, `/home/lima/.cache/codex-orphan-target`.[^supplement-receipt]

Each repetition selected two tests, yielding:

```text
upstream: 10 repetitions × 2 tests = 20 passed; 0 failed
candidate: 10 repetitions × 2 tests = 20 passed; 0 failed
```

### 13.3 Why ten repetitions

Ten repetitions were a proportionate focused stress sample:

- more informative than one pass;
- inexpensive compared with another broad project run;
- enough to expose a frequent candidate-only scheduling race;
- symmetrical across candidate and base;
- controlled by one runner and cache for the focused comparison.

Ten is not a statistical proof that the race probability is zero. The supported interpretation is:

> No candidate-only optional-header race was observed in 20 selected test executions per ref under one shared focused runner/cache.

Because no differential failure appeared, no compatibility expectation was loosened. The review instruction was conditional: modify only affected expectations **if** a candidate-only race appeared. It did not.[^supplement-receipt]

## 14. Why direct `cargo test` was superseded by repository-native `just test`

### 14.1 Earlier direct commands were real but incomplete as final convention evidence

The early runtime work used direct `cargo test` because the VM did not initially have `cargo-nextest`. Correctly scoped direct commands such as:

```sh
cargo test -p codex-core --lib terminal_cell_id_excludes_yielded_responses
```

and the standalone acceptance target did run and pass. They remain valid historical evidence for those trees.[^runtime-report]

However, the repository `justfile` says:

```text
# Run nextest with --no-fail-fast so all tests are run.
#
# Run `cargo install --locked cargo-nextest` if you don't have it installed.
# Prefer this for routine local runs.
```

and defines:

```make
RUST_MIN_STACK=8388608 NEXTEST_PROFILE=local cargo nextest run --no-fail-fast "$@"
```

for `just test`.[^justfile]

The final evidence therefore had to use the repository wrapper rather than continue treating a missing local tool as a reason to bypass it. The supplemental runner installed `cargo-nextest` and reran all affected focused tests through `just test`.

### 14.2 Exact successful final focused commands

Four unit tests:

```sh
just test -p codex-core --lib \
  -E 'test(/(live_process_ids_created_by_cell_filters_exited_and_sorts|terminal_cell_id_excludes_yielded_responses|terminal_script_status_surfaces_sorted_live_background_sessions|yielded_script_status_does_not_surface_background_sessions)$/)' \
  --no-capture --no-tests=fail
```

Five aggregate acceptance tests:

```sh
just test -p codex-core --test all \
  -E 'test(/suite::code_mode::orphan_sessions::/)' \
  --no-capture --no-tests=fail
```

Two repeated compatibility tests:

```sh
just test -p codex-core --test all \
  -E 'test(/suite::code_mode::(code_mode_can_run_multiple_yielded_sessions|code_mode_wait_can_terminate_and_continue)$/)' \
  --no-capture --no-tests=fail
```

The `--no-tests=fail` option is important archaeology: a typo or unsupported filter could not produce a false “pass” by selecting zero tests.[^supplement-receipt]

## 15. What the repository-native tools establish

### 15.1 `just test`

The root `justfile` sets the working directory to `codex-rs`, then the Unix `test` recipe sets:

```text
RUST_MIN_STACK=8388608
NEXTEST_PROFILE=local
```

and runs:

```text
cargo nextest run --no-fail-fast
```

with the supplied arguments.[^justfile]

For the focused filters used here, a successful `just test` establishes that:

- the selected test binaries compiled;
- nextest discovered the selected tests;
- `--no-tests=fail` did not detect an empty selection;
- every selected test completed successfully under the local nextest profile;
- `--no-fail-fast` would have allowed other selected tests to continue after a failure.

It does **not** establish that:

- unselected tests passed;
- the whole `codex-core` project passed;
- the workspace passed;
- tests passed on macOS, Windows, x86_64, remote exec, or every sandbox mode;
- a flake can never occur;
- an ignored or environment-skipped path executed;
- performance, leak freedom, or production deployment behaviour is proven.

### 15.2 Cargo nextest

Nextest is the executor selected by repository convention. In the broad matched run, the local profile retried failing tests once; the failure inventory records 96 second attempts, including one flaky pass, persistent failures, and a persistent timeout.[^project-inventory]

Nextest improves observability and test-process isolation, but it does not change test semantics into a proof of all product behaviour. A nextest summary must still be interpreted with:

- the exact ref;
- exact filter;
- profile and retry settings;
- skips and ignores;
- runner environment;
- helper-binary availability;
- sandbox support;
- timeouts and flaky passes.

### 15.3 `just fmt`

The `fmt` recipe calls `scripts/format.py`.[^justfile]

That script runs formatter groups for:

- the Justfile (`just --unstable --fmt`);
- Rust (`cargo fmt -- --config imports_granularity=Item`);
- Bazel/Starlark through DotSlash/buildifier;
- Python SDK fixable Ruff rewrites and formatting through `uv`;
- Python scripts formatting through `uv`.[^format-script]

A passing `just fmt`, combined with the runner's changed-path guard, establishes that the repository formatter completed and the approved files were left in formatter-accepted form without unapproved path changes.

It does **not** establish:

- semantic correctness;
- test success;
- a complete lint pass;
- that all possible generated files or non-formatter style rules were checked;
- that no formatter would behave differently on another tool version.

The format script itself notes that Ruff's `--fix --fix-only` is a fixable-rewrite pass, not a full lint gate.[^format-script]

### 15.4 `just fix -p codex-core`

The recipe expands to:

```text
cargo clippy --fix --tests --allow-dirty -p codex-core
```

because `fix *args` forwards its arguments.[^justfile]

A successful run establishes that Clippy's test-inclusive analysis completed for the selected package without an error that prevented the fix command, and that any machine-applicable fixes were applied. The changed-path guard then verifies those fixes did not escape the approved test scope.

It does **not** establish:

- a workspace-wide Clippy pass;
- zero warnings under every feature/target configuration;
- runtime test success;
- absence of non-machine-applicable lint concerns;
- API or architectural approval.

### 15.5 `cargo check -p codex-core --tests`

The earlier compile check established that `codex-core` test targets type-checked and compiled through `cargo check` on that tree. It did not link or execute every test binary and did not replace runtime tests.[^runtime-report]

### 15.6 `git status` and `git diff --check`

The final commands included:

```sh
git status --short --untracked-files=all
git diff --check 3778e1fae6e7e3d885252282a7c5ce67e06730ff 760216784efaee1ba6a3b1250349f31d5f91c7ca
```

They establish a clean recorded worktree and absence of Git-detectable whitespace errors in the compared diff. They do not establish behavioural correctness.[^supplement-receipt]

## 16. Broad red-on-both-refs differential

### 16.1 Exact broad command and environment

The project-level command was run on both the pre-polish clean candidate and exact upstream base:

```sh
just test -p codex-core
```

Environment:

```text
GitHub ubuntu-latest
repository .github/actions/setup-ci
cargo-nextest 0.9.114
CARGO_BUILD_JOBS=4
CARGO_INCREMENTAL=1
CARGO_PROFILE_TEST_DEBUG=0
RUST_BACKTRACE=1
```

The two complete broad runs used equivalent runner images and setup, but separate ephemeral GitHub VMs and fresh target directories. Only the later two-test focused differential used one runner and one shared Cargo target cache.[^project-inventory]

### 16.2 Results

Candidate `3778e1fa...`:

```text
3,110 run
3,015 passed, including one flaky pass
94 failed
1 timed out
9 skipped
```

Exact upstream `61a44880...`:

```text
3,102 run
3,007 passed
94 failed
1 timed out
9 skipped
```

The candidate had eight additional passing tests: the three new Patch 1 unit tests and five acceptance tests.[^project-inventory]

### 16.3 Failure matching and classification

The inventory found:

- 93 failed-test names shared;
- the same timed-out test shared;
- one candidate-only broad-run failure:
  `suite::unified_exec::unified_exec_formats_large_output_summary`;
- one upstream-only broad-run failure:
  `suite::compact_resume_fork::snapshot_rollback_followup_turn_trims_context_updates`.

Each differing test then passed three of three times on the candidate and three of three times on upstream in one shared focused runner/cache. Thus each passed six focused executions total and was classified as a concurrency or run-order flake rather than a Patch 1 regression.[^project-inventory]

Final failure-category totals were:

```text
environment or missing dependency     53 shared outcomes
sandbox or runner limitation          16 candidate outcomes, including timeout/flake
known or unrelated assertion          26 shared outcomes
potentially related to Patch 1         0
unclassified                           0
```

The environment category included missing `codex` and `test_stdio_server` helper binaries. Sandbox/runner failures included SIGABRT/SIG6 outcomes and timeouts. Existing code-mode failures caused by the missing `test_stdio_server` reproduced on upstream.[^project-inventory]

### 16.4 Supported classification

The evidence supports:

> **Pass with baseline-red caveat:** the broad `codex-core` project suite was not green on either ref; 93 failures and the timeout were shared; the two differing failures did not persist in controlled focused reruns; all Patch 1-focused tests passed; no candidate failure remained classified as potentially related or unclassified.

It does not support:

- “the broad suite passed”;
- “CI is green”;
- “all regressions are impossible”;
- “candidate and base were run on the same full-run machine/cache”;
- “the complete workspace suite passed.”

The complete workspace suite was not run.[^project-inventory]

## 17. Failed or discarded approaches that changed the final process

This section includes approaches that materially changed test design, command selection, or validation wording. Some launcher stderr is preserved only in the coordinating conversation and user-retained logs; the repository receipts preserve the scrubbed categories and final commands. No failed launcher committed or pushed code.

### 17.1 Over-specific large-output prefix

**Approach:** require the truncated emitted item to begin with a fixed `xxxxxxxx` prefix.

**Failure:** a valid truncation representation did not preserve that exact prefix shape.

**Change:** require non-empty separate representation; later remove exact item cardinality too.

**Evidence:** commit `89ffd99...`.[^truncation-correction]

### 17.2 Plain filtered `cargo test` without `--lib`

**Approach:**

```sh
cargo test -p codex-core <test-name>
```

**Failure:** Cargo widened the build to unrelated integration binaries such as `responses_headers` and `all`; concurrent linkers were killed by signal 9.

**Change:** use explicit `--lib` for focused library fallback commands, then later use exact nextest expressions through `just test`.

**Classification:** runner/resource and command-selection failure, not a failed Patch 1 assertion.[^runtime-report]

### 17.3 Partial formatting fallback

**Approach:** use `cargo fmt --all` because `just`, DotSlash, and `uv` were absent.

**Result:** sufficient to Rust-format the then-Rust-only implementation tree, but not equivalent to repository-native `just fmt`.

**Change:** record the deviation honestly; later install formatter prerequisites and require full `just fmt` for the final test-polish commits.[^runtime-report]

### 17.4 Standalone integration binary

**Approach:** keep `tests/code_mode_orphan_sessions.rs` as a named target.

**Problem:** contradicted the explicit single aggregate binary convention, duplicated helpers, and added build/link surface.

**Change:** move the five cases to `tests/suite/code_mode/orphan_sessions.rs` and register from `code_mode.rs`.[^roundtable-agent2]

### 17.5 Cleanup after submission

**Approach:** have `run_code_mode_turn` submit before entering `catch_unwind`.

**Problem:** submission could create terminals and return an error before cleanup protection existed.

**Change:** split preparation from submission and put every process-creating submission inside the guarded future.[^original-polish-receipt]

### 17.6 Fixed one-second/two-second race

**Approach:** let one process sleep one second and delay cell completion two seconds.

**Problem:** tested elapsed time rather than confirmed exit; susceptible to scheduling/load variance.

**Change:** bounded PID/filesystem handshake.[^roundtable-agent2]

### 17.7 Numeric-token absence scan

**Approach:** treat all digits in a yielded header as possible process IDs.

**Problem:** yielded headers contain numeric cell IDs; equal numeric values could false-fail.

**Change:** directly require absence of `Background sessions still running:`.[^roundtable-agent2]

### 17.8 First test-polish launcher required missing `just`

**Approach:** fail if repository-native tools were absent.

**Failure:** the Lima image did not have `just`.

**Change:** bootstrap user-local `just`, DotSlash, and `uv` before editing or validation. The first attempt stopped before source edits.[^original-polish-receipt]

### 17.9 Compact untracked-directory status

**Approach:** compare expected individual paths against default `git status --short`.

**Failure:** Git collapsed the new untracked child file to:

```text
?? codex-rs/core/tests/suite/code_mode/
```

so the scope guard treated a correct edit as unexpected.

**Change:** use `git status --short --untracked-files=all`, enumerate individual untracked files, and add fail-closed recovery for the exact interrupted path set.[^original-polish-receipt]

### 17.10 `assert_eq!` macro ambiguity after `use super::*`

**Approach:** rely on the child glob import while the parent imported `pretty_assertions::assert_eq`.

**Failure:** Rust reported `assert_eq` ambiguous between the imported macro and the standard prelude macro.

**Change:** explicitly import `pretty_assertions::assert_eq` in the child module.[^original-polish-receipt]

### 17.11 Cargo invoked from the wrong directory

**Approach:** run direct `cargo test` from the repository root, which has no root `Cargo.toml`.

**Failure:** Cargo reported it could not find `Cargo.toml` in the checkout root.

**Change:** use `--manifest-path codex-rs/Cargo.toml` for the interim direct commands. The final `just test` recipe avoids this class because the root Justfile sets `working-directory := "codex-rs"`.[^justfile][^original-polish-receipt]

### 17.12 First deterministic-exit attempt used nested `tools.write_stdin`

**Approach:** start a shell blocked on stdin, then call nested `tools.write_stdin` to release it and infer exit from the response.

**Failure:** the code-mode cell returned `Script failed`, so the acceptance assertion saw a failed outer status. Four other acceptance cases passed, isolating the defect to the handshake rather than the module move or cleanup wrapper.

**Change:** use only the already-supported nested `exec_command` path with a PID/file handshake.[^original-polish-receipt]

### 17.13 Direct `cargo test` accepted as final evidence

**Approach:** treat the successful direct unit and aggregate commands at `cc01596` as sufficient final convention evidence.

**Review finding:** repository guidance prefers `just test`/nextest; Agent 3 requested a repository-native rerun.

**Change:** install cargo-nextest and rerun four unit tests, five acceptance tests, and compatibility tests through exact nextest filters.[^agent3-supplement-review]

### 17.14 Supplemental runner assumed cargo-nextest existed

**Approach:** abort if `cargo-nextest` was missing.

**Failure:** the Lima environment did not have it.

**Change:** install `cargo-nextest` user-locally, verify it, and preserve the `just test` route rather than falling back again to direct Cargo.

**Evidence:** final supplemental receipt records that all focused tests used `just test`; the missing-tool stderr is retained in the coordinating transcript, not committed as raw public evidence.[^supplement-receipt]

### 17.15 Optional-header expectation change was conditional and discarded

**Approach considered:** loosen existing compatibility expectations to accept an optional point-in-time background-session line.

**Condition:** only if a candidate-only race appeared.

**Observed result:** 20/20 selected executions passed on each ref; no candidate-only race appeared.

**Change:** none. Existing expectations remained intact.[^supplement-receipt]

## 18. Evidence separated by category

### 18.1 Code-correctness evidence

The strongest Patch 1-specific correctness evidence is:

- immutable negative reproduction passes on the before-state;
- three formatter/status unit tests pass;
- direct manager-query unit test passes;
- all five end-to-end aggregate acceptance cases pass;
- compatibility tests pass 20/20 executions per ref;
- no persistent candidate-only broad failure remains;
- final diff is test/production scoped as reviewed;
- final worktree and whitespace checks pass.

This supports the selected visibility-only contract. It does not prove unrelated lifecycle policies or all product surfaces.

### 18.2 Test-harness convention

Convention evidence is independent of code correctness:

- `tests/all.rs` documents one integration test binary;
- `tests/suite/mod.rs` says it aggregates former standalone tests;
- `suite/mod.rs` already registers `code_mode`;
- the root Justfile says to prefer `just test` and defines nextest settings;
- existing code-mode helpers belong in the aggregate parent.

A test can assert correct behaviour and still be packaged contrary to repository convention. That is why the production implementation passed while test packaging received a change request.[^roundtable-synthesis]

### 18.3 Environment failures

Environment/tooling incidents included:

- missing `just`, DotSlash, `uv`, and later cargo-nextest in Lima;
- signal-9 linker kills from an overly broad direct Cargo command;
- missing `codex` and `test_stdio_server` helpers in broad GitHub runs;
- filesystem/sandbox SIGABRT outcomes;
- timeouts in sandbox/network-sensitive tests;
- fresh ephemeral full-run VMs without a shared Cargo target cache.

These failures affect what can be claimed. They do not automatically exonerate the patch, which is why exact-base comparisons and focused reruns were required.

### 18.4 Baseline failures

Baseline failures are outcomes reproduced on exact upstream or otherwise shown unrelated:

- 93 shared failed-test names;
- one shared timeout;
- 53 environment/missing-dependency outcomes;
- 26 known/unrelated assertions;
- shared sandbox-sensitive failures;
- the upstream-only broad differential that disappeared in focused reruns.

The broad result is therefore not “green,” but it also does not leave a persistent Patch 1-specific failure.[^project-inventory]

### 18.5 Flaky or race-related hypotheses

The record contains several distinct race/flake questions:

1. fixed one-second/two-second acceptance timing — design-level race removed by handshake;
2. candidate-only broad large-output failure — passed 3/3 on both refs, classified run-order/concurrency flake;
3. upstream-only compact-resume failure — passed 3/3 on both refs, same classification;
4. optional compatibility header — hypothesised, tested 10 repetitions per ref, not observed;
5. one broad nextest flaky pass in `rollout_budget` — unrelated and explicitly counted.

These must not be collapsed into “no flakes.” The accurate wording is scoped to the particular commands and observations.

### 18.6 Validation not performed

The following were not performed or not established:

- complete workspace suite;
- a green broad `codex-core` project suite;
- full project rerun after every test-polish commit;
- macOS validation;
- Windows nested `exec_command` acceptance validation;
- x86_64 parity run;
- remote code-mode host parity for this contract;
- long-duration soak or probabilistic race testing beyond recorded repetitions;
- CPU, memory, descriptor, socket, or process-group leak measurement;
- shutdown, interrupt, subagent, dispatch, or recovery-policy tests as part of Patch 1;
- cross-turn dispatch executable reproduction;
- proof that global conversation-history limits can never hide an earlier status.

No broad project or workspace suite was rerun for the final test-only supplement, by explicit instruction.[^supplement-receipt]

## 19. Audit of public validation wording

The latest publication-conventions review already required bounded language: focused and acceptance targets passed; the broad project suite was red on both candidate and exact upstream; no persistent candidate-only failure remained; the workspace suite was not run.[^publication-review]

The following wording is evidence-aligned:

> Repository-native formatting and scoped Clippy fix passed. Four focused unit tests and five aggregate acceptance cases passed. Two existing compatibility tests passed ten repetitions on the candidate and ten on exact upstream base. The broad `codex-core` project suite was red on both refs; its persistent failures were baseline/environment-limited, and the two differing broad-run failures passed focused reruns on both refs. No complete workspace suite was run.

Claims stronger than the evidence, and therefore unsuitable for public copy, include:

| Overclaim | Why unsupported | Correct bounded form |
|---|---|---|
| “All tests passed.” | Broad project run had 94 failures, one timeout, and nine skips on each ref; workspace not run. | Name the four unit and five acceptance passes, compatibility repetitions, and broad red-on-both classification. |
| “The `codex-core` suite passed.” | `just test -p codex-core` was red on both refs. | “No persistent candidate-only failure remained in the matched broad differential.” |
| “CI is green.” | Only focused paths were green; broad hosted runs were not. | “Patch-scoped validation passed; broad project suite remained baseline-red.” |
| “No flakes.” | Broad nextest recorded one flaky pass; two differential failures disappeared in focused reruns. | “No flake was observed in the final focused Patch 1 commands; broad-run flakes were separately classified.” |
| “No regressions.” | Absolute absence is not provable from selected tests. | “No persistent candidate-only failure remained in the observed matched differential.” |
| “Validated on Linux and macOS.” | Runtime evidence is Linux aarch64 Lima; no macOS run is recorded. | “Validated on Linux aarch64 under Lima.” |
| “The warning cannot be truncated.” | The test covers code-mode emitted-output truncation, not every later global history limit. | “The warning is represented in the separate code-mode status header after emitted-output truncation.” |
| “The output always has exactly two items.” | Final test intentionally rejects this cardinality claim. | “A separate status item and at least one separate non-empty emitted-output item are present.” |
| “All acceptance tests are network-independent.” | Aggregate code-mode tests retain the established network skip path; only the manager-query unit test is explicitly network-independent. | Distinguish the network-independent unit test from the integration cases. |
| “No tests were skipped.” | The final focused selected tests passed, but the broad project runs had nine skips. | Scope skip wording to a named command or omit it. |
| “Candidate and base broad suites used one shared cache.” | Complete broad runs used separate ephemeral VMs and fresh target dirs. | Only the focused differential and compatibility repetitions used a shared runner/cache. |
| “Patch 1 fixes orphan process cleanup.” | Patch 1 is visibility-only and deliberately preserves process persistence. | “Patch 1 restores model-visible IDs for surviving exact-cell sessions.” |

One earlier internal runtime report opened with “Patch 1 is green on the published ... head.” In context it immediately listed focused commands, but as public shorthand “green” is too easy to misread as a green project/workspace suite. Public copy should replace it with named, bounded results.[^runtime-report]

Likewise, “skips/flakes none” was accurate only for the correctly scoped early commands on that tree; it must not be generalised across the broad nextest evidence.

## 20. Final result ledger

### Negative proof

```text
Test:     code_mode_completion_does_not_surface_discarded_live_exec_sessions
Ref:      7298dcf44f61164ffc25b8bdf5f136281caeb9f5
Platform: Linux aarch64 Lima
Result:   1 passed; 0 failed; 0 ignored
```

### Early implementation-era focused validation

```text
cargo check -p codex-core --tests                   passed
3 code-mode unit tests                              passed
3 unified-exec unit tests                           passed
5 standalone acceptance tests                       passed
standalone acceptance elapsed                       17.12s
```

### Final repository-native focused validation

```text
just fmt                                             passed
just fix -p codex-core                               passed
4 focused unit tests via just test                   4 passed; 0 failed
5 aggregate orphan-session cases via just test       5 passed; 0 failed
upstream compatibility, 10 × 2                      20 passed; 0 failed
candidate compatibility, 10 × 2                     20 passed; 0 failed
candidate-only optional-header race                  not observed
compatibility expectation changes                   none
git status --short --untracked-files=all             clean
git diff --check                                     passed
```

### Matched broad project suite

```text
Command on each ref: just test -p codex-core
Candidate: 3,015 passed (1 flaky), 94 failed, 1 timed out, 9 skipped / 3,110
Upstream:  3,007 passed,           94 failed, 1 timed out, 9 skipped / 3,102
Shared:    93 failure names + shared timeout
Differing broad failures: each passed 3/3 on candidate and 3/3 on upstream
Classification: pass with baseline-red caveat
Workspace suite: not run
```

## 21. Final testing conclusion

Patch 1's final testing case is not “everything passed.” It is stronger and more precise:

- the before-state is preserved as a passing negative reproduction;
- the desired behaviour is expressed by five end-to-end acceptance contracts;
- the aggregate harness and parent helpers follow explicit repository convention;
- cleanup covers process-creating submission errors and panics;
- exited-session handling is causally synchronised rather than sleep-based;
- yielded neutrality checks the named warning contract;
- large-output coverage avoids accidental serialisation cardinality requirements;
- the manager query has direct deterministic unit coverage;
- final selected tests use the repository-native nextest route;
- compatibility stress found no candidate-only race in the recorded repetitions;
- the broad project result was red on both refs but left no persistent candidate-only failure after controlled differential reruns;
- the workspace and other unlisted surfaces remain unvalidated.

That is the evidence boundary maintainers should review and public copy should preserve.

## References

[^deep-dive-readme]: [`notes/code-mode-orphan-fix/deep-dive/README.md`](./README.md), especially the evidence and shared-rules sections.
[^negative-commit]: [`7298dcf44f61164ffc25b8bdf5f136281caeb9f5`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5), `test(core): reproduce hidden code-mode exec sessions`.
[^negative-handoff]: [`agent-2-handoff.md` at acceptance head `89ffd99...`](https://github.com/teamleaderleo/codex/blob/89ffd99b81e872e3a961767e67fb8ec410df7eae/notes/code-mode-orphan-fix/agent-2-handoff.md#L5-L36).
[^coordination]: [`coordination-status.md`](https://github.com/teamleaderleo/codex/blob/research/code-mode-orphan-handoffs/notes/code-mode-orphan-fix/coordination-status.md#L38-L55).
[^acceptance-file]: [`code_mode_orphan_sessions.rs` at `89ffd99...`](https://github.com/teamleaderleo/codex/blob/89ffd99b81e872e3a961767e67fb8ec410df7eae/codex-rs/core/tests/code_mode_orphan_sessions.rs).
[^truncation-correction]: [`89ffd99b81e872e3a961767e67fb8ec410df7eae`](https://github.com/teamleaderleo/codex/commit/89ffd99b81e872e3a961767e67fb8ec410df7eae), `test(core): tolerate truncated large code-mode output`.
[^acceptance-yielded]: [`code_mode_orphan_sessions.rs`, yielded and two-cell cases](https://github.com/teamleaderleo/codex/blob/89ffd99b81e872e3a961767e67fb8ec410df7eae/codex-rs/core/tests/code_mode_orphan_sessions.rs#L365-L523).
[^roundtable-agent2]: [`final-roundtable/agent-2-testing-conventions.md` at review commit `695a314...`](https://github.com/teamleaderleo/codex/blob/695a31448285bdad29aae7f18fc031cd8e4f5cb4/notes/code-mode-orphan-fix/final-roundtable/agent-2-testing-conventions.md).
[^runtime-report]: [`agent-2-test-runtime-report.md`](https://github.com/teamleaderleo/codex/blob/research/code-mode-orphan-handoffs/notes/code-mode-orphan-fix/agent-2-test-runtime-report.md).
[^all-comment]: [`codex-rs/core/tests/all.rs` at exact upstream base](https://github.com/teamleaderleo/codex/blob/61a44880a85d2fd0d8770908dea5733495e571c8/codex-rs/core/tests/all.rs#L5-L9).
[^suite-comment]: [`codex-rs/core/tests/suite/mod.rs` at exact upstream base](https://github.com/teamleaderleo/codex/blob/61a44880a85d2fd0d8770908dea5733495e571c8/codex-rs/core/tests/suite/mod.rs#L1-L53).
[^final-code-mode]: [`codex-rs/core/tests/suite/code_mode.rs` at final head](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/codex-rs/core/tests/suite/code_mode.rs#L75-L258).
[^original-polish-receipt]: [`agent-2-test-polish-validation-receipt.md` at receipt commit `4ea7d60...`](https://github.com/teamleaderleo/codex/blob/4ea7d60c562058003afce58ef159ff9ea429a584/notes/code-mode-orphan-fix/agent-2-test-polish-validation-receipt.md).
[^supplement-commit]: [`760216784efaee1ba6a3b1250349f31d5f91c7ca`](https://github.com/teamleaderleo/codex/commit/760216784efaee1ba6a3b1250349f31d5f91c7ca), `test: add code-mode compatibility coverage`.
[^supplement-receipt]: [`agent-2-test-polish-supplemental-validation-receipt.md` at receipt commit `55598f8...`](https://github.com/teamleaderleo/codex/blob/55598f8ea3b7488cda3113acf379c730b512ac00/notes/code-mode-orphan-fix/agent-2-test-polish-supplemental-validation-receipt.md).
[^agent3-supplement-review]: [`agent-3-test-polish-review-cc01596.md` at `8224df4...`](https://github.com/teamleaderleo/codex/blob/8224df4ef450e25c76612dff94bc5496fa1c4548/notes/code-mode-orphan-fix/agent-3-test-polish-review-cc01596.md).
[^justfile]: [`justfile` at final head](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/justfile#L1-L88).
[^format-script]: [`scripts/format.py` at final head](https://github.com/teamleaderleo/codex/blob/760216784efaee1ba6a3b1250349f31d5f91c7ca/scripts/format.py#L38-L145).
[^project-inventory]: [`agent-1-clean-candidate-project-failure-inventory.md` at `a3cdd18...`](https://github.com/teamleaderleo/codex/blob/a3cdd18d2cd8e60e5997c25dd41d55b1af2ec2db/notes/code-mode-orphan-fix/agent-1-clean-candidate-project-failure-inventory.md).
[^roundtable-synthesis]: [`final-roundtable/synthesis.md` at `ecf6459...`](https://github.com/teamleaderleo/codex/blob/ecf6459c856a28b154d86ea9feca7336d478c99c/notes/code-mode-orphan-fix/final-roundtable/synthesis.md).
[^publication-review]: [`final-roundtable/agent-4-publication-conventions.md`](https://github.com/teamleaderleo/codex/blob/research/code-mode-orphan-handoffs/notes/code-mode-orphan-fix/final-roundtable/agent-4-publication-conventions.md).
