# Satellite Sources

GeeFetch provides pre-configured access to several satellite data sources from Google Earth Engine. This page documents the available satellite classes and their specific parameters.

## Blueprint

Every satellite must conform to the following blueprint.

::: geefetch.data.satellites.SatelliteABC

    options:
        show_root_heading: true
        show_source: false
        heading_level: 3

## Available Satellite Sources

::: geefetch.data.satellites

    options:
        members:
            - DynWorld
            - GEDIraster
            - GEDIvector
            - Landsat8
            - NASADEM
            - Palsar2
            - S1
            - S2
        show_root_heading: false
        show_source: false
        heading_level: 3

## Custom Satellite

For data sources that are not built-in into `geefetch`, we have the following more generic implementation - albeit without fine tuned preprocessing - to download from any Google Earth Engine `ImageCollection`


::: geefetch.data.satellites.CustomSatellite

    options:
        show_root_heading: true
        show_source: false
        heading_level: 4
