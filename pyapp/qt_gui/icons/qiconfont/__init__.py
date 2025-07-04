from importlib import import_module

from ....utils.system import get_current_module_and_name
from ....app import PyApp

from .font import QIconFont, IconCache  # noqa: F401
from .sources import THIRDPARTY_FONTSPEC  # noqa: F401
from .fontspec import ICON_ASSETS_DIR


def init_iconfonts(use_tmpdir: bool = True, do_import: bool = True):
    _, modname = get_current_module_and_name()
    modparts = modname.split('.')
    thirdpartymod = f"{'.'.join(modparts[:-1]) + '.thirdparty'}"
    tmpdir = PyApp.mkdir_temp() if use_tmpdir else ICON_ASSETS_DIR
    for fontmod, fontspec in THIRDPARTY_FONTSPEC.items():
        fontspec.initialize(fontmod, tmpdir)
        if do_import:
            import_module(f'{thirdpartymod}.{fontmod}')
