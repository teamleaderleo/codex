from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one anchor in {path}, found {count}")
    file_path.write_text(text.replace(old, new, 1), encoding="utf-8")


path = "defs.bzl"
replace_once(
    path,
    '''        integration_compile_data_extra = [],
        integration_test_args = [],
        unit_test_args = [],
        integration_test_timeout = None,
''',
    '''        integration_compile_data_extra = [],
        integration_test_args = [],
        unit_test_args = [],
        binary_test_target_compatible_with = [],
        integration_test_timeout = None,
''',
)

replace_once(
    path,
    '''        integration_compile_data_extra: Extra compile_data for integration tests.
        integration_test_args: Optional args for integration test binaries.
        unit_test_args: Optional args for the unit test binary.
        integration_test_timeout: Optional Bazel timeout for integration test
''',
    '''        integration_compile_data_extra: Extra compile_data for integration tests.
        integration_test_args: Optional args for integration test binaries.
        unit_test_args: Optional args for the unit test binary.
        binary_test_target_compatible_with: Platform constraints for binary unit tests.
        integration_test_timeout: Optional Bazel timeout for integration test
''',
)

replace_once(
    path,
    '''        rust_binary(
            name = binary,
            crate_name = binary.replace("-", "_"),
            crate_root = main,
            deps = all_crate_deps() + maybe_deps + deps_extra,
            edition = crate_edition,
            rustc_flags = rustc_flags_extra + WINDOWS_RUSTC_LINK_FLAGS,
            srcs = native.glob(["src/**/*.rs"]),
            visibility = ["//visibility:public"],
        )

    for binary_label in extra_binaries:
''',
    '''        rust_binary(
            name = binary,
            crate_name = binary.replace("-", "_"),
            crate_root = main,
            deps = all_crate_deps() + maybe_deps + deps_extra,
            edition = crate_edition,
            rustc_flags = rustc_flags_extra + WINDOWS_RUSTC_LINK_FLAGS,
            srcs = native.glob(["src/**/*.rs"]),
            visibility = ["//visibility:public"],
        )

        binary_unit_test_name = binary + "-bin-unit-tests"
        binary_unit_test_binary = binary_unit_test_name + "-bin"
        binary_unit_test_shard_count = _test_shard_count(test_shard_counts, binary_unit_test_name)

        # Keep the Rust test manual so the repo-root wrapper owns filtering and
        # sharding while Clippy can still discover the underlying test crate.
        rust_test(
            name = binary_unit_test_binary,
            crate = ":" + binary,
            crate_features = crate_features,
            deps = all_crate_deps(normal_dev = True),
            rustc_flags = rustc_flags_extra + WINDOWS_RUSTC_LINK_FLAGS + [
                "--remap-path-prefix=../codex-rs=",
                "--remap-path-prefix=codex-rs=",
            ],
            rustc_env = rustc_env,
            data = test_data_extra,
            tags = test_tags + ["manual"],
        )

        binary_unit_test_kwargs = {}
        if unit_test_args:
            binary_unit_test_kwargs["args"] = unit_test_args
        if unit_test_timeout:
            binary_unit_test_kwargs["timeout"] = unit_test_timeout
        if binary_unit_test_shard_count:
            binary_unit_test_kwargs["shard_count"] = binary_unit_test_shard_count
            binary_unit_test_kwargs["flaky"] = True

        workspace_root_test(
            name = binary_unit_test_name,
            env = test_env,
            test_bin = ":" + binary_unit_test_binary,
            workspace_root_marker = "//codex-rs/utils/cargo-bin:repo_root.marker",
            target_compatible_with = binary_test_target_compatible_with,
            tags = test_tags,
            **binary_unit_test_kwargs
        )

    for binary_label in extra_binaries:
''',
)

print("FIELDWORK_BAZEL_BINARY_UNIT_TEST_SOURCE=defs.bzl")
