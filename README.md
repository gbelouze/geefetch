<!-- Do not remove the surrounding blank lines. See https://stackoverflow.com/questions/70292850/centre-align-shield-io-in-github-readme-file -->
<div align="center">

<a href="https://github.com/psf/black">![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)</a>
<a href="https://geefetch.readthedocs.io/en/latest/?badge=latest">![Documentation Status](https://readthedocs.org/projects/geefetch/badge/?version=latest)</a>

</div>

<p align="center">
    <img src="assets/logo-horizontal.png" alt="geefetch logo" style="width:70%; height:auto">
</p>


`geefetch` is a Python library and CLI designed to download large-scale satellite data from [Google Earth Engine](https://earthengine.google.com/) (GEE). It provides sensible defaults for various datasets available in GEE’s data catalog and is easily extensible to support additional satellites.

- **Simplified Data Access**: Retrieve satellite imagery directly to your local machine without extensive setup. Even over very large areas.
- **Command-Line Interface**: Convenient CLI for quick data downloads.
- **Python API**: Integrate geefetch functionalities into your Python applications.

## Supported Datasets

Currently, geefetch supports the following datasets:

- [Sentinel-1](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD)
- [Sentinel-2](https://developers.google.com/earth-engine/datasets/catalog/sentinel-2)
- [GEDI](https://developers.google.com/earth-engine/datasets/catalog/LARSE_GEDI_GEDI02_A_002_MONTHLY)
- [Dynamic World](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1)
- [Landsat-8](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T2_L2)
- [Palsar-2](https://developers.google.com/earth-engine/datasets/catalog/JAXA_ALOS_PALSAR-2_Level2_2_ScanSAR)
- [NASADEM](https://developers.google.com/earth-engine/datasets/catalog/NASA_NASADEM_HGT_001)

## Installation

`geefetch` requires Python 3.9 or higher. To install the library, ensure that [GDAL](https://gdal.org/) is available on your system. You can install GDAL using [conda](https://docs.conda.io/en/latest/):

```bash
conda install gdal
```

After installing GDAL, install `geefetch` via [PyPI](https://pypi.org/project/geefetch/):

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
