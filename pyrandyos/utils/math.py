from pandas import Series
from numpy import divmod as npdivmod

from ..logging import log_func_call


@log_func_call
def round_half_away(value: float | int | str | Series | None = None,
                    ndigits: int = 0):
    if not isinstance(value, Series):
        value = float(value)

    sgn = 1 - 2*(value < 0)
    absval = abs(value)
    expo = -ndigits or 0
    scalar = 10**expo
    quo, rem = npdivmod(absval, scalar)
    out = sgn*scalar*(quo + (rem*2 >= scalar))
    if ndigits <= 0:
        return out.astype(int) if isinstance(out, Series) else int(out)
    return out
