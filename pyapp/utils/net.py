from pathlib import Path
# from json import loads as jloads
from urllib.request import urlopen
from urllib.response import addinfourl

from ..logging import log_func_call
from .tqdm import optional_tqdm


@log_func_call
def get_github_download_url(base_url: str, commit: str, relpath: Path):
    return f'{base_url}/raw/{commit}/{relpath.as_posix()}'


@log_func_call
def download_file(url: str, dest: Path, use_tqdm: bool = True,
                  chunk_size: int = 8192):
    if dest.is_dir():
        dest = dest / Path(url).name

    with dest.open('wb') as f, urlopen(url) as response:
        response: addinfourl
        if response.status != 200:
            raise RuntimeError(f"Failed to download file from {url}: "
                               f"HTTP {response.status}")

        with optional_tqdm(use_tqdm, desc=dest.name, unit='B', unit_scale=True,
                           total=int(response.headers.get('Content-Length',
                                                          0))) as t:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                t.update(len(chunk))

    return dest
