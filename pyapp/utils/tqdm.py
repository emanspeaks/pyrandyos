from collections.abc import Iterable, Iterator
from pathlib import Path

from tqdm.auto import tqdm

from ..logging import log_func_call

TQDM_RBAR_STATWIDTH = 50

FileSet = set[Path]


@log_func_call
def iterable_max_chars(x: Iterable):
    return max(len(str(y)) for y in x)


@log_func_call
def tqdm_fixed_label_barfmt(x: Iterable, maxlen: int = None):
    if maxlen is None:
        maxlen = iterable_max_chars(x)

    return f'{{l_bar}}{{bar}}{{r_bar:{TQDM_RBAR_STATWIDTH + maxlen}}}'


@log_func_call
def tqdm_fixed_label_width(x: Iterable, maxlen: int = None, **kwargs):
    return tqdm(x, bar_format=tqdm_fixed_label_barfmt(x, maxlen), **kwargs)


class FileSetTqdm(tqdm):
    """
    A tqdm subclass that can handle FileSet objects, printing the file paths
    in the tqdm description after each iteration.
    """
    @log_func_call
    def __init__(self, fset: FileSet, maxlen: int = None, **kwargs):
        fmt = tqdm_fixed_label_barfmt([x.as_posix() for x in fset], maxlen)
        super().__init__(sorted(fset), bar_format=fmt, **kwargs)

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
