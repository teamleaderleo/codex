# Sources

This index supports the [standalone issue](issue.md), [invited PR draft](pull-request.md), and [technical deep dive](deep-dive.md).

## Upstream code

- [Verified upstream snapshot `95637f70`](https://github.com/openai/codex/commit/95637f7056835fea66bdd0044414af480fc0fd74)
- [Current code-mode terminal response formatting](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/codex-rs/core/src/tools/code_mode/mod.rs#L201-L275)
- [`ToolInvocation` carries `ToolCallSource`](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/codex-rs/core/src/tools/context.rs#L47-L71)
- [`ExecCommandHandler` currently constructs unified-exec context without creator-cell provenance](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L108-L133)
- [Existing unified-exec context and process entries](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/codex-rs/core/src/unified_exec/mod.rs#L77-L181)
- [Invitation-only contribution policy](https://github.com/openai/codex/blob/95637f7056835fea66bdd0044414af480fc0fd74/docs/contributing.md)

## Prototype code

- [Prototype head `77e7e314`](https://github.com/teamleaderleo/codex/commit/77e7e3149df366236db2426596c23ebbe1d6bb48)
- [Prototype base-to-head comparison](https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...77e7e3149df366236db2426596c23ebbe1d6bb48)
- [Negative before-state reproduction `7298dcf4`](https://github.com/teamleaderleo/codex/commit/7298dcf44f61164ffc25b8bdf5f136281caeb9f5)

### Creator-cell provenance

- [`ExecCommandHandler` captures the code-mode source cell](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L132-L138)
- [`UnifiedExecContext` carries typed creator metadata](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L76-L99)
- [`ProcessEntry` retains creator-cell attribution](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L189-L200)
- [`store_process` copies creator metadata into the entry](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/process_manager.rs#L944-L976)

### Lookup and formatting

- [`live_process_ids_created_by_cell`](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod.rs#L168-L180)
- [Terminal-response lookup and yielded exclusion](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L201-L269)
- [Bounded deterministic status formatting](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L270-L305)
- [`has_exited()` backend asymmetry](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/process.rs#L194-L205)

## Prototype tests

- [Focused formatter tests](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/tools/code_mode/mod.rs#L444-L612)
- [Direct manager lookup test](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/src/unified_exec/mod_tests.rs#L333-L395)
- [Acceptance module](https://github.com/teamleaderleo/codex/blob/77e7e3149df366236db2426596c23ebbe1d6bb48/codex-rs/core/tests/suite/code_mode/orphan_sessions.rs)

The invited PR should retain only the primary discarded-handle end-to-end case from that acceptance module unless maintainers request broader coverage.

## Execution evidence

- [Focused validation run 30220464228](https://github.com/teamleaderleo/codex/actions/runs/30220464228)
- [Local and Docker acceptance run 30217686056](https://github.com/teamleaderleo/codex/actions/runs/30217686056)
- [Scrubbed prototype validation record](validation.md)

## Related reports

| Issue | Relationship |
|---|---|
| [#34866](https://github.com/openai/codex/issues/34866) | Broader wrapper/process completion contradiction and lifecycle representation. |
| [#33816](https://github.com/openai/codex/issues/33816) | Model-side loss of a yielded session can produce false completion and duplicate commands. |
| [#14731](https://github.com/openai/codex/issues/14731) | Proposes keeping a turn active while unified-exec work remains live. |
| [#15723](https://github.com/openai/codex/issues/15723) and [#32188](https://github.com/openai/codex/issues/32188) | Background completion wake-up proposals. |
| [#13733](https://github.com/openai/codex/issues/13733) | Cost of repeated model-driven polling. |

The standalone issue targets discarded handle visibility only.