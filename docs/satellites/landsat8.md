# Landsat-8

## Overview

Landsat-8 is part of the Landsat program jointly operated by NASA and the USGS. It carries two instruments: the Operational Land Imager (OLI) and the Thermal Infrared Sensor (TIRS), which together provide multispectral and thermal imagery for land monitoring. With a spatial resolution of 30 meters for most bands and a 16-day revisit cycle, Landsat-8 is widely used for vegetation analysis, land cover classification, and environmental monitoring.

In GeeFetch, Landsat-8 data is accessed via the Google Earth Engine collection [`LANDSAT/LC08/C02/T1_L2`](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2), which provides Collection 2, Tier 1 Level-2 surface reflectance and surface temperature products.

## Processing

1.  Filtering by date range and area of interest
2.  Cloud and saturated pixels masking using the QA_PIXEL and QA_RADSAT bands.
3.  Bidirectional Reflectance Distribution Function (BRDF) correction: adjust radiometric values to account for variations in surface reflectance based on the sun and view angles.
4.  Mosaicking of overlapping acquisitions
5.  Resampling to target resolution
6.  Scaling to maximize precision with the requested data type. Pixels outside the range $(0, 65455)$ are saturated. For example, when the requested datatype is `uint8`, the image is scaled by $255/2^{16}$.

## Available Bands for download

| Band  | Description                                          | Native resolution | Download by default |
| ----- | ---------------------------------------------------- | ----------------- | ------------------- |
| SR_B1 | Band 1 (Ultra Blue, Coastal Aerosol, 0.435–0.451 µm) | 30m               | no                  |
| SR_B2 | Band 2 (Blue, 0.452–0.512 µm)                        | 30m               | yes                 |
| SR_B3 | Band 3 (Green, 0.533–0.590 µm)                       | 30m               | yes                 |
| SR_B4 | Band 4 (Red, 0.636–0.673 µm)                         | 30m               | yes                 |
| SR_B5 | Band 5 (Near-Infrared, 0.851–0.879 µm)               | 30m               | yes                 |
| SR_B6 | Band 6 (Shortwave Infrared 1, 1.566–1.651 µm)        | 30m               | yes                 |
| SR_B7 | Band 7 (Shortwave Infrared 2, 2.107–2.294 µm)        | 30m               | yes                 |

## Configuration Options

See [common configuration options](../api/cli/configuration.md#geefetch.cli.omegaconfig.SatelliteDefaultConfig).

## Example Usage

### Command Line

Write the following `config.yaml`

```yaml
data_dir: ~/satellite_data
satellite_default:
  aoi:
    spatial:
      left: -0.7
      right: -0.2
      top: 44.2
      bottom: 43.8
      epsg: 4326
    temporal:
      start_date: "2023-06-01"
      end_date: "2023-06-30"
  gee:
    ee_project_id: "your-gee-id"
  tile_size: 2000
  resolution: 10
```

then download with

```bash
geefetch landsat8 -c config.yaml
```

### Python API

Though this is not `geefetch` main intended use, you can bypass the configuration and directly download Landsat-8 data with the following function.

::: geefetch.data.get.download_landsat8

    options:
        show_root_heading: true
        show_source: false
        heading_level: 5
        show_root_toc_entry: false

## Relevant library code

::: geefetch.data.satellites.Landsat8

    options:
        show_root_heading: true
