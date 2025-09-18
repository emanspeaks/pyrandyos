import sys
from pathlib import Path, PurePosixPath, PureWindowsPath, PurePath, WindowsPath

from ..logging import log_func_call, DEBUGLOW2
from .expandvars import expandvars, is_key_resolved
from .constants import IS_WIN32


@log_func_call(DEBUGLOW2, trace_only=True)
def get_equiv_pureposixpath(x: str | Path):
    """
    Returns a `PurePosixPath` object equivalent to the given input path.

    The Python standard library `pathlib.Path` class automatically assumes the
    paths it is passed are valid paths for the platform it is running on and
    does not try to infer anything from its own contents.  This function exists
    to provide a means to convert Windows paths to POSIX-style paths in a
    consistent way so that `Path` objects created from the results of this
    function operate correctly in a platform-independent way.

    No expansions or path resolution is performed by this function; the path is
    converted as is.

    Args:
        x (str  |  Path): input path

    Returns:
        PurePosixPath: path to `x` as a `PurePosixPath`, or None if `x` is None
            or empty
    """
    # this voodoo was found experimentally and forces all flavors of Windows
    # paths and slashes to unify and become POSIX-ified.  All these steps are
    # necessary for reasons that I can't recall, but I assure you that it
    # needs to stay like this.  Don't be tempted to simplify.
    if x:
        return PurePosixPath(PureWindowsPath(str(x)).as_posix())


@log_func_call(DEBUGLOW2, trace_only=True)
def pureposixpath_to_pathobj(ppp: PurePosixPath):
    """
    Converts a `PurePosixPath` object to a `Path` object, expanding user
    directories if necessary.

    Args:
        ppp (PurePosixPath): path to convert to `Path`

    Returns:
        Path: path pointed to by `ppp` with user directory expanded if needed
    """
    # the as_posix() here is required to workaround a "feature" where the slash
    # after the drive letter in windows gets dropped otherwise
    if ppp:
        pathobj = Path(ppp.as_posix()).expanduser()
        if (isinstance(pathobj, WindowsPath) and pathobj.drive
                and not pathobj.root):
            pathobj = Path(f'{pathobj}/')

        return pathobj


@log_func_call(DEBUGLOW2, trace_only=True)
def pureposixpath_to_resolved_pathobj(ppp: PurePosixPath):
    """
    Converts a `PurePosixPath` object to an absolute `Path` object, expanding
    user directories if necessary.

    Args:
        ppp (PurePosixPath): path to convert to an absolute `Path`

    Returns:
        Path: absolute path pointed to by `ppp` with user directory expanded
            if needed
    """
    pathobj = pureposixpath_to_pathobj(ppp)
    # if we have a leading unexpanded variable at this point, we can't rule out
    # that the variable might have an absolute path in it, so don't try to
    # resolve it any further.
    if pathobj.as_posix()[0] == '$':
        return pathobj
    return pathobj.resolve()


@log_func_call(DEBUGLOW2, trace_only=True)
def get_expanded_pureposixpath(x: str | Path, addl_expand_vars: dict = {},
                               case_insensitive: bool = IS_WIN32):
    """
    Returns a `PurePosixPath` object equivalent to the given input path with
    all known variables of form `$var` or `${var}` expanded.
    See `get_equiv_pureposixpath()` for details on why this function is
    necessary.

    See `expandvars()` for details on how variables are expanded.

    The given path is merely expanded and returned as a `PurePosixPath`.
    User directories are not expanded, nor is the path resolved to an
    absolute one.

    Args:
        x (str  |  Path): input path
        addl_expand_vars (dict, optional): additional variables to override or
            supplement OS environment variables.  See `expandvars()` for
            details. Defaults to {}.

    Returns:
        PurePosixPath: path to `x` as a `PurePosixPath` with all known
            variables expanded, or None if `x` is None or empty
    """
    if x:
        return get_equiv_pureposixpath(expandvars(str(x), addl_expand_vars,
                                                  case_insensitive))


@log_func_call(DEBUGLOW2, trace_only=True)
def get_expanded_pathobj(x: str | Path, addl_expand_vars: dict = {},
                         case_insensitive: bool = IS_WIN32,
                         resolve: bool = True):
    """
    Returns an absolute `Path` object on the current system platform
    resolved from the given input path with user directories and all known
    variables of form `$var` or `${var}` expanded.

    See `expandvars()` for details on how variables are expanded.

    Args:
        x (str  |  Path): input path
        addl_expand_vars (dict, optional): additional variables to override or
            supplement OS environment variables.  See `expandvars()` for
            details. Defaults to {}.

    Returns:
        Path: fully-expanded absolute path to `x`, or None if `x` is None
            or empty
    """
    if x:
        ppp = get_expanded_pureposixpath(x, addl_expand_vars, case_insensitive)
        if resolve:
            return pureposixpath_to_resolved_pathobj(ppp)
        return pureposixpath_to_pathobj(ppp)


DLL_EXTS = ('.dll', '.so', '.dylib')


@log_func_call(DEBUGLOW2, trace_only=True)
def get_dll_ext_for_platform(platform: str = None):
    """
    Returns the preferred DLL file extension for the given
    `sys.platform` string

    Args:
        platform (str, optional): output of `sys.platform` to use.  Can be
            user-provided to allow overriding current platform for cross-target
            scripts.  If None, gets the current value of `sys.platform`.

    Returns:
        str: DLL file extension for platform
    """
    platform = platform or sys.platform

    if platform == 'win32':
        return '.dll'
    if platform == 'darwin':
        return '.dylib'
    return '.so'


@log_func_call(DEBUGLOW2, trace_only=True)
def replace_extension(p: Path | PurePath, ext: str):
    """
    Returns path `p` with the final suffix replaced by `ext`.

    Args:
        p (Path | PurePath): path to replace final suffix
        ext (str): extension to substitute for final suffix

    Returns:
        Path | PurePath: path with extension substituted
    """
    # return p.parent/(p.stem + ext)
    return p.with_suffix(ext)


@log_func_call(DEBUGLOW2, trace_only=True)
def test_alt_dll_paths(dll_path: Path, prefer_ext: str):
    """
    Test existence of the given DLL path with extensions other than the
    preferred extension.  Return the first found path.

    Args:
        dll_path (Path): path to replace extension and test
        prefer_ext (str): preferred extension (i.e. extension to skip testing)

    Returns:
        Path: found file that exists, otherwise None
    """
    prefer_ext = prefer_ext.lower()
    for ext in DLL_EXTS:
        if ext == prefer_ext:
            continue
        p = replace_extension(dll_path, ext)
        if p.exists():
            return p


@log_func_call(DEBUGLOW2, trace_only=True)
def expand_and_check_var(var_name: str, addl_expand_vars: dict = {},
                         case_insensitive: bool = IS_WIN32):
    "returns resolved, value"

    value = expandvars(f'${var_name}', addl_expand_vars, case_insensitive)
    resolved = is_key_resolved(value, var_name, case_insensitive)
    return resolved, value


@log_func_call(DEBUGLOW2, trace_only=True)
def expand_and_check_var_path(var_name: str, addl_expand_vars: dict = {},
                              case_insensitive: bool = IS_WIN32,
                              resolve_path: bool = True):
    "returns resolved, value"

    resolved, value = expand_and_check_var(var_name, addl_expand_vars,
                                           case_insensitive)
    if resolve_path:
        p = get_expanded_pathobj(value, addl_expand_vars, case_insensitive)

    else:
        ppp = get_expanded_pureposixpath(value, addl_expand_vars,
                                         case_insensitive)
        p = pureposixpath_to_pathobj(ppp)

    return resolved, p
