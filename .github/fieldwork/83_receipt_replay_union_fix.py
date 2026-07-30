from pathlib import Path

for rust_path in Path("codex-rs").rglob("*.rs"):
    lines = rust_path.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = False
    for index in range(len(lines) - 1):
        current = lines[index].lstrip()
        following = lines[index + 1].lstrip()
        if (
            current.startswith("RolloutItem::ToolOperationReceipt(_)")
            and following.startswith("RolloutItem::SessionMeta(_)")
            and not following.startswith("|")
        ):
            indent = lines[index + 1][: len(lines[index + 1]) - len(following)]
            lines[index + 1] = f"{indent}| {following}"
            changed = True
    if changed:
        rust_path.write_text("".join(lines), encoding="utf-8")
