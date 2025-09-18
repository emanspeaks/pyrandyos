# This module contains functions that interact either with the operating system
# the Python interpreter, or conda environments.

import sys
from os import system as os_sys
from pathlib import Path
from shutil import chown, copy2
from importlib.util import spec_from_file_location, module_from_spec
from shlex import split as shsplit

from ..logging import DEBUGLOW2, log_func_call, log_debug
from .constants import (
    DEFAULT_GROUP, DEFAULT_DIR_MODE, DEFAULT_FILE_MODE, IS_WIN32,
)
from .paths import expand_and_check_var_path, expand_and_check_var
from .string import quote_str


@log_func_call(DEBUGLOW2, trace_only=True)
def mkdir_chgrp(p: Path, group: str = DEFAULT_GROUP,
                mode: int = DEFAULT_DIR_MODE):
    if p:
        p.mkdir(exist_ok=True, parents=True, mode=mode)
        if group:
            chown(p, group=group)


@log_func_call(DEBUGLOW2, trace_only=True)
def chmod_chgrp(p: Path, group: str = DEFAULT_GROUP,
                mode: int = DEFAULT_FILE_MODE):
    if p:
        p.chmod(mode=mode)
        if group:
            chown(p, group=group)


@log_func_call(DEBUGLOW2, trace_only=True)
def file_copy_chmod_chgrp(src: Path, dest: Path, group: str = DEFAULT_GROUP,
                          mode: int = DEFAULT_FILE_MODE):
    copy2(src, dest)  # preserves file stat metadata (like mtime, etc.)
    chmod_chgrp(dest, group, mode)


@log_func_call
def import_python_file(pyfile: Path, as_name: str = None):
    as_name = as_name or pyfile.stem
    spec = spec_from_file_location(as_name, str(pyfile))
    mod = module_from_spec(spec)
    sys.modules[as_name] = mod
    spec.loader.exec_module(mod)
    return mod


@log_func_call
def add_path_to_syspath(p: Path | str):
    log_debug(f'attempt to add {p} to sys.path')
    ppath = Path(p).resolve()
    pstr = str(p)
    log_debug(f'(before) sys.path={sys.path}')
    for x in sys.path:
        if Path(x).resolve() == ppath:
            log_debug('directory already in sys.path, taking no action')
            return

    sys.path.insert(0, pstr)
    log_debug(f'updated sys.path to include {p}')
    log_debug(f'(after) sys.path={sys.path}')


@log_func_call(DEBUGLOW2, trace_only=True)
def build_cmd_arg_dict(value: list[str] | dict | str = None):
    value = value or dict()
    args = dict()
    if isinstance(value, str):
        args = shsplit(value)

    if isinstance(value, list):
        lastkey = None
        for x in value:
            if x[0] == '-':
                if lastkey:
                    args[lastkey] = True

                lastkey = x[1:]

            elif lastkey:
                if lastkey in args:
                    orig = args[lastkey]
                    orig = orig if isinstance(orig, list) else [orig]

                    x = orig + [x]
                args[lastkey] = x
                lastkey = None

            else:
                ValueError('multiple values with no command or parse error')

        if lastkey:
            args[lastkey] = True

    else:
        args = value

    return args


@log_func_call(DEBUGLOW2, trace_only=True)
def _add_arg_to_list(args: list, k: str, v: str,
                     quotekeys: list[str] | tuple[str] = ()):
    args.append(f'-{k}')
    if v is not True:
        if k in quotekeys:
            v = quote_str(v)

        args.append(str(v))


@log_func_call(DEBUGLOW2, trace_only=True)
def build_cmd_arg_list(value: list[str] | dict | str = None,
                       quotekeys: list[str] | tuple[str] = ()):
    value = value or list()
    args = list()
    if isinstance(value, dict):
        for k, v in value.items():
            if v is False:
                continue

            v = v if isinstance(v, list) else [v]
            for x in v:
                _add_arg_to_list(args, k, x, quotekeys)

    elif isinstance(value, str):
        args = shsplit(value)

    else:
        args = value

    return args


@log_func_call
def press_any_key():
    if IS_WIN32:
        os_sys('pause')
    else:
        os_sys('read -srn1 -p "Press any key to continue... "')


@log_func_call(DEBUGLOW2)
def is_dir_conda_env(p: Path):
    return (p/'conda-meta/history').exists()


@log_func_call
def get_conda_base_prefix(addl_expand_vars: dict = {},
                          case_insensitive: bool = IS_WIN32):
    # we don't need to worry about case sensitivity because the Conda source
    # code always uses all caps for these.  It's easy to update later if that
    # ever becomes not the case.
    resolved, shlvl = expand_and_check_var('CONDA_SHLVL', addl_expand_vars,
                                           case_insensitive)
    if resolved:
        # assert shlvl, 'Not running in a Conda environment'
        resolved, base = expand_and_check_var_path('CONDA_ROOT',
                                                   addl_expand_vars,
                                                   case_insensitive)
        if not resolved and int(shlvl) > 1:
            resolved, p = expand_and_check_var_path('CONDA_EXE',
                                                    addl_expand_vars,
                                                    case_insensitive)
            if resolved:
                base = p.parent.parent  # CONDA_EXE defined base/Scripts/conda

    if not resolved:
        base = Path(sys.prefix)

    assert is_dir_conda_env(base), 'Not running in a Conda environment'
    return base
