from importlib import import_module

from ....utils.stack import get_module_and_name
from ....app import PyApp

from .font import QIconFont, IconCache  # noqa: F401
from .sources import THIRDPARTY_FONTSPEC  # noqa: F401
from .fontspec import ICON_ASSETS_DIR


def init_iconfonts(use_tmpdir: bool = True, do_import: bool = True):
    modparts = get_module_and_name()[1].split('.')
    thirdpartymod = f"{'.'.join(modparts[:-1]) + '.thirdparty'}"
    tmpdir = PyApp.mkdir_temp() if use_tmpdir else ICON_ASSETS_DIR
    for fontmod, fontspec in THIRDPARTY_FONTSPEC.items():
        fontspec.initialize(fontmod, tmpdir)
        relqualname = fontspec.relative_module_qualname
        if do_import:
            import_module(f'{thirdpartymod}.{relqualname}')
