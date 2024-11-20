import logging
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install

__all__ = ["setup"]


def setup(level: int = logging.NOTSET, logfile: Path | None = None) -> None:
    """Configure the logging level and message format."""
    FORMAT = "[white]%(name)s[/]\t %(message)s"

    handlers = [RichHandler(markup=True)]
    install()
    if logfile is not None:
        handlers.append(RichHandler(markup=True, console=Console(file=logfile.open("a+"))))  # noqa: SIM115
    logging.basicConfig(
        level=max(logging.INFO, level), format=FORMAT, datefmt="[%X]", handlers=handlers
    )
    logging.getLogger("geefetch").setLevel(level)
