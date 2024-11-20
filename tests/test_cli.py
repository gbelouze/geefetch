import logging
from pathlib import Path

from click.testing import CliRunner

from geefetch.cli.main import main

log = logging.getLogger("geefetch")


TESTS_DIR = Path(__file__).parent


def test_api_consistency():
    runner = CliRunner()

    res = runner.invoke(main, ["--help"])
    assert res.exit_code == 0
    assert res.output == (TESTS_DIR / "data" / "cli_help.txt").read_text()

    res = runner.invoke(main, ["all", "--help"])
    assert res.exit_code == 0
    assert res.output == (TESTS_DIR / "data" / "cli_all_help.txt").read_text()


def test_fail_on_missing_config():
    runner = CliRunner(mix_stderr=False)
    results = [
        runner.invoke(main, [satellite, "--config", "fakeconfig.yaml"])
        for satellite in ["s1", "s2", "palsar2", "gedi", "dynworld", "landsat8"]
    ]
    for res in results:
        assert res.exit_code == 2
        assert (
            "Error: Invalid value for '--config' / '-c': Path 'fakeconfig.yaml' does not exist."
            in res.stderr
        )
