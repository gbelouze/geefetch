# CLI Configuration

GeeFetch uses a YAML-based configuration system to specify download parameters. This page documents all available configuration options.

## Common Configuration Schema

This is configuration that you specify once in the `default_satellite` section, and that will be merge to all satellite-specific configurations.

::: geefetch.cli.omegaconfig

    options:
        members:
            - SatelliteDefaultConfig
            - GEEConfig
            - AOIConfig
            - TemporalAOIConfig
            - SpatialAOIConfig
        show_root_heading: true
        show_root_toc_entry: false
        show_source: false
        heading_level: 2

## Satellite specific options

::: geefetch.cli.omegaconfig

    options:
        show_root_heading: false
        show_root_toc_entry: false
        show_source: false
        heading_level: 3
        filters:
            - "!.*"
            - "^.*Config$"
            - "!^SatelliteDefaultConfig$"
            - "!^GEEConfig$"
            - "!^AOIConfig$"
            - "!^TemporalAOIConfig$"
            - "!^SpatialAOIConfig$"
            - "!^GeefetchConfig$"

## Geefetch configuration

Tying it all together, the configuration for the `geefetch` application looks like this.

::: geefetch.cli.omegaconfig

    options:
        members: ["GeefetchConfig", "load"]
        show_root_heading: false
        show_root_toc_entry: false
        show_source: false
        heading_level: 3
