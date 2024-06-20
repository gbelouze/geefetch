import logging
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install

__all__ = ["setup"]


def setup(level: int = logging.NOTSET, logfile: Optional[Path] = None) -> None:
    """Configure the logging level and message format."""
    FORMAT = "[white]%(name)s[/]\t %(message)s"

    handlers = [RichHandler(markup=True)]
    install()
    if logfile is not None:
        handlers.append(
            RichHandler(markup=True, console=Console(file=open(logfile, "a+")))
        )
    logging.basicConfig(level=level, format=FORMAT, datefmt="[%X]", handlers=handlers)

    logging.getLogger("geedim").setLevel(max(logging.INFO, level))
    logging.getLogger("geedim.stac").setLevel(
        max(logging.ERROR, level)
    )  # hack while geedim doesn't fix There is no STAC entry for None error.
    logging.getLogger("patched_geedim").setLevel(max(logging.INFO, level))
    logging.getLogger("googleapiclient.discovery").setLevel(max(logging.INFO, level))
    logging.getLogger("matplotlib").setLevel(max(logging.INFO, level))
    logging.getLogger("fiona").setLevel(max(logging.INFO, level))
    logging.getLogger("numexpr").setLevel(max(logging.WARNING, level))
    logging.getLogger("rasterio").setLevel(max(logging.INFO, level))
    logging.getLogger("urllib3.connectionpool").setLevel(max(logging.INFO, level))
