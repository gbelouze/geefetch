<!-- Do not remove the surrounding blank lines. See https://stackoverflow.com/questions/70292850/centre-align-shield-io-in-github-readme-file -->
<div align="center">

<a href="https://docs.astral.sh/ruff/">![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-D7FF63.svg)</a>
<a href="https://geefetch.readthedocs.io/en/latest/?badge=latest">![Documentation Status](https://readthedocs.org/projects/geefetch/badge/?version=latest)</a>

</div>

<p align="center">
    <img src="assets/logo-horizontal.png" alt="geefetch logo" style="width:70%; height:auto">
</p>


**GeeFetch** is a Python library and command-line tool for downloading large-scale satellite data from Google Earth Engine directly to your computer. Built as a higher-level wrapper around [geedim](https://geedim.readthedocs.io/en/latest/), GeeFetch focuses on reproducibility, scalability, and ease of use, especially for those who want to use satellite data without being remote sensing experts.

## Why GeeFetch?

- **Reproducible data acquisition** through a declarative configuration approach
- **Scalable downloads** for national or international coverage
- **Robust execution** resume your download after your internet went down
- **Pre-configured defaults** for popular satellite sources
- **Simple CLI** for straightforward data access without programming expertise

GeeFetch doesn't aim to be a general-purpose tool for crafting custom algorithms on Earth Engine data. Instead, it provides a streamlined way to get standardized satellite data that you can then use for your own applications, such as machine learning, deep learning, or other analytical workflows.

## Supported Datasets

Currently, geefetch supports the following datasets:

- [Sentinel-1](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD) (SAR imagery)
- [Sentinel-2](https://developers.google.com/earth-engine/datasets/catalog/sentinel-2) (multispectral imagery)
- [GEDI](https://developers.google.com/earth-engine/datasets/catalog/LARSE_GEDI_GEDI02_A_002_MONTHLY) (forest structure)
- [Dynamic World](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1) (land use/land cover)
- [Landsat-8](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T2_L2) (multispectral imagery)
- [Palsar-2](https://developers.google.com/earth-engine/datasets/catalog/JAXA_ALOS_PALSAR-2_Level2_2_ScanSAR) (SAR imagery)
- [NASADEM](https://developers.google.com/earth-engine/datasets/catalog/NASA_NASADEM_HGT_001) (elevation data)

## Installation

`geefetch` requires Python 3.9 or higher. To install the library, ensure that [GDAL](https://gdal.org/) is available on your system.
The simplest is to install GDAL using [conda](https://docs.conda.io/en/latest/):

```bash
conda install gdal
```

Once GDAL is available, install `geefetch` via [PyPI](https://pypi.org/project/geefetch/):

```bash
pip install geefetch
```

For developers interested in contributing or modifying `geefetch`, clone the repository and install the development dependencies:

```bash
git clone git@github.com:gbelouze/geefetch.git
cd geefetch
conda env create -f environment.yml
pip install -e '.[dev, doc]'
```

## Usage

```bash
$ geefetch --help
Usage: geefetch [OPTIONS] COMMAND [ARGS]...

  Download satellite data from Google Earth Engine.

Options:
  -v, --verbose
  --quiet / --no-quiet
  --logfile PATH        File to output the log messages in addition to
                        stdout/stderr.
  --debug
  --help                Show this message and exit.

Commands:
  all       Download all satellites given in the config.
  custom    Download Custom images.
  dynworld  Download Dynamic World images.
  gedi      Download GEDI images.
  landsat8  Download Landsat 8 images.
  nasadem   Download NASA-DEM images.
  palsar2   Download Palsar-2 images.
  s1        Download Sentinel-1 images.
  s2        Download Sentinel-2 images.
```

Read the [docs](https://geefetch.readthedocs.io/en/latest/) for more details.

## Contributing

Contributions are welcome! If you encounter issues or have suggestions for improvements, please open an issue or submit a pull request on the [GitHub repository](https://github.com/gbelouze/geefetch).

## License

This project is licensed under the BSD-2-Clause License. See the [LICENSE](https://github.com/gbelouze/geefetch/blob/main/LICENSE) file for more details.

# How to cite us ?

```
@misc{geefetch2025,
  author = {G. Belouze, D. Purnell, H. Rechatin},
  title = {GeeFetch},
  year = {2025},
  url = {https://github.com/gbelouze/geefetch},
  note = {v0.6.0}
}
```
