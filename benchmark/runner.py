import json
import logging
import tempfile
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from omegaconf import DictConfig, OmegaConf
from utils import (
    get_gee_project_id,
    get_geefetch_version,
    get_git_commit,
    get_output_stats,
    get_system_info,
)

from geefetch.cli.download_implementation import download_gedi, download_s1, download_s2

logger = logging.getLogger(__name__)


class BenchmarkConfigs:
    BASECONFIG_PATH = Path(__file__).parent / "config.yaml"

    @classmethod
    def base(cls) -> DictConfig:
        conf = OmegaConf.load(BenchmarkConfigs.BASECONFIG_PATH)
        gee_id = get_gee_project_id()
        conf.satellite_default.gee.ee_project_id = gee_id
        return conf

    @classmethod
    def s1mosaic(cls) -> DictConfig:
        conf = cls.base()
        conf.s1.composite_method = "MEAN"
        return conf

    @classmethod
    def s1timeseries(cls) -> DictConfig:
        conf = cls.base()
        conf.s1.composite_method = "TIME_SERIES"
        return conf

    @classmethod
    def s2mosaic(cls) -> DictConfig:
        conf = cls.base()
        conf.s2.composite_method = "MEDIAN"
        return conf

    @classmethod
    def s2timeseries(cls) -> DictConfig:
        conf = cls.base()
        conf.s2.composite_method = "TIME_SERIES"
        return conf


# Each benchmark: (config path, label, function to infer output directory)
BENCHMARKS: list[tuple[str, Callable[[], DictConfig], Callable[[Path], None]]] = [
    ("Sentinel-1-mosaic", BenchmarkConfigs.s1mosaic, download_s1),
    ("Sentinel-1-series", BenchmarkConfigs.s1timeseries, download_s1),
    ("Sentinel-2-mosaic", BenchmarkConfigs.s2mosaic, download_s2),
    ("Sentinel-2-series", BenchmarkConfigs.s2timeseries, download_s2),
    (
        "GEDI-table",
        lambda: None,
        lambda path: download_gedi(path, vector=True),
    ),
]


def run_all_benchmarks(log_dir: str, dry: bool = False):
    """
    Run all configured benchmarks and write logs to disk.

    Parameters
    ----------
    log_dir : str
        Path to directory where logs will be saved.
    dry : bool
        If True, skip actual geefetch call.
    """
    log_root = Path(log_dir)
    log_root.mkdir(parents=True, exist_ok=True)

    for label, get_config, download_func in BENCHMARKS:
        logger.info(f"\n🛰️  Running benchmark for {label}...")
        config = get_config()
        with tempfile.TemporaryDirectory() as data_dir:
            config.data_dir = str(data_dir)
            data_dir = Path(data_dir)
            config_path = data_dir / "config.yaml"
            config_path.write_text(OmegaConf.to_yaml(config))

            if not dry:
                try:
                    timestamp = datetime.now(timezone.utc).isoformat()
                    start_time = time.time()
                    download_func(config_path)
                    end_time = time.time()
                    duration = round(end_time - start_time, 1)

                    log: dict = {
                        "timestamp": timestamp,
                        "dataset": label,
                        "geefetch_version": get_geefetch_version(),
                        "git_commit": get_git_commit(),
                        "config_file": config_path,
                        "duration_seconds": duration,
                    }
                    log.update(get_system_info())
                    log.update(get_output_stats(data_dir))

                    log_path = log_root / f"{timestamp}_{label.replace(' ', '_')}.jsonl"
                    with log_path.open("w") as f:
                        f.write(json.dumps(log) + "\n")

                    logger.info(f"✅ Benchmark complete in {duration}s. Log saved to {log_path}")
                    breakpoint()

                except Exception as e:
                    logger.error(f"❌ Benchmark failed for {label}: {e}")
                    continue
            else:
                logger.info("[DRY RUN] Skipping geefetch call")
