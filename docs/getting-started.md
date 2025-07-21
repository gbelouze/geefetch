# Getting Started with GeeFetch

This guide will help you set up GeeFetch and run your first satellite data download.

## Prerequisites

### Python Environment

GeeFetch requires Python 3.8 or later. GeeFetch also requires `gdal` which depending on your installation method can be troublesome to install. You may refer to [rasterio installation page](https://rasterio.readthedocs.io/en/stable/installation.html) for more details.

### Google Earth Engine Authentication

GeeFetch uses Google Earth Engine to access satellite data. You'll need:

1. A Google account
2. Access to Google Earth Engine (sign up at [earthengine.google.com](https://earthengine.google.com/))

To authenticate with Earth Engine:

```bash
# Install the Earth Engine Python API
pip install earthengine-api

# Authenticate
earthengine authenticate
```

This will open a browser window and guide you through the authentication process.

## Installation

Install GeeFetch using `pip`, `conda` or with your prefered package manager:

=== "pip"

    ```bash
    pip install geefetch
    ```

=== "conda"

    If you have trouble with `gdal` or `rasterio`, you can use `conda` for a more out of the box install

    ```bash
    conda install "rasterio>=1.3" "gdal>=3.6"
    pip install geefetch
    ```

=== "dev"

    For development or the latest features, you can install directly from GitHub:

    ```bash
    pip install git+https://github.com/gbelouze/geefetch.git
    ```

## Basic Configuration

GeeFetch uses YAML configuration files to specify what data to download and how. Create a basic configuration file (e.g., `config.yaml`):

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
    ee_project_id: "my-ee-project" # Your GEE project ID
  tile_size: 2000
  resolution: 10
```

This configuration specifies:

- A storage location for downloaded data
- An area of interest (aoi) in southern France
- A time period for June 2023
- A tile size : the AOI will be split to download 2000 x 2000 rasters.

## Your First Download

Now you're ready to download your first dataset. Let's try Sentinel-2 imagery:

```bash
# Download Sentinel-2 data using our configuration
geefetch s2 -c config.yaml
```

This command will:

1. Connect to Google Earth Engine
2. Search for Sentinel-2 imagery matching your criteria (see [Sentinel-2](satellites/sentinel2.md) for more details on the Sentinel-2 processing)
3. Download the data to `~/satellite_data/s2`
4. Save metadata about the download for reproducibility in `~/satellite_data/s2/config.yaml`

## Checking the Results

After the download completes, you'll find the data in the directory specified in your configuration (`~/satellite_data` in our example):

```bash
~/satellite_data/
└── s2
    ├── config.yaml
    ├── s2_UTM30N.vrt
    ├── s2_UTM30N_680000_4840000.tif
    ├── s2_UTM30N_680000_4860000.tif
    ├── s2_UTM30N_680000_4880000.tif
    ├── s2_UTM30N_700000_4840000.tif
    ├── s2_UTM30N_700000_4860000.tif
    ├── s2_UTM30N_700000_4880000.tif
    ├── s2_UTM30N_720000_4840000.tif
    ├── s2_UTM30N_720000_4860000.tif
    └── s2_UTM30N_720000_4880000.tif
```

Each GeoTIFF file contains the requested satellite bands for a portion of your area of interest. A virtual raster file `.vrt` file has also been created
to include the whole aoi in a single file.

## Next Steps

Now that you've successfully downloaded your first dataset, you can:

- Explore different [satellite data sources](satellites/index.md)
- Learn about [advanced configuration options](configuration.md)
- See [example use cases](examples/index.md) for inspiration
- Automate downloads using the [Python API](api/index.md)
