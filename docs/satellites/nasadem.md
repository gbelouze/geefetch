# NASA-DEM

## Overview

NASADEM is a global digital elevation model (DEM) developed by NASA, derived from the NASA’s Earth Science Division’s Operation IceBridge and other satellite-based observations. It provides high-resolution topographic data with a spatial resolution of approximately 30 meters, offering valuable elevation data for a variety of scientific and environmental applications.

In GeeFetch, NASADEM data is accessed via the Google Earth Engine collection [`NASA/NASADEM_HGT/001`](https://developers.google.com/earth-engine/datasets/catalog/NASA_NASADEM_HGT_001).

## Processing

1. Selecting area of interest
2. Resampling to target resolution
3. Scaling to maximize precision within the requested data type. For instance, if the requested datatype is `uint8`, the image is scaled by $x \mapsto 255 \cdot \frac{x - \textrm{band_min}}{\textrm{band_max} - \textrm{band_min}}$.

## Available Bands for download

| Band      | Description                                   | Native resolution | Range        | Download by default |
| --------- | --------------------------------------------- | ----------------- | ------------ | ------------------- |
| elevation | Elevation in meters (EGM96 geoid)             | 30m               | -512 to 8768 | yes                 |
| slope     | Terrain slope in degrees                      | 30m               | 0 to 90      | yes                 |
| swb       | Surface water body mask (0: land, 255: water) | 30m               | 0 to 255     | no                  |

Refer to [`NASA/NASADEM_HGT/001`](https://developers.google.com/earth-engine/datasets/catalog/NASA_NASADEM_HGT_001) for more details.

## Configuration Options

See [common configuration options](../api/cli/configuration.md#geefetch.cli.omegaconfig.SatelliteDefaultConfig)

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
nasadem:
  aoi:
    temporal: null
```

then download with

```bash
geefetch nasadem -c config.yaml
```

### Python API

Though this is not `geefetch` main intended use, you can bypass the configuration and directly download NASA-DEM data with the `geefetch.data.get.download_nasadem` function.
For instance, the CLI command above is roughly equivalent to

```python

import logging
from pathlib import Path

from geobbox import GeoBoundingBox

from geefetch.data.get import download_nasadem
from geefetch.utils.gee import auth
from geefetch.utils.log import setup

setup(level=logging.INFO)

data_dir = Path("geefetch_data/")
data_dir.mkdir(exist_ok=True)

auth("your-gee-id")

download_nasadem(
    data_dir,
    bbox=GeoBoundingBox(2.2, 48.7, 2.5, 49),
    tile_shape=2000,
)

```

See the API reference of [`geefetch.data.get.download_nasadem`](../api/core/get.md#geefetch.data.get.download_nasadem) for more details.

## Relevant library code

[`NASADEM`](../api/satellites.md#geefetch.data.satellites.NASADEM)  
[`geefetch.data.get.download_nasadem`](../api/core/get.md#geefetch.data.get.download_nasadem)
