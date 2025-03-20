# Sentinel-1

## Overview

Sentinel-1 is a C-band synthetic aperture radar (SAR) mission supporting Copernicus land and marine monitoring services. It provides all-weather, day-and-night radar imagery with a spatial resolution ranging from 5m to 40m and a revisit time of 6 to 12 days, depending on the location and acquisition mode.

In GeeFetch, Sentinel-1 data is accessed via the Google Earth Engine collection [`COPERNICUS/S1_GRD`](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD) (Ground Range Detected).

## Processing

1. Filtering by date range and area of interest
2. Filtering by orbit availability (see [configuration options](#configuration-options))
3. Mosaicking of multiple images
4. Resampling to target resolution
5. Scaling to maximize precision within the requested data type. Pixels outside of the range $(-30, 0)$ saturate. For instance, if the requested datatype is `uint8`, the image is scaled by $x \mapsto (x + 30) \cdot 255/30$.

## Available Bands for download

| Band | Description                             | Native resolution | Download by default |
| ---- | --------------------------------------- | ----------------- | ------------------- |
| VV   | Vertical transmit, vertical receive     | 10m               | yes                 |
| VH   | Vertical transmit, horizontal receive   | 10m               | yes                 |
| HH   | Horizontal transmit, horizontal receive | 10m               | no                  |
| HV   | Horizontal transmit, vertical receive   | 10m               | no                  |

## Configuration Options

See [common configuration options](/api/config#geefetch.cli.omegaconfig.SatelliteDefaultConfig) for non Sentinel-1-specific configuration. Additionnally, you may provide the following options.

::: geefetch.cli.omegaconfig.S1Config

    options:
        show_source: false
        show_signature: false
        show_category_heading: false
        show_docstring_description: false
        show_bases: false
        show_root_toc_entry: false

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
    ee_project_id: "ffb-pipeline" # Your GEE project ID
  tile_size: 2000
  resolution: 10
s1: # more scrict cloud filtering than the defaults
  orbit: ASCENDING
```

then download with

```bash
geefetch s1 -c config.yaml
```

### Python API

Though this is not `geefetch` main intended use, you can bypass the configuration and directly download Sentinel-1 data with the following function.

::: geefetch.data.get.download_s1

    options:
        show_root_heading: true
        show_source: false
        heading_level: 5
        show_root_toc_entry: false

## Relevant library code

::: geefetch.data.satellites.S1

    options:
        show_root_heading: true
