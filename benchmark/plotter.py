import json
import logging
from pathlib import Path

import pandas as pd
import plotly.express as px

logger = logging.getLogger(__name__)


def load_logs(log_dir: str) -> pd.DataFrame:
    """
    Load all .jsonl logs from directory into a DataFrame.

    Parameters
    ----------
    log_dir : str
        Directory containing .jsonl benchmark logs.

    Returns
    -------
    pd.DataFrame
        Combined logs.
    """
    records = []
    for path in Path(log_dir).rglob("*.jsonl"):
        with path.open() as f:
            for line in f:
                records.append(json.loads(line))
    return pd.DataFrame.from_records(records)


def generate_all_plots(log_dir: str, out_dir: str):
    """
    Generate benchmark plots from logs.

    Parameters
    ----------
    log_dir : str
        Path to directory with .jsonl files.
    out_dir : str
        Path to output directory for SVG plots.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    df = load_logs(log_dir)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Duration over time per dataset
    fig = px.line(
        df,
        x="timestamp",
        y="duration_seconds",
        color="dataset",
        markers=True,
        title="Download Duration Over Time",
    )
    fig.write_image(str(out_path / "duration_vs_time.svg"))

    # Duration vs output size
    fig = px.scatter(
        df,
        x="output_size_mb",
        y="duration_seconds",
        color="dataset",
        title="Duration vs Output Size",
        hover_data=["file_count", "geefetch_version"],
    )
    fig.write_image(str(out_path / "duration_vs_size.svg"))

    # Duration vs geefetch version
    fig = px.box(
        df,
        x="geefetch_version",
        y="duration_seconds",
        color="dataset",
        points="all",
        title="Duration by geefetch Version",
    )
    fig.write_image(str(out_path / "duration_vs_version.svg"))

    logger.info(f"✅ Plots written to {out_path}")
