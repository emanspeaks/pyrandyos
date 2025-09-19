from re import sub, DOTALL, MULTILINE, compile
from collections import OrderedDict

from ...logging import log_func_call


@log_func_call
def strip_qss_comments(qss: str) -> str:
    """Remove /* ... */ comments from QSS string."""
    return sub(r'/\*.*?\*/', '', qss, flags=DOTALL)


@log_func_call
def parse_qss_blocks(qss_text: str) -> OrderedDict:
    """Parse QSS into an OrderedDict: selector -> OrderedDict of properties."""
    blocks = OrderedDict()
    pattern = compile(r'([^{]+)\{([^}]*)\}', MULTILINE)
    # This regex matches key: value; pairs, where value can include semicolons
    # inside quotes
    import re
    prop_pattern = re.compile(r'([a-zA-Z0-9\-]+)\s*:\s*((?:"[^"]*"|[^;])*);')
    for match in pattern.finditer(qss_text):
        selector = match.group(1).strip()
        props = OrderedDict()
        for prop_match in prop_pattern.finditer(match.group(2)):
            k = prop_match.group(1).strip()
            v = prop_match.group(2).strip()
            props[k] = v
        blocks[selector] = props
    return blocks


@log_func_call
def update_qss_block(blocks: OrderedDict, selector: str,
                     updates: dict[str, str]) -> None:
    """Update or add properties for a selector in the QSS blocks.

    To remove a property, pass None as the value.
    """
    if selector not in blocks:
        blocks[selector] = OrderedDict()
    for k, v in updates.items():
        if v is None:
            # Remove the property if it exists
            blocks[selector].pop(k, None)
        else:
            # Set or update the property
            blocks[selector][k] = v


@log_func_call
def qss_blocks_to_text(blocks: OrderedDict) -> str:
    """Convert QSS blocks back to a QSS string."""
    out = []
    for selector, props in blocks.items():
        out.append(f"{selector} {{")
        for k, v in props.items():
            out.append(f"    {k}: {v};")
        out.append("}")
    return "\n".join(out)


@log_func_call
def merge_qss_properties(qss: str, selector: str, updates: dict[str, str]):
    """
    Load QSS, strip comments, parse, update properties for selector, and return
    merged QSS string.
    """
    qss = strip_qss_comments(qss)
    blocks = parse_qss_blocks(qss)
    update_qss_block(blocks, selector, updates)
    return qss_blocks_to_text(blocks)

# Example usage:
# with open("vibedark-full.qss", "r", encoding="utf-8") as f:
#     qss = f.read()
# merged_qss = merge_qss_properties(qss, "QComboBox::down-arrow", {
#     "image": 'url("data:image/png;base64,...")',
#     "width": "16px",
#     "height": "16px"
# })
# app.setStyleSheet(merged_qss)
