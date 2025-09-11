import sys
from typing import TYPE_CHECKING
from collections.abc import Iterable, Iterator, Generator
from pathlib import Path
from contextlib import contextmanager
from unittest.mock import MagicMock

from tqdm.auto import tqdm
from tqdm.utils import _screen_shape_wrapper

from ..logging import log_func_call
from .string import iterable_max_chars
if TYPE_CHECKING:
    from .filemeta import FileSet

TQDM_RBAR_STATWIDTH = 50


@log_func_call
def tqdm_fixed_label_barfmt(x: Iterable | int = None,
                            ncols: int | None = None):
    maxlen = x if isinstance(x, int) else iterable_max_chars(x)
    statwidth = TQDM_RBAR_STATWIDTH + maxlen
    if ncols and statwidth > 0.75*ncols:
        statwidth = int(0.75*ncols)
    return f'{{l_bar}}{{bar}}{{r_bar:{statwidth}}}'


@log_func_call
def tqdm_fixed_label_width(x: Iterable, maxlen: int = None, **kwargs):
    ncols = get_tqdm_ncols(**kwargs)
    return tqdm(x, bar_format=tqdm_fixed_label_barfmt(maxlen or x, ncols),
                **kwargs)


class FileSetTqdm(tqdm):
    """
    A tqdm subclass that can handle FileSet objects, printing the file paths
    in the tqdm description after each iteration.
    """
    @log_func_call
    def __init__(self, fset: 'FileSet', maxlen: int = None, **kwargs):
        # in case fset is a generator, let's preconvert it to a sorted tuple
        fset = sorted(tuple(fset))
        if not maxlen:
            from .filemeta import fileset_max_chars
            maxlen = fileset_max_chars(fset)

        ncols = get_tqdm_ncols(**kwargs)
        fmt = tqdm_fixed_label_barfmt(maxlen, ncols)
        super().__init__(fset, bar_format=fmt, **kwargs)

    @log_func_call
    def update_file(self, p: Path):
        self.set_postfix(file=p.as_posix())
        self.refresh()

    async def __anext__(self):
        res: Path = super().__anext__()
        self.update_file(res)
        return res

    def __iter__(self):
        """Backward-compatibility to use: for x in tqdm(iterable)"""

        the_iter: Iterator[Path] = super().__iter__()
        for obj in the_iter:
            obj: Path
            self.update_file(obj)
            yield obj


@log_func_call
def get_tqdm_ncols(file=None, ncols: int | None = None,
                   dynamic_ncols: bool = False, **kwargs):
    if ncols is not None:
        return ncols

    if file is None:
        file = sys.stderr

    if (file in (sys.stderr, sys.stdout)) or dynamic_ncols:
        if dynamic_ncols:
            dynamic_ncols = _screen_shape_wrapper()
            if dynamic_ncols:
                ncols, _ = dynamic_ncols(file)
        else:
            _dynamic_ncols = _screen_shape_wrapper()
            if _dynamic_ncols:
                ncols, _ = _dynamic_ncols(file)

    return ncols


@contextmanager
@log_func_call
def optional_tqdm(use_tqdm: bool = True, tqdmclass: type = tqdm,
                  *args, **kwargs) -> Generator[tqdm, None, None]:
    """
    Context manager that yields a tqdm instance if use_tqdm is True,
    otherwise yields a MagicMock that no-ops all tqdm methods.
    """
    if use_tqdm:
        bar: tqdm = tqdmclass(*args, **kwargs)
    else:
        bar = MagicMock()
        bar.__enter__.return_value = bar
        bar.__exit__.return_value = None
    try:
        yield bar
    finally:
        bar.close()
