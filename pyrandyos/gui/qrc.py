"""
This module ensures that the Qt resource file (resources.qrc) is compiled to a
Python module (qt_resources.py) at runtime if it is missing or out of date.
It should be imported before any Qt widgets are created.
"""
from subprocess import run, CalledProcessError
from pathlib import Path
from os import environ, pathsep

from ..logging import log_func_call
from ..config.keys import QRC_PYFILE_KEY, QRC_FILE_KEY
from ..utils.constants import IS_WIN32
from ..utils.system import import_python_file, get_conda_base_prefix
from ..app import PyRandyOSApp

HERE = Path(__file__).parent
PY_FILENAME = "qt_resources.py"
QT_RESOURCES_MODULE = f"{__name__}.resources"


@log_func_call
def compile_qrc(qrcfile: Path = None):
    """Compile the Qt resource file if needed."""
    if qrcfile:
        PyRandyOSApp.set(QRC_FILE_KEY, qrcfile)
    else:
        qrcfile: Path = qrcfile or PyRandyOSApp.get(QRC_FILE_KEY, None)

    if not qrcfile:
        return
    if qrcfile and not qrcfile.exists():
        raise FileNotFoundError(f"Resource file not found: {qrcfile}")

    tmpdir = PyRandyOSApp.mkdir_temp()
    py_file = tmpdir/PY_FILENAME
    PyRandyOSApp.set(QRC_PYFILE_KEY, py_file)

    # Only recompile if .py is missing or older than .qrc
    if py_file.exists() and py_file.stat().st_mtime > qrcfile.stat().st_mtime:
        return  # Up to date

    # Try to find pyside2-rcc or pyrcc5
    conda_path = get_conda_base_prefix()
    script_dir = conda_path/('Scripts' if IS_WIN32 else 'bin')
    bin_dir = conda_path/('Library/bin' if IS_WIN32 else 'bin')
    env = environ.copy()
    env['PATH'] = f"{bin_dir}{pathsep}{script_dir}{pathsep}{env['PATH']}"
    rcc_cmds = [
        ["pyside2-rcc", str(qrcfile)],
        ["pyrcc5", str(qrcfile)],
    ]
    for cmd in rcc_cmds:
        try:
            # On Windows, need to add shell=True for .bat/.cmd
            result = run(cmd, capture_output=True, check=True, shell=IS_WIN32,
                         env=env)
            if result.returncode == 0:
                py_file.write_bytes(result.stdout)
                return
        except (FileNotFoundError, CalledProcessError):
            continue
    raise RuntimeError(
        "Could not compile Qt resources. "
        "Please ensure 'pyside2-rcc' or 'pyrcc5' and 'rcc' "
        "are installed and on PATH."
    )


@log_func_call
def import_qrc():
    # Import the generated resource module so resources are registered
    qrcfile: Path = PyRandyOSApp.get(QRC_FILE_KEY, None)
    if not qrcfile:
        return
    py_file: Path = PyRandyOSApp.get(QRC_PYFILE_KEY, None)
    if not py_file or not py_file.exists():
        compile_qrc()

    try:
        mod = import_python_file(py_file, QT_RESOURCES_MODULE)
    except ImportError:
        mod = None

    if not mod:
        raise ImportError("Could not import compiled Qt resource module: "
                          f"{py_file}")
