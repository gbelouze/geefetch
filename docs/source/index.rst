..
    GeeFetch documentation master file, created by
    sphinx-quickstart on Wed Jun 12 20:59:36 2024.
    You can adapt this file completely to your liking, but it should at least
    contain the root `toctree` directive.

Welcome to GeeFetch's documentation!
====================================
.. raw:: html

   <img src="_static/logo.png" width="200px" style="float: left"/>

**GeeFetch** is a Python's library/CLI wrapper around geedim_ to download large scale
data from Google Earth Engine directly to your computer. It implements sane default for
some datasets from GEE's data catalog, and is easily extensible to support new
satellites.

.. note::

    This project is new and under active development. Its aim is to provide an easy,
    streamlined way to download all of the major datasets from GEE.

.. toctree::
    :maxdepth: 1

    installation
    cli
    api

API
===

.. autosummary::

    geefetch

.. _geedim: https://geedim.readthedocs.io/en/latest/

Indices and tables
==================

- :ref:`genindex`
- :ref:`modindex`
- :ref:`search`
