from importlib import import_module

from ....logging import log_func_call
from ....app import PyApp
from ...loadstatus import load_status_step

from .font import QIconFont, IconCache  # noqa: F401
from .sources import THIRDPARTY_FONTSPEC  # noqa: F401
from .fontspec import ICON_ASSETS_DIR


@load_status_step("Loading icon fonts")
@log_func_call
def init_iconfonts(use_tmpdir: bool = True, do_import: bool = True):
    thirdpartymod = f"{'.'.join(__name__.split('.')[:-1])}.thirdparty"
    tmpdir = PyApp.mkdir_temp() if use_tmpdir else ICON_ASSETS_DIR
    for fontmod, fontspec in THIRDPARTY_FONTSPEC.items():
        fontspec.initialize(fontmod, tmpdir)
        relqualname = fontspec.relative_module_qualname
        if do_import:
            import_module(f'{thirdpartymod}.{relqualname}')
