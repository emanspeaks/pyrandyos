from keyword import iskeyword


def legalize_iconname(iconname: str) -> str:
    """
    Convert an icon name to a legal Python identifier.
    """
    newname = iconname.replace('-', '_')
    if iskeyword(newname):
        newname += '_'

    if newname[0].isdigit():
        newname = f'_{newname}'

    if newname == "l":
        newname = "L"

    return newname
