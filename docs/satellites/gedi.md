# GEDI

## Overview

The Global Ecosystem Dynamics Investigation **GEDI** misson helps characterize ecosystem structure and dynamics such as canopy heights and plante area indices. It is attached to the ISS and collects data globally between 51.6° N and 51.6° S latitudes. It obtains it's metrics via 8 beams that collect metric at a **25 m/pixel** resolution.

The data collections contain sparse information relative to the aoi's you would work on.

In GeeFetch, GEDI data is accessed via the Google Earth Engine collections - [`LARSE/GEDI/GEDI02_A_002`](https://developers.google.com/earth-engine/datasets/catalog/LARSE_GEDI_GEDI02_A_002) for canopy top height metrics.
- [`LARSE/GEDI/GEDI02_B_002`](https://developers.google.com/earth-engine/datasets/catalog/LARSE_GEDI_GEDI02_B_002) for canopy cover vertical profile metrics.

## Processing

1. Filtering by date range and area of interest
2. Filtering out low quality data points

## Available Bands for download

### GEDI L2A

| Band| Description| Download by default |
| - | - | - |
|beam|Beam identifier|yes|
|degrade_flag| Flag indicating degraded state of pointing and/or positioning information.|yes|
| delta_time | Time delta since Jan 1 00:00 2018 |yes|
| digital_elevation_model | TanDEM-X elevation at GEDI footprint location|no|
| digital_elevation_model_srtm | SRTM elevation at GEDI footprint location|no|
| elev_highestreturn  | Elevation of highest detected return relative to reference ellipsoid|no|
| elev_lowestmode | Elevation of center of lowest mode relative to reference ellipsoid|no|
| elevation_bias_flag | Elevations potentially affected by 4bin (~60 cm) ranging error|yes|
| energy_total| Integrated counts in the return waveform relative to the mean noise level|yes|
| landsat_treecover| Tree cover in the year 2010, defined as canopy closure for all vegetation taller than 5 m in height as a percentage per output grid cell|no|
| landsat_water_persistence| Percent UMD GLAD Landsat observations with classified surface water|no|
| lat_highestreturn| Latitude of highest detected return|no|
| leaf_off_doy| GEDI 1 km EASE 2.0 grid leaf-off start day-of-year|no|
| leaf_off_flag   | GEDI 1 km EASE 2.0 grid flag|no|
| leaf_on_cycle   | Flag that indicates the vegetation growing cycle for leaf-on observations|no|
| leaf_on_doy| GEDI 1 km EASE 2.0 grid leaf-on start day-of-year|no|
| lon_highestreturn| Longitude of highest detected return|no|
| modis_nonvegetated  | Percent non-vegetated from MODIS MOD44B V6 data|no|
| modis_nonvegetated_sd   | Percent non-vegetated standard deviation from MODIS MOD44B V6 data|no|
| modis_treecover | Percent tree cover from MODIS MOD44B V6 data|yes|
| modis_treecover_sd  | Percent tree cover standard deviation from MODIS MOD44B V6 data|no|
| num_detectedmodes| Number of detected modes in rxwaveform|no|
| pft_class  | GEDI 1 km EASE 2.0 grid Plant Functional Type (PFT)|no|
| quality_flag| Flag indicating likely invalid waveform (1=valid, 0=invalid)|yes|
| region_class| GEDI 1 km EASE 2.0 grid world continental regions|no|
| selected_algorithm  | Identifier of algorithm selected as identifying the lowest non-noise mode|yes|
| selected_mode   | Identifier of mode selected as lowest non-noise mode|no|
| selected_mode_flag  | Flag indicating status of selected_mode|no|
| sensitivity| Maxmimum canopy cover that can be penetrated. Valid range is [0, 1]. Values outside of this range may be present but must be ignored. They represent noise and non-land surface waveforms.|yes|
| solar_azimuth   | The azimuth of the sun position vector from the laser bounce point position in the local ENU frame. The angle is measured from North and is positive towards East.|yes|
| solar_elevation | The elevation of the sun position vector from the laser bounce point position in the local ENU frame. The angle is measured from the East-North plane and is positive Up.  |yes|
| surface_flag| Indicates elev_lowestmode is within 300m of Digital Elevation Model (DEM) or Mean Sea Surface (MSS) elevation|no|
| urban_focal_window_size| The focal window size used to calculate urban_proportion. Values are 3 (3x3 pixel window size) or 5 (5x5 pixel window size).|no|
| urban_proportion| The percentage proportion of land area within a focal area surrounding each shot that is urban land cover.|no|
| orbit_number| Orbit number|yes|
| minor_frame_number  | Minor frame number 0-241|no|
| shot_number_within_beam | Shot number within beam|no|
| local_beam_azimuth  | Azimuth in radians of the unit pointing vector for the laser in the local ENU frame. The angle is measured from North and positive towards East.|no|
| local_beam_elevation||no|
|rh98|Relative height metrics at 98% (at this height, only 2% of the beam has been reflected, this value is often used as a proxy for canoupy height label)|yes|
|rh0-97 & 99-100|Relative height metrics at n%|no|


Refer to [`LARSE_GEDI_GEDI02_A_002_MONTHLY`](https://developers.google.com/earth-engine/datasets/catalog/LARSE_GEDI_GEDI02_A_002_MONTHLY#bands) for more details.

### GEDI L2B
| Band | Description | Download by default |
| - | - | - |
| algorithmrun_flag| The L2B algorithm is run if this flag is set to 1 indicating data have sufficient waveform fidelity for L2B to run.|no|
| beam | Beam number|yes|
| cover| Total canopy cover|no|
| degrade_flag| Flag indicating degraded state of pointing and/or positioning information. |yes|
| delta_time  | Transmit time of the shot, measured in seconds from the master_time_epoch since 2018-01-01|yes|
| fhd_normal  | Foliage Height Diversity|no|
| l2b_quality_flag | L2B quality flag|yes|
| local_beam_azimuth | Azimuth of the unit pointing vector for the laser in the local ENU frame measured from North and positive towards East.   |no|
| local_beam_elevation    | Elevation of the unit pointing vector for the laser in the local ENU frame measured from East-North plane and positive towards Up.    |no|
| pai| Total Plant Area Index |yes|
| pgap_theta  | Total Gap Probability (theta)|no|
| selected_l2a_algorithm  | Selected L2A algorithm setting|yes|
| selected_rg_algorithm   | Selected R (ground) algorithm|no|
| sensitivity | Maxmimum canopy cover that can be penetrated. Valid range is [0, 1]. Values outside of this range may be present but must be ignored. They represent noise and non-land surface waveforms.|yes|
| solar_azimuth    | The azimuth of the sun position vector from the laser bounce point position in the local ENU frame measured from North and is positive towards East.|yes|
| solar_elevation  | The elevation of the sun position vector from the laser bounce point position in the local ENU frame measured from the East-North plane and is positive Up.|yes|
| shot_number | Shot number, a unique identifier. This field has the format of OOOOOBBRRGNNNNNNNN, where: OOOOO: Orbit number BB: Beam number RR: Reserved for future use G: Sub-orbit granule number NNNNNNNN: Shot index|yes|
| shot_number_within_beam | Shot number within beam|no|
| cover_zn / $n\in[0,29]$| Cumulative canopy cover at bin n. There are 30 bins each of height 5 m|no|
| pai_zn / $n\in[0,29]$| Plante area index profile at bin n.|no|
| pavd_zn / $n\in[0,29]$| Plant Area Volume Density profile at bin n.|no|


## Configuration Options

See [common configuration options](../api/cli/configuration.md#geefetch.cli.omegaconfig.SatelliteDefaultConfig) for non Sentinel-2-specific configuration. Additionnally, you may provide the following options.

::: geefetch.cli.omegaconfig.GediL2BConfig/GediConfig

    options:
        format: PARQUET


## Example Usage

### Command Line

As it was added first, the command and configuration *gedi* corresponds to L2A data and gedi_2lb to 2LB. To avoid breaking any existing configuration files, it will be left as is for now.

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
gedi: # more scrict cloud filtering than the defaults
    selected_bands:
    - rh98
    format: PARQUET
gedi_l2b:
    selected_bands:
    - rh98
```
then download GEDI L2A with

```bash
geefetch gedi --vector -c config.yaml
```

The *vector* parameter indicates wheter you whish to download the data as vectors or rasters.

Download GEDI L2B with

```bash
geefetch gedi_l2b -c config.yaml
```

GEDI L2B only has a vector implementation. It therfore does not have any specific CLI parameters.

### Python API

Though this is not `geefetch` main intended use, you can bypass the configuration and directly download Sentinel-2 data with the `geefetch.data.get.download_s2` function.
For instance, the CLI command above is roughly equivalent to

```python
import logging
from pathlib import Path

from geobbox import GeoBoundingBox

from geefetch.data.get import download_gedi, download_gedi_vector, download_gedi_l2b_vector
from geefetch.utils.gee import auth
from geefetch.utils.log import setup

setup(level=logging.INFO)

data_dir = Path("geefetch_data/")
data_dir.mkdir(exist_ok=True)

auth("your-gee-id")

download_gedi(
    data_dir,
    bbox=GeoBoundingBox(2.2, 48.7, 2.5, 49),
    start_date="2023-06-01",
    end_date="2023-06-30",
    tile_shape=2000,
)
```

See the API reference of [`geefetch.data.get.download_gedi`](../api/core/get.md#geefetch.data.get.gedi) for more details.

## Relevant library code

[`GEDI L2A`](../../src/geefetch/data/satellites/gedi.py)

[`GEDI L2B`](../../src/geefetch/data/satellites/gedi_2lb.py)
