# Sentinel-1

## Overview

Sentinel-1 is a C-band synthetic aperture radar (SAR) mission supporting Copernicus land and marine monitoring services. It provides all-weather, day-and-night radar imagery with a spatial resolution ranging from 5m to 40m and a revisit time of 6 to 12 days, depending on the location and acquisition mode.

In GeeFetch, Sentinel-1 data is accessed via the Google Earth Engine collection [`COPERNICUS/S1_GRD`](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD) (Ground Range Detected).

## Processing

1. Filtering by date range and area of interest
2. Filtering by orbit availability (see [configuration options](#configuration-options))
3. Resampling to target resolution
4. Mosaicking of overlapping acquisitions
5. Scaling to maximize precision within the requested data type. Pixels outside of the range $(-30, 0)$ saturate. For instance, if the requested datatype is `uint8`, the image is scaled by $x \mapsto (x + 30) \cdot 255/30$.

## Available Bands for download

| Band | Description                                  | Native resolution | Download by default |
| ---- | -------------------------------------------- | ----------------- | ------------------- |
| VV   | Vertical transmit, vertical receive (dB)     | 10m               | yes                 |
| VH   | Vertical transmit, horizontal receive (dB)   | 10m               | yes                 |
| HH   | Horizontal transmit, horizontal receive (dB) | 10m               | no                  |
| HV   | Horizontal transmit, vertical receive (dB)   | 10m               | no                  |

Refer to [`COPERNICUS/S1_GRD`](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD) for more details.

## Configuration Options

See [common configuration options](../api/cli/configuration.md#geefetch.cli.omegaconfig.SatelliteDefaultConfig) for non Sentinel-1-specific configuration. Additionnally, you may provide the following options.

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
      left: 2.2
      bottom: 48.7
      right: 2.5
      top: 49
      epsg: 4326
    temporal:
      start_date: "2023-06-01"
      end_date: "2023-06-30"
  gee:
    ee_project_id: "your-gee-id"
  tile_size: 2000
  resolution: 10
s1:
  orbit: ASCENDING
  speckle_filter_config:
        speckle_filter_framework: 'MONO'
        speckle_filter: 'BOXCAR'
        speckle_filter_kernel_size: 3
        speckle_filter_nr_of_images: 10
  terrain_normalization_config:
        terrain_flattening_model: 'DIRECT'
        dem: 'USGS/SRTMGL1_003'
        terrain_flattening_additional_layover_shadow_buffer: 0
```

then download with

```bash
geefetch s1 -c config.yaml
```

For more information on the [speckle_filter_config](https://github.com/LSCE-forest/gee_s1_processing/blob/main/doc/Speckle_Filters.md) and [terrain_normalization_config](https://github.com/LSCE-forest/gee_s1_processing/blob/main/doc/Terrain_Normalization.md).

### Python API

Though this is not `geefetch` main intended use, you can bypass the configuration and directly download Sentinel-1 data with the `geefetch.data.get.download_s1` function.
For instance, the CLI command above is roughly equivalent to

```python
import logging
from pathlib import Path

from geobbox import GeoBoundingBox

from geefetch.data.get import download_s1
from geefetch.utils.enums import S1Orbit
from geefetch.utils.gee import auth
from geefetch.utils.log import setup

setup(level=logging.INFO)

data_dir = Path("geefetch_data/")
data_dir.mkdir(exist_ok=True)

auth("your-gee-id")

download_s1(
    data_dir,
    bbox=GeoBoundingBox(2.2, 48.7, 2.5, 49),
    start_date="2023-06-01",
    end_date="2023-06-30",
    tile_shape=2000,
    orbit=S1Orbit.ASCENDING
)
```

See the API reference of [`geefetch.data.get.download_s1`](../api/core/get.md#geefetch.data.get.download_s1) for more details.

## Relevant library code

[`S1`](../api/satellites.md#geefetch.data.satellites.S1)  
[`geefetch.data.get.download_s1`](../api/core/get.md#geefetch.data.get.download_s1)
