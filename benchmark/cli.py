import logging

import click


@click.group()
def cli():
    """Benchmarking utilities for geefetch."""
    from geefetch.utils.log import setup

    setup(level=logging.DEBUG)


@cli.command()
@click.argument("which", type=click.Choice(["all"], case_sensitive=False))
@click.option("--dry", is_flag=True, help="Don't actually run geefetch fetch, only simulate.")
@click.option(
    "--log-dir", type=click.Path(), default="benchmarks/history", help="Path to log directory."
)
def make(which: str, dry: bool, log_dir: str):
    """
    Run benchmark(s) and log results.
    """
    from runner import run_all_benchmarks

    run_all_benchmarks(log_dir=log_dir, dry=dry)


@cli.command()
@click.option(
    "--log-dir", type=click.Path(), default="benchmark/history", help="Path to log directory."
)
@click.option(
    "--out-dir",
    type=click.Path(),
    default="benchmarks/plots",
    help="Path to output plots directory.",
)
def plot(log_dir: str, out_dir: str):
    """
    Generate plots from benchmark logs.

    Parameters
    ----------
    log_dir : str
        Path to directory containing .jsonl benchmark logs.
    out_dir : str
        Directory to write plots to.
    """
    from plotter import generate_all_plots

    generate_all_plots(log_dir=log_dir, out_dir=out_dir)


if __name__ == "__main__":
    cli()
