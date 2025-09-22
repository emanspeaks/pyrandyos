"""
Compute the version number and store it in the `__version__` variable.

Based on <https://github.com/maresb/hatch-vcs-footgun-example>.
"""


def _get_hatch_version():
    """
    Compute the most up-to-date version number in a development environment.

    Returns `None` if Hatchling is not installed, e.g. in a prod environment.

    For more details, see:
    <https://github.com/maresb/hatch-vcs-footgun-example/>.
    """
    import os

    try:
        from hatchling.metadata.core import ProjectMetadata
        from hatchling.plugin.manager import PluginManager
        from hatchling.utils.fs import locate_file
        from hatchling.plugin.exceptions import UnknownPluginError
    except ImportError:
        # Hatchling is not installed, so probably we are not in
        # a development environment.
        return None

    pyproject_toml = locate_file(__file__, "pyproject.toml")
    if pyproject_toml:
        root = os.path.dirname(pyproject_toml)
        metadata = ProjectMetadata(root=root, plugin_manager=PluginManager())
        # can be either statically set in pyproject.toml
        # or computed dynamically:
        try:
            return metadata.core.version or metadata.hatch.version.cached
        except UnknownPluginError:
            return None

    # pyproject.toml not found although hatchling is installed
    return None


def _get_importlib_metadata_version():
    """Compute the version number using importlib.metadata.

    This is the official Pythonic way to get the version number of an installed
    package. However, it is only updated when a package is installed. Thus, if
    a package is installed in editable mode, and a different version is checked
    out, then the version number will not be updated.
    """
    from importlib.metadata import version, PackageNotFoundError

    try:
        __version__ = version(__package__)
    except PackageNotFoundError:
        # raise
        __version__ = None
    return __version__


__dynamic_version__ = _get_hatch_version() or _get_importlib_metadata_version()

try:
    from ._version import __version__  # pyright: ignore[reportMissingImports]
except (ModuleNotFoundError, ImportError):
    __version__ = __dynamic_version__
