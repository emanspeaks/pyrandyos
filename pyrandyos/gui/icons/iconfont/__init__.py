from ....logging import log_func_call
from ....app import PyRandyOSApp
from ...loadstatus import load_status_step

from .font import IconFont  # noqa: F401
from .sources import THIRDPARTY_FONTSPEC  # noqa: F401
from .fontspec import ICON_ASSETS_DIR
from .icon import IconSpec, IconStateSpec, IconLayer  # noqa: F401


@load_status_step("Loading icon fonts")
@log_func_call
def init_iconfonts(use_tmpdir: bool = True, do_import: bool = True):
    tmpdir = PyRandyOSApp.mkdir_temp() if use_tmpdir else ICON_ASSETS_DIR
    for fontmod, fontspec in THIRDPARTY_FONTSPEC.items():
        fontspec.initialize(fontmod, tmpdir)
        if do_import:
            fontspec.import_font()
