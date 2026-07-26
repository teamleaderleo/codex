# Code-mode live session IDs

A code-mode cell can start nested terminal commands and receive session IDs for commands that keep running. If its JavaScript keeps only each command's output, those copied IDs can be discarded while the session-level unified-exec process manager still owns the live processes. The completing-cell result can then say `Script completed` without showing the handles needed to inspect, continue, or stop those processes.

The patch retains the existing creator-cell identity on stored process entries, asks the existing manager which processes created by that exact cell are still live when the final response is formatted, sorts their logical session IDs numerically, and reports up to 64 IDs. When more than 64 match, it displays the first 64 sorted IDs plus an exact suffix such as `(+7 more)`.

## Findings

1. The defect is lost model-visible control information, not loss of the manager-owned processes.
2. Liveness is a point-in-time manager observation and attribution is limited to the exact completing cell.
3. Lists of 64 or fewer matching IDs are complete; overflow output is deliberately bounded.
4. The only model-visible behaviour change is the completion-status text. Process ownership and lifecycle policy are unchanged.
5. The formatter and manager query received nine focused tests. Five acceptance cases passed locally on the pre-decoupling capped workspace; four selected Docker cases passed, and the host-path survivor case was excluded from the Docker filter and passed locally.
6. The current head adds target-Windows guards to the four acceptance cases whose commands require POSIX shell syntax. That guard-only commit has not yet received a new public Actions run.
7. The code diff is above the repository's 800-line review guideline because the acceptance module is large. The pull-request draft records a coherent two-stage split if maintainers prefer smaller review units.

See [validation.md](validation.md) for exact refs, commands, run boundaries, and limitations.
