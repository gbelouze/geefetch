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
geefetch nasadem -c config.yaml
```

### Python API

Though this is not `geefetch` main intended use, you can bypass the configuration and directly download NASA-DEM data with the following function.

::: geefetch.data.get.download_nasadem

    options:
        show_root_heading: true
        show_source: false
        heading_level: 5
        show_root_toc_entry: false

## Relevant library code

::: geefetch.data.satellites.NASADEM

    options:
        show_root_heading: true
