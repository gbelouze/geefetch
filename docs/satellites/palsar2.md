# PALSAR-2

## Overview

PALSAR-2 is an L-band synthetic aperture radar (SAR) sensor onboard the ALOS-2 satellite operated by JAXA. It provides high-resolution, all-weather radar imagery suitable for vegetation structure analysis, forest monitoring, and land cover classification. Its longer wavelength enables deeper penetration into forest canopies compared to C-band SAR systems.

In GeeFetch, PALSAR-2 data is accessed via the Google Earth Engine collection [`JAXA/ALOS/PALSAR-2/Level2_2/ScanSAR`](https://developers.google.com/earth-engine/datasets/catalog/JAXA_ALOS_PALSAR-2_Level2_2_ScanSAR) (Level 2.2 orthorectified, terrain corrected).

## Processing

1. Filtering by date range and area of interest
2. Noise removal : 🚧 Documentation is under construction 🚧
3. Mosaicking of overlapping acquisitions
4. Resampling to target resolution
5. Scaling to maximize precision within the requested data type. Pixels outside the range $(0, 8000)$ saturate. For instance, if the requested datatype is `uint8`, the image is scaled by $255/8000$.

## Available Bands for download

| Band | Description                                                      | Native resolution | Download by default |
| ---- | ---------------------------------------------------------------- | ----------------- | ------------------- |
| HH   | Horizontal transmit, horizontal receive                          | 25m               | yes                 |
| HV   | Horizontal transmit, vertical receive                            | 25m               | yes                 |
| LIN  | Local incidence angle (between radar direction and slope normal) | 0.01 deg          | no                  |
| MSK  | Data quality bitmask                                             | 25m               | no                  |

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
palsar2:
  orbit: ASCENDING
```

then download with

```bash
geefetch palsar2 -c config.yaml
```

### Python API

Though this is not geefetch main intended use, you can bypass the configuration and directly download PALSAR-2 data with the following function.

::: geefetch.data.get.download_palsar2

    options:
        show_root_heading: true
        show_source: false
        heading_level: 5
        show_root_toc_entry: false

## Relevant library code

::: geefetch.data.satellites.Palsar2

    options:
        show_root_heading: true
