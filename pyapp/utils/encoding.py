from pathlib import Path


def read_text_utf8(path: str | Path) -> str:
    return Path(path).read_text(encoding='utf-8')


def write_text_utf8(path: str | Path, content: str) -> None:
    Path(path).write_text(content, encoding='utf-8')
