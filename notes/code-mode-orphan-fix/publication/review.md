# Final review handoff

Use this page as the single entry point for coordinated review of Patch 1.

## Review targets

### Code

- Branch: [`fix/code-mode-live-session-ids`](https://github.com/teamleaderleo/codex/tree/fix/code-mode-live-session-ids)
- Head: [`77e7e3149df366236db2426596c23ebbe1d6bb48`](https://github.com/teamleaderleo/codex/commit/77e7e3149df366236db2426596c23ebbe1d6bb48)
- [Selected-base comparison](https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...77e7e3149df366236db2426596c23ebbe1d6bb48)

### Final drafts and evidence

- Branch: [`review/code-mode-final-draft`](https://github.com/teamleaderleo/codex/tree/review/code-mode-final-draft/notes/code-mode-orphan-fix/publication)
- [Summary](summary.md)
- [Issue draft](issue.md)
- [Pull-request draft](pull-request.md)
- [Deep dive](deep-dive.md)
- [Sources](sources.md)
- [Validation](validation.md)

Nothing has been opened upstream. Review edits belong on the final-draft branch; implementation changes belong on the code branch.

## Suggested review lanes

### Behaviour and issue framing

Read the [summary](summary.md) and [issue draft](issue.md).

Check that the report isolates one reproducible defect: a completing code-mode cell can omit the session IDs of nested commands that remain live and manager-owned. Confirm that the impact language does not imply a memory leak, security severity, automatic cleanup failure, or a broader wake-up defect.

### Production-code correctness

Review the [code comparison](https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...77e7e3149df366236db2426596c23ebbe1d6bb48) with the [deep dive](deep-dive.md).

Check creator-cell attribution, exact-cell filtering, point-in-time liveness, numeric ordering, the independent 64-ID display bound, final-response selection, and warning placement after code-mode output truncation. Confirm that ownership and lifecycle policy remain unchanged.

### Tests and validation

Read [validation.md](validation.md) and inspect the linked Actions runs.

Check that every pass is attributed to the ref or workspace that actually ran. Treat the Wine attempt as blocked before Rust test discovery—not as a pass or a Patch 1 failure. Confirm that the four target-Windows guards are test-routing changes only.

### Current-upstream adaptation

Read the **Current upstream drift** section in the [deep dive](deep-dive.md).

Confirm that current upstream still lacks an equivalent manager lookup, that `ToolCallSource::CodeMode` still exposes the cell ID, and that the implementation will require a normal rebase and adaptation before submission.

### Editorial and reviewability

Read the [issue draft](issue.md) and [pull-request draft](pull-request.md) without the deep dive first.

Check that each stands alone, uses current Codex conventions, stays concise, and sends technical detail to linked evidence rather than repeating it. Review the proposed two-stage split only as an optional reviewability measure.

## Questions every reviewer should answer

1. Is any factual claim broader than the code or recorded test evidence?
2. Is there a simpler implementation that preserves the same exact-cell and lifecycle boundaries?
3. Can any live process be incorrectly included, or any matching process incorrectly excluded, under manager state at lookup time?
4. Is the `Result` / `Terminated` versus `Yielded` boundary correct?
5. Is the 64-ID output contract clear and independent of manager capacity?
6. Do the issue and PR explain the change without turning into a design document?
7. Is any validation statement ambiguous about the tested ref, environment, selection filter, or blocked Wine path?
8. Does current upstream drift require a design change, or only implementation adaptation?

## How to report findings

For each finding, include:

- severity: blocking, important, or polish;
- target: code, issue, PR, deep dive, sources, or validation;
- exact file, symbol, or section;
- the claim or behaviour that is wrong or unclear;
- the smallest correction that resolves it.

Avoid proposing adjacent lifecycle, polling, wake-up, process-group, sandbox, or backpressure work unless the current patch creates a concrete regression in that area.

## Ready-to-submit criteria

The package is ready for an upstream invitation when:

- no blocking correctness or factual findings remain;
- issue and PR wording match the final adapted code;
- validation has been rerun on the final rebased head;
- the rebase does not change the stated behaviour or scope;
- review-size handling is agreed;
- an upstream maintainer has invited the issue or contribution.
