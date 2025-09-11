from collections.abc import Iterable

from ..logging import log_func_call


@log_func_call
def ensure_str(x: str | bytes):
    """
    Coerce `x` to `str`, decoding bytes if necessary

    Args:
        x (str | bytes): object to coerce to `str`

    Returns:
        str: `x` coerced to `str`
    """
    if hasattr(x, 'decode'):
        x = x.decode()
    return str(x)


@log_func_call
def ensure_bytes(x: str | bytes, encoding: str = 'utf-8'):
    """
    Coerce `x` to `bytes`, encoding string if necessary.  If `x` is not
    `bytes`-like, it is converted to a string and then encoded.

    Args:
        x (str | bytes): object to coerce to `bytes`
        encoding (str, optional): encoding to use for strings.
            See Python `codecs` documentation for list of valid options
            for [standard encodings](https://docs.python.org/3/library/codecs.html#standard-encodings)
            or [Python-specific encodings](https://docs.python.org/3/library/codecs.html#python-specific-encodings).
            For WinAPI calls, use 'utf-16-le' (see `pyrandyos.utils.constants.windows.WIN_WCHAR_ENCODING` for details).
            Defaults to 'utf-8'.

    Returns:
        bytes: `x` coerced to `bytes`
    """  # noqa: E501
    x = x if hasattr(x, 'decode') else str(x)
    return bytes(x.encode(encoding) if hasattr(x, 'encode') else x)


@log_func_call
def quote_str(s: str):
    """
    Enclose the string in double quotations marks.
    """
    if s:
        return '"' + ensure_str(s).strip('"').strip("'") + '"'


@log_func_call
def iterable_max_chars(x: Iterable):
    return max(len(str(y)) for y in x) if x else 0
