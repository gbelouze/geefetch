"""This module provides the CLI for interacting with `geefetch`."""

from pathlib import Path

import click

config_option = click.option(
    "--config",
    "-c",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    default=Path("default.yaml"),
    help="Path to config file. See default.yaml for an overview of possible content.",
)


@click.group()
@click.option("-v", "--verbose", is_flag=True)
@click.option("--quiet/--no-quiet", default=False)
@click.option(
    "--logfile",
    type=click.Path(path_type=Path),
    default=None,
    help="File to output the log messages in addition to stdout/stderr.",
)
@click.option("--debug", is_flag=True)
def main(verbose, quiet, logfile, debug):
    """Download satellites from Google Earth Engine."""
    from .logging_implementation import logging_setup

    logging_setup(verbose, quiet, logfile, debug)


@main.command()
@config_option
def all(config):
    """Download all satellites given in the config."""
    from .download_implementation import download_all

    download_all(config)


@main.command()
@config_option
@click.option(
    "--vector/--no-vector",
    " /--raster",
    default=True,
    help="Whether to use vectorized or rasterized data points.",
)
def gedi(config, vector):
    """Download GEDI images."""
    from .download_implementation import download_gedi

    download_gedi(config, vector)


@main.command()
@config_option
def s1(config):
    """Download Sentinel-1 images."""
    from .download_implementation import download_s1

    download_s1(config)


@main.command()
@config_option
def s2(config):
    """Download Sentinel-2 images."""
    from .download_implementation import download_s2

    download_s2(config)


@main.command()
@config_option
def dynworld(config):
    """Download Dynamic World images."""
    from .download_implementation import download_dynworld

    download_dynworld(config)
