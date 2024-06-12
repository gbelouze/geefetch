# `geefetch`

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A python library/CLI to download large scale satellite data from Google Earth Engine.


## Overview

This library is still in its early days and in active development. After installing `geefetch`, you can check the available commands with

```bash
geefetch --help
```

In its current state, `geefetch` allows you to download Sentinel-1, Sentinel-2, Dynamic World data as raster files, and GEDI data as raster or vector files. See `geefetch download --help`.

## Development

Install `geefetch` locally in editable mode

```bash
git clone https://github.com/gbelouze/geefetch.git
cd geefetch
pip install -e .
```
Be sure to read [CONTRIBUTING.md](/CONTRIBUTING.md) before making your first pull request.

### Adding autocompletion

You can add autocompletion for the `geefetch` CLI, following [`click` doc](https://click.palletsprojects.com/en/8.1.x/shell-completion/).

If you are using a `conda` environment, you need to activate autocompletion in that environment only. Following the instructions in [the doc](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#macos-and-linux), add the following command to `$CONDA_PREFIX/etc/conda/activate.d/env_vars.sh` (adapt for other shell than `zsh`)

```bash
eval "$(_GEEFETCH_COMPLETE=zsh_source geefetch)"
```
