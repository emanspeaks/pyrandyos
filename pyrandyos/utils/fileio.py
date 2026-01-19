from pathlib import Path
from contextlib import contextmanager

from ..logging import log_critical


@contextmanager
def safe_file_io(file: Path):
    try:
        yield
    except (FileNotFoundError, OSError):
        log_critical(f'File {file} not found or unreachable')


@contextmanager
def safe_file_io_retry(file: Path):
    success = False
    while not success:
        try:
            yield
        except (FileNotFoundError, OSError):
            log_critical(f'File {file} not found or unreachable')
        else:
            success = True
