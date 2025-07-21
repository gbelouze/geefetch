import difflib


def git_style_diff(a: str, b: str) -> str:
    """
    Generate a unified diff between two strings, similar to Git-style diffs.

    Parameters
    ----------
    a : str
        The original string.
    b : str
        The modified string to compare against `a`.

    Returns
    -------
    str
        A unified diff string showing the differences between `a` and `b`,
        using the standard Git-style format.
    """
    diff = difflib.unified_diff(
        a.splitlines(keepends=True), b.splitlines(keepends=True), lineterm=""
    )
    return "".join(diff)
