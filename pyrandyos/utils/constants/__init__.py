import sys
from getpass import getuser

IS_WIN32 = sys.platform == "win32"

NODEFAULT = object()
"""
Sentinel constant to indicate no default value was given to a
`get()`-like function, such as `config_dict_get()`
"""

USER = getuser()
DEFAULT_GROUP = None if IS_WIN32 else USER
DEFAULT_DIR_MODE = 0o2750
DEFAULT_FILE_MODE = 0o640
