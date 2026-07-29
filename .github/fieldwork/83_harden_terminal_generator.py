from pathlib import Path
from textwrap import dedent

path = Path('.github/fieldwork/83_terminal_certainty.py')
text = path.read_text(encoding='utf-8')
start = text.index('def replace_once(')
stop = text.index('\n\nlifecycle =')
helpers = dedent('''\
def _indent_block(block: str, spaces: int) -> str:
    prefix = " " * spaces
    return "".join(
        prefix + line if line.strip() else line
        for line in block.splitlines(keepends=True)
    )


def _line_boundary_matches(text: str, block: str):
    matches = []
    offset = 0
    while True:
        index = text.find(block, offset)
        if index < 0:
            return matches
        if index == 0 or text[index - 1] == "\\n":
            matches.append(index)
        offset = index + 1


def _indented_matches(text: str, block: str):
    matches = []
    seen = set()
    for spaces in range(33):
        candidate = _indent_block(block, spaces)
        if candidate in seen:
            continue
        seen.add(candidate)
        for index in _line_boundary_matches(text, candidate):
            matches.append((index, candidate, spaces))
    return matches


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    matches = _indented_matches(text, old)
    if len(matches) != 1:
        raise SystemExit(f"{path}: expected one anchor, found {len(matches)}")
    index, candidate, spaces = matches[0]
    replacement = _indent_block(new, spaces)
    target.write_text(
        text[:index] + replacement + text[index + len(candidate) :],
        encoding="utf-8",
    )


def replace_first(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    matches = _indented_matches(text, old)
    if not matches:
        raise SystemExit(f"{path}: first anchor missing")
    index, candidate, spaces = min(matches, key=lambda match: match[0])
    replacement = _indent_block(new, spaces)
    target.write_text(
        text[:index] + replacement + text[index + len(candidate) :],
        encoding="utf-8",
    )


def replace_last(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    matches = _indented_matches(text, old)
    if not matches:
        raise SystemExit(f"{path}: last anchor missing")
    index, candidate, spaces = max(matches, key=lambda match: match[0])
    replacement = _indent_block(new, spaces)
    target.write_text(
        text[:index] + replacement + text[index + len(candidate) :],
        encoding="utf-8",
    )
''')
path.write_text(text[:start] + helpers + text[stop:], encoding='utf-8')
