# Sentinel-2

## Overview

Sentinel-2 is a wide-swath, high-resolution, multi-spectral imaging mission supporting Copernicus Land Monitoring services. It provides optical imagery at 10m, 20m, and 60m resolution with a revisit time of 5 days at the equator.

In GeeFetch, Sentinel-2 data is accessed via the Google Earth Engine collection [`COPERNICUS/S2_SR`](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED) (Surface Reflectance).

## Processing

1. Filtering by date range and area of interest
2. Cloud masking using the [`COPERNICUS/S2_CLOUD_PROBABILITY`](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_CLOUD_PROBABILITY) product (see [configuration options](#configuration-options))  
   a. Remove images where `CLOUDY_PIXEL_PERCENTAGE > 100 - cloudless_portion`  
   b. Remove images where `HIGH_PROBA_CLOUDS_PERCENTAGE > 50 - cloudless_portion/2`  
   c. Mask pixels which have a probability of being a cloud `> cloud_prb_threshold`  
   d. Mask pixels based on the `QA60` band
3. Resampling to target resolution
4. Mosaicking of multiple images
5. Scaling to maximize precision within the requested data type. Pixels outside of the range $(0, 3000)$ saturate. For instance, if the requested datatype is `uint8`, the image is scaled by $255/3000$.

## Available Bands for download

| Band       | Description               | Native resolution | Download by default |
| ---------- | ------------------------- | ----------------- | ------------------- |
| B1         | Coastal aerosol           | 60m               | no                  |
| B2         | Blue                      | 10m               | yes                 |
| B3         | Green                     | 10m               | yes                 |
| B4         | Red                       | 10m               | yes                 |
| B5         | Red Edge 1                | 20m               | yes                 |
| B6         | Red Edge 2                | 20m               | yes                 |
| B7         | Red Edge 3                | 20m               | yes                 |
| B8         | NIR                       | 10m               | yes                 |
| B8A        | Narrow NIR                | 20m               | yes                 |
| B9         | Water vapor               | 60m               | no                  |
| B11        | SWIR 1                    | 20m               | yes                 |
| B12        | SWIR 2                    | 20m               | yes                 |
| QA60       | Cloud mask                | 60m               | no                  |
| AOT        | Aerosol Optical Thickness | 10m               | no                  |
| WVP        | Water Vapor Pressure      | 10m               | no                  |
| SCL        | Scene Classification      | 20m               | no                  |
| TCI_R      | True Color Red            | 10m               | no                  |
| TCI_G      | True Color Green          | 10m               | no                  |
| TCI_B      | True Color Blue           | 10m               | no                  |
| MSK_CLDPRB | Cloud Probability         | 20m               | no                  |

Refer to [`COPERNICUS/S2_SR`](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED) for more details.

## Configuration Options

See [common configuration options](../api/cli/configuration.md#geefetch.cli.omegaconfig.SatelliteDefaultConfig) for non Sentinel-2-specific configuration. Additionnally, you may provide the following options.

::: geefetch.cli.omegaconfig.S2Config

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
    ee_project_ids: ["your-gee-id"]
  tile_size: 2000
  resolution: 10
s2: # more scrict cloud filtering than the defaults
  cloudless_portion: 60
  cloud_prb_threshold: 20
```

then download with

```bash
geefetch s2 -c config.yaml
```

### Python API

Though this is not `geefetch` main intended use, you can bypass the configuration and directly download Sentinel-2 data with the `geefetch.data.get.download_s2` function.
For instance, the CLI command above is roughly equivalent to

```python
import logging
from pathlib import Path

from geobbox import GeoBoundingBox

from geefetch.data.get import download_s2
from geefetch.utils.gee import auth
from geefetch.utils.log import setup

setup(level=logging.INFO)

data_dir = Path("geefetch_data/")
data_dir.mkdir(exist_ok=True)

auth("your-gee-id")

download_s2(
    data_dir,
    bbox=GeoBoundingBox(2.2, 48.7, 2.5, 49),
    start_date="2023-06-01",
    end_date="2023-06-30",
    tile_shape=2000,
    cloudless_portion=60,
    cloud_prb_thresh=20,
)
```

See the API reference of [`geefetch.data.get.download_s2`](../api/core/get.md#geefetch.data.get.download_s2) for more details.

## Relevant library code

[`S2`](../api/satellites.md#geefetch.data.satellites.S2)  
[`geefetch.data.get.download_s2`](../api/core/get.md#geefetch.data.get.download_s2)
