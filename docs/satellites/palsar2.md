# PALSAR-2

## Overview

PALSAR-2 is an L-band synthetic aperture radar (SAR) sensor onboard the ALOS-2 satellite operated by JAXA. It provides high-resolution, all-weather radar imagery suitable for vegetation structure analysis, forest monitoring, and land cover classification. Its longer wavelength enables deeper penetration into forest canopies compared to C-band SAR systems.

In GeeFetch, PALSAR-2 data is accessed via the Google Earth Engine collection [`JAXA/ALOS/PALSAR-2/Level2_2/ScanSAR`](https://developers.google.com/earth-engine/datasets/catalog/JAXA_ALOS_PALSAR-2_Level2_2_ScanSAR) (Level 2.2 orthorectified, terrain corrected).

## Processing

1. Filtering by date range and area of interest
2. Refined lee filter is applied to remove noise
3. Resampling to target resolution
4. Mosaicking of overlapping acquisitions
5. Scaling to maximize precision within the requested data type. Pixels outside of the range $(-30, 0)$ saturate. For instance, if the requested datatype is `uint8`, the image is scaled by $x \mapsto (x + 30) \cdot 255/30$.

## Available Bands for download

| Band | Description                                                      | Native resolution | Download by default |
| ---- | ---------------------------------------------------------------- | ----------------- | ------------------- |
| HH   | Horizontal transmit, horizontal receive (dB)                     | 25m               | yes                 |
| HV   | Horizontal transmit, vertical receive (dB)                       | 25m               | yes                 |
| LIN  | Local incidence angle (between radar direction and slope normal) | 0.01 deg          | no                  |
| MSK  | Data quality bitmask                                             | 25m               | no                  |

Refer to [`JAXA/ALOS/PALSAR-2/Level2_2/ScanSAR`](https://developers.google.com/earth-engine/datasets/catalog/JAXA_ALOS_PALSAR-2_Level2_2_ScanSAR) for more details.

## Configuration Options

See [common configuration options](../api/cli/configuration.md#geefetch.cli.omegaconfig.SatelliteDefaultConfig) for non PALSAR-2-specific configuration.

::: geefetch.cli.omegaconfig.Palsar2Config

    options:
        show_source: false
        show_signature: false
        show_category_heading: false
        show_docstring_description: false
        show_bases: false
        show_root_toc_entry: false

## Example Usage

### Command Line

Write the following `config.yaml`:

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
      start_date: "2024-06-01"
      end_date: "2024-06-30"
  gee:
    ee_project_ids: ["your-gee-id"]
  tile_size: 2000
  resolution: 10
palsar2:
  orbit: DESCENDING
  aoi:
    temporal:
      end_date: "2024-12-30"
```

then download with

```bash
geefetch palsar2 -c config.yaml
```

### Python API

Though this is not `geefetch` main intended use, you can bypass the configuration and directly download Palsar-2 data with the `geefetch.data.get.download_palsar2` function.
For instance, the CLI command above is roughly equivalent to

```python

import logging
from pathlib import Path

from geobbox import GeoBoundingBox

from geefetch.data.get import download_palsar2
from geefetch.utils.gee import auth
from geefetch.utils.log import setup

setup(level=logging.INFO)

data_dir = Path("geefetch_data/")
data_dir.mkdir(exist_ok=True)

auth("your-gee-id")

download_palsar2(
    data_dir,
    bbox=GeoBoundingBox(2.2, 48.7, 2.5, 49),
    start_date="2024-06-01",
    end_date="2024-12-30",
    tile_shape=2000,
)

```

See the API reference of [`geefetch.data.get.download_palsar2`](../api/core/get.md#geefetch.data.get.download_palsar2) for more details.

## Relevant library code

[`Palsar2`](../api/satellites.md#geefetch.data.satellites.Palsar2)  
[`geefetch.data.get.download_palsar2`](../api/core/get.md#geefetch.data.get.download_palsar2)
