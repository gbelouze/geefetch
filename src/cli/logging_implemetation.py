import logging
from pathlib import Path

from geefetch.utils.log import setup

from . import debug as debug_flag

log = logging.getLogger(__name__)


def logging_setup(verbose: bool, quiet: bool, logfile: Path, debug: bool) -> None:
    level = logging.NOTSET
    if verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    if quiet:
        level = logging.ERROR
    if debug:
        level = logging.DEBUG
        debug_flag.DEBUG = True
    setup(level, logfile=logfile)
