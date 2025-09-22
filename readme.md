# PyRandyOS

Library of common functions for Python applications

[![GitHub Badge](https://img.shields.io/badge/GitHub-181717?logo=github&logoColor=fff&style=plastic)](https://github.com/emanspeaks/pyrandyos)
[![CI Status](https://github.com/emanspeaks/pyrandyos/actions/workflows/ci.yml/badge.svg)](https://github.com/emanspeaks/pyrandyos/actions)
[![last-commit](https://img.shields.io/github/last-commit/emanspeaks/pyrandyos)](https://github.com/emanspeaks/pyrandyos/commits/main)
[![PyPI Downloads](https://img.shields.io/pypi/dm/pyrandyos?label=PyPI%20downloads)](https://pypi.org/project/pyrandyos/)
<!-- [![Conda Downloads](https://img.shields.io/conda/dn/conda-forge/pyrandyos?label=Conda%20downloads)](https://anaconda.org/conda-forge/pyrandyos) -->

This library was created to assist with rapid prototyping of Qt GUIs and other
common functionality Randy needs on a day-to-day basis.

## Licenses

### Icons

This repo uses icons taken from other open source icon font libraries.  Links to their licensing info are maintained alongside the URLs for the icon fonts in [`pyrandyos/gui/icons/iconfont/sources.py`](pyrandyos/gui/icons/iconfont/sources.py), where the paths to the license files are with respect to the repo root at the given URL.  The license files are also included in the corresponding asset directories with the font files.

## Develop

### Automatic versioning

If you need to test features that require a version number prior to creating a tag, you can override the automatic versioning by creating a Python module `pyrandyos._version` that exports `__version__`.  When this file is absent or does not contain a `__version__` attribute, it reverts to dynamic versioning. Note that `hatchling build` automatically generates the `pyrandyos._version` module when the package is built, so versions deployed to PyPI should have the hardcoded versions via these files.  Similarly, though, if you are starting from a version of the package that has one of these hardcoded files, simply delete it to again go back to dynamic versioning.

Note that the dynamic versioning really only works when `hatchling` and `hatch-vcs` are installed.
If either of these packages are not installed, it attempts to read the version from the installed package metadata.
However, any value in `pyrandyos._version.__version__` will always override both of these.

When a pull request is opened against the main branch, this will trigger a push to test.pypi.org.  However, the GitHub Actions workflow is configured to publish only on `pull_request`, which checks out the git repo AFTER a temporary merge to main, so it has an extra merge commit in the history and increments the dev version by one when doing the Hatch build.  This means that the dev version on test.pypi.org may be a different dev number than what appears in a local repo when running `hatch version` or otherwise getting the dynamic version from the package in Python.
