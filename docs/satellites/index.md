# Satellite Data Sources

GeeFetch provides access to a variety of satellite data sources through Google Earth Engine. This page offers an overview of all supported satellites and guides you in selecting the appropriate data source for your needs.

## Supported Satellites

GeeFetch supports the following satellite data sources, each accessible through a dedicated command:

| Satellite                    | Command    | Description                        | Resolution    | Main Applications                                           |
| ---------------------------- | ---------- | ---------------------------------- | ------------- | ----------------------------------------------------------- |
| [Sentinel-2](sentinel2.md)   | `s2`       | Multispectral optical imagery      | 10m, 20m, 60m | Vegetation monitoring, agriculture, land use classification |
| [Sentinel-1](sentinel1.md)   | `s1`       | Synthetic Aperture Radar (SAR)     | 10m-40m       | All-weather monitoring, flood mapping, sea ice tracking     |
| [Landsat-8](landsat8.md)     | `landsat8` | Multispectral optical imagery      | 15m-30m       | Long-term land change monitoring, broad area coverage       |
| [GEDI](gedi.md)              | `gedi`     | LiDAR-based forest structure       | 25m           | Forest canopy height, biomass estimation                    |
| [Dynamic World](dynworld.md) | `dynworld` | Land use/land cover classification | 10m           | Near real-time land cover mapping                           |
| [Palsar-2](palsar2.md)       | `palsar2`  | L-band SAR imagery                 | 10m-100m      | Forest monitoring, soil moisture, geology                   |
| [NASADEM](nasadem.md)        | `nasadem`  | Digital elevation model            | 30m           | Topography, hydrological modeling                           |
| [Custom](custom.md)          | `custom`   | Any GEE image collection           | Varies        | Custom data needs                                           |

## Choosing the Right Satellite Data

Selecting the appropriate satellite data depends on your specific application:

### For Vegetation and Agriculture

- **Sentinel-2**: High resolution optical imagery with specialized vegetation bands
- **Landsat-8**: Longer historical coverage with good spectral capabilities
- **Dynamic World**: Pre-classified land cover including crop and vegetation classes

### For All-Weather Monitoring

- **Sentinel-1**: C-band SAR that can penetrate clouds and operate day/night
- **Palsar-2**: L-band SAR with greater penetration capabilities for forests

### For Elevation and Terrain

- **NASADEM**: High-quality global elevation data

### For Forest Structure

- **GEDI**: Specialized LiDAR data for detailed forest structure measurements

### For Custom Applications

- **Custom**: Flexibility to access any image collection available in Google Earth Engine

## Custom Data Sources

The `custom` command provides access to any image collection available in Google Earth Engine without special processing steps beyond mosaicking. This allows you to leverage GeeFetch's downloading capabilities while accessing data sources not explicitly supported through dedicated commands.

```yaml
# Example custom configuration
custom:
  nrti:
    url: "COPERNICUS/S5P/NRTI/L3_NO2"
    selected_bands: ["NO2_column_number_density", "cloud_fraction"]
    pixel_range:
      NO2_column_number_density: [-0.0006, 0.0096]
      cloud_fraction: [0, 1]
```

See [Custom download](custom.md) for more details.

## Processing Overview

For each supported satellite, GeeFetch applies standardized preprocessing steps to ensure data quality and consistency. These typically include:

1. Filtering by date range and area of interest
2. Cloud masking (for optical sensors)
3. Mosaicking of multiple images
4. Resampling to target resolution
5. Scaling to maximize precision within the requested data type.

See the dedicated page for each satellite for detailed information on specific processing steps.

## Next Steps

- Review detailed specifications for specific satellites like [Sentinel-2](sentinel2.md)
- Learn about [configuration options](../configuration.md) to customize your downloads
- Explore [examples](../examples/index.md) showing how to use different satellite data
