# Welcome to GeeFetch

<img src="assets/logo-horizontal-750px.png" width="500" style="margin-bottom: 20px"/>

**GeeFetch** is a Python library and command-line tool for downloading large-scale satellite data from Google Earth Engine directly to your computer. Built as a higher-level wrapper around [geedim](https://geedim.readthedocs.io/en/latest/), GeeFetch focuses on reproducibility, scalability, and ease of use, especially for those who want to use satellite data without being remote sensing experts.

## Why GeeFetch?

- **Reproducible data acquisition** through a declarative configuration approach
- **Scalable downloads** for national or international coverage
- **Robust execution** resume your download after your internet went down
- **Pre-configured defaults** for popular satellite sources
- **Simple CLI** for straightforward data access without programming expertise

GeeFetch doesn't aim to be a general-purpose tool for crafting custom algorithms on Earth Engine data. Instead, it provides a streamlined way to get standardized satellite data that you can then use for your own applications, such as machine learning, deep learning, or other analytical workflows.

## Supported Satellites

- [Sentinel-1](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD) (SAR imagery)
- [Sentinel-2](https://developers.google.com/earth-engine/datasets/catalog/sentinel-2) (multispectral imagery)
- [GEDI](https://developers.google.com/earth-engine/datasets/catalog/LARSE_GEDI_GEDI02_A_002_MONTHLY) (forest structure)
- [Dynamic World](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1) (land use/land cover)
- [Landsat-8](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T2_L2) (multispectral imagery)
- [Palsar-2](https://developers.google.com/earth-engine/datasets/catalog/JAXA_ALOS_PALSAR-2_Level2_2_ScanSAR) (SAR imagery)
- [NASADEM](https://developers.google.com/earth-engine/datasets/catalog/NASA_NASADEM_HGT_001) (elevation data)

## Basic Example

```bash
# Install geefetch
pip install geefetch

# Download Sentinel-2 imagery using a configuration file
geefetch s2 -c my_config.yaml
```

Configuration example (`my_config.yaml`), targetting an area around Les Landes, France:

```yaml
data_dir: ~/satellite_data
satellite_default:
  aoi:
    spatial:
      left: -0.7
      right: -0.2
      bottom: 43.8
      top: 44.2
      epsg: 4326
    temporal:
      start_date: "2023-06-01"
      end_date: "2023-08-31"
  gee:
    ee_project_ids: ["my-ee-project"]  # can be more to increase throughput
    max_tile_size: 10
  tile_size: 1000
  resolution: 10
s2:
  cloudless_portion: 40
  cloud_prb_threshold: 40
```

!!! note
    GeeFetch is currently under active development. New satellite datasets and features may be added in the near future.
