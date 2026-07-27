# Prototype validation

This record preserves the evidence that establishes feasibility while keeping final PR validation separate.

## Relevant refs

| Role | Ref |
|---|---|
| Selected prototype base | [`61a44880a85d2fd0d8770908dea5733495e571c8`](https://github.com/openai/codex/commit/61a44880a85d2fd0d8770908dea5733495e571c8) |
| Independent display-cap prototype | [`eb530466cafac0a5aee86342cd2b5ada9047d448`](https://github.com/teamleaderleo/codex/commit/eb530466cafac0a5aee86342cd2b5ada9047d448) |
| Published prototype head | [`77e7e3149df366236db2426596c23ebbe1d6bb48`](https://github.com/teamleaderleo/codex/commit/77e7e3149df366236db2426596c23ebbe1d6bb48) |
| Verified upstream snapshot | [`95637f7056835fea66bdd0044414af480fc0fd74`](https://github.com/openai/codex/commit/95637f7056835fea66bdd0044414af480fc0fd74) |

The verified upstream snapshot is five commits ahead of the selected base, with no changes to the four production files touched by the prototype.

## Result matrix

| Coverage | Ref/workspace | Result |
|---|---|---|
| Focused formatter and manager tests | `eb530466...` | 9 passed |
| Formatting, scoped fixes, diff, and cleanliness checks | `eb530466...` | passed |
| Local acceptance | pre-decoupling capped workspace with final remote harness | 5 passed |
| Docker/Linux remote acceptance | same workspace; four selected remote-safe cases | 4 passed |
| Existing compatibility tests | same workspace | 2 passed |

These are prototype results. They come from more than one closely related ref or workspace and should stay out of the final PR's primary validation claim.

## Focused validation

Run: [GitHub Actions 30220464228](https://github.com/teamleaderleo/codex/actions/runs/30220464228)  
Platform: GitHub-hosted Ubuntu 24.04  
Validated head: `eb530466cafac0a5aee86342cd2b5ada9047d448`

Commands:

```sh
just fmt
just fix -p codex-core

UNIT_FILTER='test(/(live_process_ids_created_by_cell_filters_exited_and_sorts|terminal_cell_id_excludes_yielded_responses|terminal_script_status_surfaces_sorted_live_background_sessions|terminal_script_status_preserves_sessions_at_display_limit|terminal_script_status_caps_sessions_above_display_limit|terminal_script_status_sorts_before_truncation|terminal_script_status_formats_exact_omitted_count|terminal_script_status_omits_warning_for_empty_sessions|yielded_script_status_does_not_surface_background_sessions)$/)'

just test -p codex-core --lib -E "$UNIT_FILTER" --no-capture --no-tests=fail
git diff --check
git status --porcelain=v1 --untracked-files=all
```

Results:

- formatting and scoped fixes passed;
- nine focused tests passed;
- diff checks passed;
- the worktree was clean.

The direct manager test provides deterministic evidence for exact-cell filtering, exited-entry exclusion, and numeric ordering in the prototype.

## Acceptance validation

Run: [GitHub Actions 30217686056](https://github.com/teamleaderleo/codex/actions/runs/30217686056)  
Host: GitHub-hosted Ubuntu 24.04  
Remote executor: Docker `ubuntu:24.04`

Results:

- five local acceptance cases passed;
- four remote-safe Docker cases exercised the exec-server path and passed;
- the exited-process/survivor case passed locally and was excluded from the Docker filter, so stale remote-exit exclusion remains untested;
- two existing code-mode compatibility tests passed;
- `git diff --check` passed.

## Final invited-PR requirement

Create the smaller submission branch directly from then-current upstream `main`. Apply the cleanup items from [review.md](review.md), then run and report every claimed check on one final SHA:

- focused manager and formatter tests;
- one primary discarded-handle end-to-end regression;
- relevant existing compatibility tests;
- any terminal-outcome cases agreed in the issue;
- `just test -p codex-core`;
- repository-wide `just test` when requested or approved for the invited contribution;
- `just fix -p codex-core`;
- `just fmt`;
- `git diff --check`.

The final PR should contain one compact validation section tied to that final SHA.
