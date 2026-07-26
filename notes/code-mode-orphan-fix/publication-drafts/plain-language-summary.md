# Plain-language Patch 1 summary

Status: public-facing synthesis draft; unpublished.

Code mode can run terminal commands from JavaScript. When one of those commands keeps running, `exec_command` returns a session ID that can be used to check the command, send it input, or stop it. The failure here happens when the JavaScript keeps only the command's text output and drops that session ID. The code cell can then say `Script completed` even though the terminal session is still alive. Codex still tracks the process internally, but the model no longer has the ID it needs to control it.

Patch 1 restores that missing control visibility. It remembers which code-mode cell created each stored live terminal session. When that exact cell reaches a terminal result, Codex asks the existing session-level unified-exec process manager which of that cell's sessions are still live and adds their session IDs to the status header. Exited sessions and sessions from other cells are excluded.

The patch does **not** kill the processes, wait for them to finish, or change when background work is allowed to persist. It also does not change the JavaScript result schema, nested call IDs, process pruning, shutdown, interrupt, recovery, wake-up, or public protocol behaviour. It only makes the existing live-session handles visible again at the point where the cell reports completion or termination.

This matters because a still-running command without a visible session ID may continue using CPU, memory, sockets, file descriptors, locks, subprocesses, network activity, or filesystem state without an obvious control path. That is an operational resource-retention risk, not evidence of a literal Rust memory leak, and the current evidence does not establish a security severity.

The final candidate has four focused unit tests and five aggregate acceptance cases covering multiple live sessions, exited-session exclusion, exact-cell isolation, output-truncation placement, and yielded-response neutrality. Two existing compatibility tests passed 20/20 executions on the candidate and 20/20 on the exact upstream base. The broad `codex-core` run was red on both refs, with no persistent candidate-only failure after focused comparison; the complete workspace suite was not run.

## Read next

- [Polished standalone issue proposal](standalone-issue-layered.md)
- [PR-ready technical proposal](pull-request-layered.md)
- [Public technical deep dive](public-deep-dive.md)
- [Works cited and evidence classification](works-cited.md)
- [Final code comparison](https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...760216784efaee1ba6a3b1250349f31d5f91c7ca)
