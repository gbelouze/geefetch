# API Reference

This section provides detailed API documentation for GeeFetch, automatically generated from the library's docstrings.

## Package Structure

GeeFetch is organized into several key modules:

- [CLI Configuration](cli/configuration.md): Documentation for the YAML configuration options used with the command-line interface
- [Satellite Sources](satellites.md): Available satellite data sources and how to implement custom ones
- [Downloadable Classes](downloadables.md): Different classes that handle downloading from Google Earth Engine
- [Data Download Core](core/index.md): Main downloading functions
- [Geefetch Utils and Enums](utils.md): Utilities and useful enum types

## Getting Started with the API

If you're using GeeFetch as a Python library rather than through the CLI, start with the [`geefetch.data.get`](core/get.md) module, which provides the main entry points for data downloads.

To implement custom satellite sources, check out the [Custom Satellites](satellites.md#custom-satellite) documentation.
