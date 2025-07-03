"""
This module ensures that the Qt resource file (icons.qrc) is compiled to a
Python module (icons_rc.py) at runtime if it is missing or out of date.
It should be imported before any Qt widgets are created.
"""
from subprocess import run, CalledProcessError
from pathlib import Path

from ..logging import log_func_call
from ..config.defaults import QT_ICON_PYFILE_KEY
from ..utils.constants import IS_WIN32
from ..utils.system import import_python_file
from ..app import PyApp

# Path to this file (qrc.py)
HERE = Path(__file__).parent
ICONS_DIR = HERE/"icons"
QRC_FILE = ICONS_DIR/"icons.qrc"
PY_FILENAME = "icons_rc.py"


@log_func_call
def compile_qrc():
    """Compile the Qt resource file if needed."""
    if not QRC_FILE.exists():
        raise FileNotFoundError(f"Resource file not found: {QRC_FILE}")

    tmpdir = PyApp.mkdir_temp()
    py_file = tmpdir/PY_FILENAME
    PyApp.set(QT_ICON_PYFILE_KEY, py_file)

    # Only recompile if .py is missing or older than .qrc
    if py_file.exists() and py_file.stat().st_mtime > QRC_FILE.stat().st_mtime:
        return  # Up to date

    # Try to find pyside2-rcc or pyrcc5
    rcc_cmds = [
        ["pyside2-rcc", str(QRC_FILE)],
        ["pyrcc5", str(QRC_FILE)],
    ]
    for cmd in rcc_cmds:
        try:
            # On Windows, need to add shell=True for .bat/.cmd
            result = run(cmd, capture_output=True, check=True, shell=IS_WIN32)
            if result.returncode == 0:
                py_file.write_bytes(result.stdout)
                return
        except (FileNotFoundError, CalledProcessError):
            continue
    raise RuntimeError(
        "Could not compile Qt resources. "
        "Please ensure 'pyside2-rcc' or 'pyrcc5' is installed and on PATH."
    )


@log_func_call
def import_qrc():
    # Import the generated resource module so resources are registered
    py_file: Path = PyApp[QT_ICON_PYFILE_KEY]
    try:
        mod = import_python_file(py_file, "pyapp.qt_gui.icons.icons_rc")
    except ImportError:
        mod = None

    if not mod:
        raise ImportError("Could not import compiled Qt resource module: "
                          f"{py_file}")
