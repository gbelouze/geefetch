"""Google Earth Engine utilities."""

from functools import wraps

import ee
import requests.adapters

__all__ = ["auth"]

# Store original __init__ method
_original_init = requests.adapters.HTTPAdapter.__init__


@wraps(_original_init)
def patched_init(self, *args, **kwargs):
    if "pool_maxsize" not in kwargs and len(args) < 2:
        kwargs["pool_maxsize"] = 40  # your desired default
    return _original_init(self, *args, **kwargs)


# Monkey-patch it globally
requests.adapters.HTTPAdapter.__init__ = patched_init  # type: ignore[method-assign]


def auth(project: str) -> None:
    """Authentificate and initialize Google Earth Engine

    Parameters
    ----------
    project : str
        Google Earth Engine project id.
    """
    ee.Authenticate()
    ee.Initialize(
        project=project,
        opt_url="https://earthengine-highvolume.googleapis.com",
    )
