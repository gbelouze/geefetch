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

See [common configuration options](../api/cli/configuration.md#geefetch.cli.omegaconfig.SatelliteDefaultConfig) for non Sentinel-1-specific configuration. Additionally, you may provide the following options.

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
    ee_project_ids: ["your-gee-id"]
  tile_size: 2000
  resolution: 10
s1:
  orbit: ASCENDING
  speckle_filter:
    framework: "MONO"
    filter_name: "BOXCAR"
    kernel_size: 3
    nr_of_images: 10
  terrain_normalization:
    flattening_model: "DIRECT"
    layover_shadow_buffer: 0
    dem: "USGS/SRTMGL1_003"
```

then download with

```bash
geefetch s1 -c config.yaml
```

### Terrain Normalization

S1 images can be preprocessed with terrain flattening algorithms. See the table below for the possible configurations.

| Parameter             | Type    | Accepted Values                    | Description                                           |
| --------------------- | ------- | ---------------------------------- | ----------------------------------------------------- |
| dem                   | string  | The GEE snippet of any DEM dataset | Digital elevation Model used for terrain corrections. |
| flattening_model      | string  | 'VOLUME', 'DIRECT'                 | The flattening model to be used.                      |
| layover_shadow_buffer | integer | $i\in\mathbb{N}$                   | Layover and shadow buffer distance.                   |

By default, **terrain normalization** will be implemented with the following configuration:

```yaml
terrain_normalization:
  model: "VOLUME"
  layover_shadow_buffer: 3
  dem: "USGS/SRTMGL1_003"
```

which is equivalent to passing `terrain_normalization: default`.

If you do not want any terrain normalization done you can explicitly deactivate it by setting the following:

```yaml
s1:
  terrain_normalization: null
```

More detail on the functions and conventions [here](https://github.com/LSCE-forest/gee_s1_processing/blob/main/doc/Terrain_Normalization.md).

### Speckle Filters

S1 images can be preprocessed with speckle filtering. See the table bellow for the possible configurations.

| Parameter    | Type    | Accepted Values                                          | Description                                                                                                                                     |
| ------------ | ------- | -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| framework    | string  | 'MONO', 'MULTI'                                          | Whether the speckle filter will be applied on a single image or to a temporal stack of images neighboring each image in the filtered collection |
| nr_of_images | integer | $i\in\mathbb{N}$                                         | The number of images to be used by the multi temporal speckle filter framework                                                                  |
| filter_name  | string  | 'BOXCAR', 'LEE', 'REFINED LEE', 'LEE SIGMA', 'GAMMA MAP' | The name of the speckle filter to use                                                                                                           |
| kernel_size  | integer | $i\in\mathbb{N}$, $i$ odd                     | Size of the kernel that will be used to convolve the images.                                                                                    |

By default, speckle filtering isn't applied. You can get baseline speckle filtering by passing `speckle_filter: default`, which is equivalent to

```yaml
s1:
  speckle_filter:
    framework: MONO
    filter_name: BOXCAR
    kernel_size: 3
    nr_of_images: 10
```

More details on the filters and conventions [here](https://github.com/LSCE-forest/gee_s1_processing/blob/main/doc/Speckle_Filters.md).

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
