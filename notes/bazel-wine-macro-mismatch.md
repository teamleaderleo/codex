# Bazel Wine-exec macro mismatch

## Summary

The repository's documented Wine-exec target cannot reach test execution because Bazel fails while loading `codex-rs/windows-sandbox-rs/BUILD.bazel`.

This is separate from the code-mode lost-handle work tracked in `openai/codex#35613`. The Wine attempts exposed a repository build-graph mismatch that also remains present on current upstream `main`.

## Reproduction

From an x86-64 Linux Bazel environment:

```sh
bazel test //codex-rs/core:core-all-wine-exec-test \
  --nocache_test_results \
  --test_output=all
```

Public reproductions against implementation head `77e7e3149df366236db2426596c23ebbe1d6bb48`:

- <https://github.com/teamleaderleo/codex/actions/runs/30293323612>
- <https://github.com/teamleaderleo/codex/actions/runs/30296440567>

Both attempts fail identically before any test target is constructed.

## Failure

```text
ERROR: Traceback (most recent call last):
  File "codex-rs/windows-sandbox-rs/BUILD.bazel", line 3, column 17, in <toplevel>
    codex_rust_crate(
  File "defs.bzl", line 181, column 5, in codex_rust_crate
    def codex_rust_crate(
Error: codex_rust_crate() got unexpected keyword argument: binary_test_target_compatible_with

ERROR: no such target '//codex-rs/windows-sandbox-rs:codex-command-runner'
ERROR: Analysis of target '//codex-rs/core:core-all-wine-exec-test' failed
ERROR: No test targets were found, yet testing was requested
```

## Cause

`codex-rs/windows-sandbox-rs/BUILD.bazel` passes:

```starlark
binary_test_target_compatible_with = ["@platforms//os:windows"]
```

but the current `codex_rust_crate` signature in `defs.bzl` has no such parameter. Package loading aborts before the macro declares `codex-command-runner` and `codex-windows-sandbox-setup`, so the core Wine target cannot analyze.

The same mismatch is present on upstream `main` at commit `8495963ac6d15a3ac891517d979f5509d55605c0`:

- `codex-rs/windows-sandbox-rs/BUILD.bazel` blob `af54a80c47b38e800a66c77d86fbddc5bf4c5db7`;
- `defs.bzl` blob `76a82ab3624d324b26753e04c75ff8b1f6af0f29`.

The original Wine-exec integration commit `1fe89de576e2ee6dc341e6f97beca6160ef85a7f` did not yet pass `binary_test_target_compatible_with` from the Windows sandbox BUILD file, so the mismatch was introduced later.

## Expected

The BUILD call and macro contract should agree, and `//codex-rs/core:core-all-wine-exec-test` should at least complete Bazel analysis and construct its test target.

## Repair question

The correct repair should be established from the intended target graph rather than guessed from the argument name.

Two narrow possibilities need to be distinguished:

1. `binary_test_target_compatible_with` was an intended macro input that was dropped or never completed, in which case it should be restored and applied to the specific generated **test-facing target** it was designed for.
2. The call-site argument is stale after a macro/test-target refactor, in which case it should be removed and the Windows sandbox tests should express compatibility through the current target shape.

Do **not** blindly apply `@platforms//os:windows` to the generated helper `rust_binary` targets. `codex-rs/core/BUILD.bazel` consumes `codex-command-runner` and `codex-windows-sandbox-setup` through `extra_binaries`; making those labels globally Windows-only could make native Linux core test targets incompatible instead of repairing Wine-exec.

The argument name suggests test-target compatibility rather than a blanket platform restriction on the helper binaries, but the current macro no longer exposes any matching target or parameter. History and `cquery` should determine the intended layer.

## Validation plan

1. Trace the commit that added the BUILD argument and identify the target it intended to constrain.
2. `bazel query` or `bazel cquery` the Windows sandbox helper and test targets under native Linux and Windows-transitioned platforms.
3. Run a representative native Linux `codex-core` Bazel target and confirm it remains runnable.
4. Run `bazel test //codex-rs/core:core-all-wine-exec-test --nocache_test_results --test_output=all` on x86-64 Linux.
5. Confirm the suite reaches Rust test execution and emits the expected source-local Windows/remote skips.
6. Keep this fix independent of the code-mode implementation branch so the Wine result is clearly a harness/build-graph result.

## Boundary

The two public runs are not product-test failures: no Patch 1 assertion, Rust test process, Windows exec server, or runtime skip guard executed. This note is specifically about restoring an analyzable Bazel graph for the repository's documented Wine-exec target.
