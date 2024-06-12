import difflib


def git_style_diff(a: str, b: str) -> str:
    diff = difflib.unified_diff(
        a.splitlines(keepends=True), b.splitlines(keepends=True), lineterm=""
    )
    return "".join(diff)
