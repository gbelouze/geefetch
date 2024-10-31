<!-- Do not remove the surrounding blank lines. See https://stackoverflow.com/questions/70292850/centre-align-shield-io-in-github-readme-file -->
<div align="center">

  <a href="https://github.com/psf/black">![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)</a>
  <a href="https://geefetch.readthedocs.io/en/latest/?badge=latest">![Documentation Status](https://readthedocs.org/projects/geefetch/badge/?version=latest)</a>

</div>

<p align="center">
    <img src="assets/logo-horizontal.png" alt="Alt Text" style="width:70%; height:auto">
</p>

A python library/CLI to download large scale satellite data from Google Earth Engine.

[![CLI demo](https://asciinema.org)](https://asciinema.org/a/1xT8v4UGXCNOPbKjluYun9Vu4)

⚠️ This library is still in its early days and in active development. ⚠️

## Overview

```bash
$ geefetch --help
Usage: geefetch [OPTIONS] COMMAND [ARGS]...

  Download satellites from Google Earth Engine.

Options:
  -v, --verbose
  --quiet / --no-quiet
  --logfile PATH        File to output the log messages in addition to
                        stdout/stderr.
  --debug
  --help                Show this message and exit.

Commands:
  all       Download all satellites given in the config.
  dynworld  Download Dynamic World images.
  gedi      Download GEDI images.
  s1        Download Sentinel-1 images.
  s2        Download Sentinel-2 images.
  landsat8  Download Landsat-8 images.
  palsar2   Download Palsar-2 images.
```

Currently are supported

- [Sentinel-1](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD)
- [Sentinel-2](https://developers.google.com/earth-engine/datasets/catalog/sentinel-2)
- [GEDI](https://developers.google.com/earth-engine/datasets/catalog/LARSE_GEDI_GEDI02_A_002_MONTHLY)
- [Dynamic World](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1)
- [Landsat-8](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T2_L2)
- [Palsar-2](https://developers.google.com/earth-engine/datasets/catalog/JAXA_ALOS_PALSAR_YEARLY_SAR_EPOCH)

Read the [docs](https://geefetch.readthedocs.io/en/latest/) for more details.
