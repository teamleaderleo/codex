# Summary

Code mode can start terminal commands from JavaScript. When a command keeps running, `exec_command` returns a session ID that the model can use to check it, send input, or stop it. The failure occurs when the JavaScript keeps only the command output and drops that ID: the cell can report `Script completed` while the terminal is still live, and the model no longer has the handle needed to control it.

The proposed change records which code-mode cell created each stored live terminal session. When that cell finishes, Codex asks the existing process manager which of its sessions are still live and reports those session IDs in the status. It does not stop processes or change background-process lifetime.

## Findings

1. The live process is still owned by Codex; the missing information is the model-visible session ID.
2. The fix reports only still-live sessions created by the exact completing cell.
3. Exited sessions and sessions created by other cells are excluded.
4. Ordinary yielded responses and the JavaScript result schema are unchanged.
5. Focused tests passed; the broad `codex-core` run remained red on both candidate and exact base, and the complete workspace suite was not run.

## Documents

- [Issue](issue.md)
- [Pull request](pull-request.md)
- [Deep dive](deep-dive.md)
- [Sources](sources.md)
- [Code comparison](https://github.com/teamleaderleo/codex/compare/61a44880a85d2fd0d8770908dea5733495e571c8...760216784efaee1ba6a3b1250349f31d5f91c7ca)
