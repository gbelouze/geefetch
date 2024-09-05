Installation
============

Installation of the `Geefetch` package is complicated by its dependency on `rasterio`
which itself depends on `libgdal` and other C libraries. See
https://rasterio.readthedocs.io/en/stable/installation.html for more details on
installing rasterio.

Example with `conda`
--------------------

You must first ensure that `GDAL` is available on your system

.. code-block:: console

    conda install gdal

Then, install normally from PyPI

.. code-block:: console

    pip install geefetch

.. note::

    GeeFetch requires Rasterio 1.4 or higher, which requires Python 3.9 or higher and
    GDAL 3.3 or higher.

For developpers
---------------

If you want to work on `Geefetch`, clone the repository locally and optionally install
the `[doc]` and `[dev]` dependencies.

.. code-block:: console

    git clone git@github.com:gbelouze/geefetch.git
    cd geefetch
    conda env create -f environment.yml
    pip install -e '.[dev, doc]'

Adding autocompletion
---------------------

You can add autocompletion for the ``geefetch`` CLI, following `click's doc
<https://click.palletsprojects.com/en/8.1.x/shell-completion/>`__.

If you are using a ``conda`` environment, you need to activate autocompletion in that
environment only. Following the instructions in `the doc
<https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#macos-and-linux>`__,
add the following command to ``$CONDA_PREFIX/etc/conda/activate.d/env_vars.sh`` (adapt
for other shell than ``zsh``)

.. code-block:: bash

    eval "$(_GEEFETCH_COMPLETE=zsh_source geefetch)"
