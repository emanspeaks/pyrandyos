from json import loads as jloads, JSONDecodeError, dumps as jdumps
from pathlib import Path
from types import NoneType
from re import sub

from ..logging import log_func_call

JSONTYPES = (str, float, int, bool, list, dict, NoneType)
JsonDataType = str | float | int | bool | list | dict | NoneType


@log_func_call
def load_jsonc(fn: str | Path) -> dict | list:
    """
    Open a JSON file and return its parsed contents as a dict or list.

    Args:
        fn (str | Path): file path to open

    Raises:
        JSONDecodeError: provides details on what file it failed to parse and
            details about the error.

    Returns:
        dict | list: parsed contents of the file `fn`
    """
    try:
        return parse_jsonc(Path(fn).read_text())
    except JSONDecodeError as e:
        raise JSONDecodeError(f'error reading {fn}: {e.msg}', e.doc, e.pos)


@log_func_call
def parse_jsonc(jsonstr: str) -> dict | list:
    """
    return the parsed contents of given string as a dict or list.

    Args:
        jsonstr (str): JSON-formatted string to parse

    Raises:
        JSONDecodeError: provides details on why it failed to parse

    Returns:
        dict | list: parsed contents of the string `jsonstr`
    """
    buf = ""
    for line in jsonstr.splitlines():
        curline = ''
        inquote = False
        escape = False
        lastc = ''
        for c in line:
            if escape:
                escape = False
            elif c == '"':
                inquote = not inquote
            elif inquote:
                if c == '\\':
                    escape = True
            elif c == '/' and lastc == '/':
                lastc = ''
                break
            curline += lastc
            lastc = c
        curline += lastc
        buf += curline

    # Remove trailing commas in objects and arrays
    buf = sub(r',([ \t\r\n]*[}}\]])', r'\1', buf)

    return jloads(buf)


@log_func_call
def save_json(fn: str | Path, data: dict | list):
    """
    Save `data` to the file `fn` in JSON format.

    The values inside of `data` must all be JSON-compatible types.
    The constant `JSON_TYPES` lists all valid pure JSON types.  While the
    contents of `data` do not need to be exclusively these types, they must be
    easily coercible to one of these types.  The validation of types is done
    by the Python standard library JSON implementation and no additional
    validation is performed by this function.

    Args:
        fn (str | Path): file path to save
        data (dict | list): structured data to convert to JSON.
    """
    Path(fn).write_text(jdumps(data, indent=2))


@log_func_call
def jsonify(data) -> JsonDataType:
    if isinstance(data, dict):
        return {k: jsonify(v) for k, v in data.items()}

    elif isinstance(data, list):
        return [jsonify(item) for item in data]

    elif isinstance(data, (str, float, int, bool)) or data is None:
        return data

    elif isinstance(data, Path):
        return data.as_posix()

    else:
        raise TypeError(f"Type is not JSON serializable: {type(data)}")
