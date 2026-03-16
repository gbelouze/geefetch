import os
import platform
import shutil
import subprocess
from pathlib import Path

import geefetch

GEE_PROJECT_ID_ENV_NAME = "GEEFETCH_GEE_PROJECT_ID"


def get_geefetch_version() -> str:
    """
    Return geefetch library version.

    Returns
    -------
    str
        Version string.
    """
    return geefetch.__version__


def get_git_commit() -> str:
    """
    Return current git commit hash.

    Returns
    -------
    str
        Git commit hash.
    """
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        return "unknown"


def get_system_info() -> dict:
    """
    Collect basic system info.

    Returns
    -------
    dict
        Contains CPU, RAM, and OS information.
    """
    return {
        "system": platform.system(),
        "platform": platform.platform(),
        "cpu": platform.processor(),
        "ram_gb": round(shutil.disk_usage("/").total / 1e9, 1),
    }


def get_output_stats(output_path: Path) -> dict:
    """
    Return number of files and total size of benchmark output.

    Parameters
    ----------
    output_path : Path
        Path to output directory or root.

    Returns
    -------
    dict
        file_count, total_size_mb.
    """
    if not output_path.exists():
        return {"file_count": 0, "output_size_mb": 0.0}

    files = list(output_path.rglob("*.tif"))
    total_bytes = sum(f.stat().st_size for f in files)

    return {
        "file_count": len(files),
        "output_size_mb": round(total_bytes / 1e6, 2),
    }


def get_gee_project_id() -> str:
    match os.getenv(GEE_PROJECT_ID_ENV_NAME):
        case None:
            raise RuntimeError(
                f"Did not find {GEE_PROJECT_ID_ENV_NAME} in the environment. "
                "Cannot query Google Earth Engine."
            )
        case _ as project_id:
            assert isinstance(project_id, str)
            return project_id
