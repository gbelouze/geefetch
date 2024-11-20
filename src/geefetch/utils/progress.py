import logging
import os

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
)

__all__ = ["default_bar", "disable_progress"]


log = logging.getLogger(__name__)


def disable_progress() -> bool:
    match os.getenv("GEEFETCH_DEBUG"):
        case "true":
            return True
        case "1":
            return True
        case _:
            return False


def default_bar() -> Progress:
    disabled = disable_progress()
    if disabled:
        log.warning("progress bar is disabled.")
    return Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        refresh_per_second=1,
        disable=disabled,
    )


if __name__ == "__main__":
    log.info(f"{disable_progress()=}")
