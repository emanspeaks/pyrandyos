def round_half_away(value: float | int | str | None = None,
                    ndigits: int = 0):
    value = float(value)
    sgn = 1 - 2*(value < 0)
    absval = abs(value)
    expo = -ndigits or 0
    scalar = 10**expo
    quo, rem = divmod(absval, scalar)
    out = sgn*scalar*(quo + (rem*2 >= scalar))
    if ndigits <= 0:
        return int(out)
    return out
