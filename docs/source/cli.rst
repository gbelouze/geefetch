Command Line User Guide
=======================

Geefetch's command line interface (CLI) is a program named "geefetch" .

The CLI plugs into the downloading utilities of Geefetch. It includes a rich
configuration system that allows you to share configurations to download different
satellites. See :ref:`config format`

The `geefetch` program is developed using the `Click
<http://click.palletsprojects.com/>`__ framework. Its plugin system allows external
modules to share a common namespace and handling of context variables.

.. _config format:

Configuration
-------------

Here is an example config given to the command `geefetch [satellite] --config config.yaml`

.. code-block:: yaml

    data_dir: /path/to/datadir  # where the data is donwwloaded
    satellite_default:
      resolution: 10
      tile_size: 5_000  # the side length, in pixel, of downloaded rasters
      dtype: Float32
      composite_method: MEDIAN  # see geefetch.utils.enums.CompositeMethod
      aoi:
        spatial:
          left: 0
          right: 1
          bottom: 0
          top: 1
          epsg: 4326  # the CRS in which the AOI is expressed
        temporal:
          start_date: 2020-01-01
          end_date: 2020-01-31
        country: France  # optional country name to further refine AOI.
      gee:
        ee_project_id: ee-project-id # add your Earth Engine project id here.
        max_tile_size: 8 # in MB, decrease if User Memory Excess Error, choose highest possible otherwise.
    s1:
      composite_method: MEAN
    s2: {} # use satellite_default
    dynworld:
      composite_method: ${s1.composite_method}
    palsar2: {}

The config has

- A `satellite_default` section which configures the default download option for any
  satellites
- A section by satellite that you wish to download, amending the default options when
  necessary, or adding some satellite-specific configuration. See :ref:`cli options` for the list of supported satellites.

  - You can use config interpolation as is done for `dynworld.composite_method`.
  - You can use an empty section `{}` to use the defaults, as is done for `s2`

.. note::

    `satellite.gee.ee_project_id` is your Google Earth Engine project ID, used to
    connect to the GEE API. This is the string that you give to `ee.Initialize
    <https://developers.google.com/earth-engine/apidocs/ee-initialize>`__.

Usage
-----

.. _cli options:

.. click:: geefetch.cli:main
    :prog: geefetch
    :nested: short
