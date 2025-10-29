import logging
import os

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
)

__all__ = ["default_bar", "geefetch_debug"]


log = logging.getLogger(__name__)


def geefetch_debug() -> bool:
    match os.getenv("GEEFETCH_DEBUG"):
        case "true":
            return True
        case "1":
            return True
        case _:
            return False


def default_bar() -> Progress:
    disabled = geefetch_debug()
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
    log.info(f"{geefetch_debug()=}")
