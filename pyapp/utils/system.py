# This module contains functions that interact either with the operating system
# the Python interpreter, or conda environments.
# The reason for some of the "nolog" equivalent versions of these functions can
# be found in the comments in the `nolog_system` module.

import sys
from os import system as os_sys, environ
from pathlib import Path
# from importlib.util import find_spec
from inspect import getfile, getmodule, stack
from importlib import import_module

from ..logging import get_logger

from .constants import (
    DEFAULT_GROUP, DEFAULT_DIR_MODE, DEFAULT_FILE_MODE, IS_WIN32,
)
from .notebook import is_notebook
from .paths import expand_and_check_var_path
from .nolog_system import (
    nolog_mkdir_chgrp, nolog_chmod_chgrp, nolog_file_copy_chmod_chgrp,
    nolog_import_python_file, nolog_add_path_to_syspath,
    nolog_build_cmd_arg_dict, nolog_build_cmd_arg_list,
)


def mkdir_chgrp(p: Path, group: str = DEFAULT_GROUP,
                mode: int = DEFAULT_DIR_MODE):
    nolog_mkdir_chgrp(p, group, mode, get_logger())


def chmod_chgrp(p: Path, group: str = DEFAULT_GROUP,
                mode: int = DEFAULT_FILE_MODE):
    nolog_chmod_chgrp(p, group, mode, get_logger())


def file_copy_chmod_chgrp(src: Path, dest: Path, group: str = DEFAULT_GROUP,
                          mode: int = DEFAULT_FILE_MODE):
    nolog_file_copy_chmod_chgrp(src, dest, group, mode, get_logger())


def import_python_file(pyfile: Path, as_name: str = None):
    return nolog_import_python_file(pyfile, as_name, get_logger())


def add_path_to_syspath(p: Path | str):
    nolog_add_path_to_syspath(p, get_logger())


def build_cmd_arg_dict(value: list[str] | dict | str = None):
    return nolog_build_cmd_arg_dict(value)


def build_cmd_arg_list(value: list[str] | dict | str = None,
                       quotekeys: list[str] | tuple[str] = ()):
    return nolog_build_cmd_arg_list(value, quotekeys)


def press_any_key():
    if IS_WIN32:
        os_sys('pause')
    else:
        os_sys('read -srn1 -p "Press any key to continue... "')


def get_top_package_dir_for_obj(obj: object):
    mod = getmodule(obj)
    modname = mod.__name__
    if modname == '__main__':
        return None if is_notebook() else Path(getfile(mod)).parent
    return get_path_to_top_package_dir(modname)


def get_path_to_top_package_dir(modname: str = None):
    if not modname:
        stk = stack()
        frm = stk[1]
        return get_top_package_dir_for_obj(frm[0])

    try:
        return Path(getfile(import_module(modname.split('.')[0]))).parent
    except TypeError:
        print('no pkg')
        pass


def is_dir_conda_env(p: Path):
    return (p/'conda-meta/history').exists()


def get_conda_base_prefix():
    # we don't need to worry about case sensitivity because the Conda source
    # code always uses all caps for these.  It's easy to update later if that
    # ever becomes not the case.
    shlvl = environ.get('CONDA_SHLVL')
    assert shlvl, 'Not running in a Conda environment'
    resolved, base = expand_and_check_var_path('CONDA_ROOT')
    if not resolved and shlvl > 1:
        resolved, p = expand_and_check_var_path('CONDA_EXE')
        if resolved:
            base = p.parent.parent  # CONDA_EXE defined as base/Scripts/conda

    if not resolved:
        base = Path(sys.prefix)

    assert is_dir_conda_env(base), 'Not running in a Conda environment'
    return base
