# Custom satellite source

## Overview

You can use Geefetch to download data collections that are not officially supported (see [Officially Supported Satellites](index.md)).
Do note however that while you will benefit from Geefetch downloading abilities, you will not get standardized, fine tuned data processing that you might have for supported satellites.
The configuration for custom satellite source is slightly more involved that for supported satellites, see [Configuration Options](#configuration-options).

## Processing

The processing for custom satellites is very generic and thus quite basic.

1. Selecting area of interest
2. Resampling to target resolution
3. Scaling to maximize precision within the requested data type. For instance, if the requested datatype is `uint8`, the image is scaled by $x \mapsto 255 \cdot \frac{x - \textrm{band_min}}{\textrm{band_max} - \textrm{band_min}}$.

## Configuration Options

See [common configuration options](../api/cli/configuration.md#geefetch.cli.omegaconfig.SatelliteDefaultConfig) for common configuration between all satellites. Additionnally, downloading from custom sources requires you to specify the following options.

::: geefetch.cli.omegaconfig.CustomSatelliteConfig

    options:
        show_source: false
        show_signature: false
        show_category_heading: false
        show_docstring_description: false
        show_bases: false
        show_root_toc_entry: false

## Example Usage

As an example, we show how to get a roughly similar behaviour as the builtin `geefetch nasadem` using custom satellite specifications. You can see that the [NASA-DEM processing](nasadem.md/#processing) is very basic, not unlike the processing of custom satellites.

### Using the CLI

Write the following `config.yaml`

```yaml
data_dir: geefetch_data
satellite_default:
  aoi:
    spatial:
      left: 2.2
      bottom: 48.7
      right: 2.5
      top: 49
      epsg: 4326
  gee:
    ee_project_ids: ["your-gee-id"]
  tile_size: 2000
  resolution: 10

customs:
  nasadem:
    url: NASA/NASADEM_HGT/001
    pixel_range: [-512, 8768]
    selected_bands: [elevation]
    composite_method: MOSAIC
```

then download with

```bash
geefetch custom nasadem -c config.yaml
```

### Using the Python API

Though this is not `geefetch` main intended use, you can bypass the configuration and directly download custom data with the `geefetch.data.get.download_custom` function.
For instance, the CLI command above is roughly equivalent to

```python
import logging
from pathlib import Path

from geobbox import GeoBoundingBox

from geefetch.data.get import download_custom
from geefetch.data.satellites import CustomSatellite
from geefetch.utils.enums import CompositeMethod
from geefetch.utils.gee import auth
from geefetch.utils.log import setup

setup(level=logging.INFO)

nasadem_custom = CustomSatellite(
    url="NASA/NASADEM_HGT/001", pixel_range=(-512, 8768), name="nasadem"
)

data_dir = Path("geefetch_data/")
data_dir.mkdir(exist_ok=True)

auth("your-gee-id")

download_custom(
    nasadem_custom,
    data_dir,
    bbox=GeoBoundingBox(2.2, 48.7, 2.5, 49),
    start_date=None,
    end_date=None,
    selected_bands=["elevation"],
    composite_method=CompositeMethod.MOSAIC,
    tile_shape=2000,
)
```

See the API reference of [`geefetch.data.get.download_custom`](../api/core/get.md#geefetch.data.get.download_custom) for more details.

## Relevant library code

[`CustomSatellite`](../api/satellites.md#geefetch.data.satellites.CustomSatellite)  
[`geefetch.data.get.download_custom`](../api/core/get.md#geefetch.data.get.download_custom)
