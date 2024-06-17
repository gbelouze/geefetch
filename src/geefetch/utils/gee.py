"""Google Earth Engine utilities."""

import ee


def auth(project: str) -> None:
    """Authentificate and initialize Google Earth Engine

    Parameters
    ----------
    project : str
        Google Earth Engine project id.
    """
    ee.Authenticate(auth_mode="appdefault")
    ee.Initialize(
        project=project,
        opt_url="https://earthengine-highvolume.googleapis.com",
    )
