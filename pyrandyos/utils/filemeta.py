from collections.abc import Iterable
from pathlib import Path
from hashlib import new as newhash
from re import search

from ..logging import log_func_call
from .string import iterable_max_chars
from .tqdm import FileSetTqdm

FileSet = set[Path]
StrTup = tuple[str]
FilePair = tuple[Path, Path]

BULLETSEP = '\n* '


@log_func_call
def filehash(p: Path, *, blocksize: int = 65536,
             algorithm: str = 'md5') -> str:
    hasher = newhash(algorithm)
    with p.open('rb') as f:
        while chunk := f.read(blocksize):
            hasher.update(chunk)
    return hasher.hexdigest()


@log_func_call
def is_file_in_ignore_regex(p: Path, ignore: StrTup = ()):
    for x in ignore:
        if search(x, p.as_posix()):
            return True

    return False


@log_func_call
def is_file_in_ignore_parts(p: Path, ignore: StrTup = ()):
    parts = p.parts
    for x in ignore:
        if x in parts:
            return True

    return False


@log_func_call
def is_file_in_ignore_suffix(p: Path, ignore: StrTup = ()):
    suffix = p.suffix
    joinsuffix = ''.join(p.suffixes)
    for x in ignore:
        if suffix == x or joinsuffix == x:
            return True
    return False


@log_func_call
def is_file_in_ignore_dirs(p: Path, ignore: StrTup = ()):
    for x in ignore:
        if p.is_relative_to(Path(x)):
            return True
    return False


@log_func_call
def is_file_in_fileset(p: Path, files: StrTup = ()):
    return p.as_posix() in files


@log_func_call
def is_file_in_blacklist(p: Path, blacklist: StrTup = ()):
    return is_file_in_fileset(p, blacklist)


@log_func_call
def is_file_in_whitelist(p: Path, whitelist: StrTup = ()):
    return is_file_in_fileset(p, whitelist)


@log_func_call
def should_ignore_file(p: Path,
                       blacklist: StrTup = (),
                       dir_ignores: StrTup = (),
                       parts_ignores: StrTup = (),
                       suffix_ignores: StrTup = (),
                       regex_ignores: StrTup = ()):
    return (is_file_in_blacklist(p, blacklist)
            or is_file_in_ignore_dirs(p, dir_ignores)
            or is_file_in_ignore_parts(p, parts_ignores)
            or is_file_in_ignore_suffix(p, suffix_ignores)
            or is_file_in_ignore_regex(p, regex_ignores))


@log_func_call
def build_ignore_args_dict(blacklist: StrTup = (),
                           dir_ignores: StrTup = (),
                           parts_ignores: StrTup = (),
                           suffix_ignores: StrTup = (),
                           regex_ignores: StrTup = ()):
    return dict(blacklist=blacklist,
                dir_ignores=dir_ignores,
                parts_ignores=parts_ignores,
                suffix_ignores=suffix_ignores,
                regex_ignores=regex_ignores)


@log_func_call
def generate_fileset(p: Path,
                     apply_filter: bool = True,
                     whitelist: StrTup = (),
                     blacklist: StrTup = (),
                     dir_ignores: StrTup = (),
                     parts_ignores: StrTup = (),
                     suffix_ignores: StrTup = (),
                     regex_ignores: StrTup = ()):
    ignore_args = build_ignore_args_dict(blacklist, dir_ignores, parts_ignores,
                                         suffix_ignores, regex_ignores)
    s = set()
    for f in p.rglob('*'):
        if f.is_dir():
            continue
        relpath = f.relative_to(p)
        if (apply_filter
                and not is_file_in_whitelist(relpath, whitelist)
                and should_ignore_file(relpath, **ignore_args)):
            continue

        s.add(relpath)

    return s


@log_func_call
def compare_dirs(src: Path, dest: Path,
                 filter: bool = True):
    return compare_filesets(*get_src_dest_filesets(src, dest, filter))


@log_func_call
def get_src_dest_filesets(src: Path, dest: Path,
                          apply_filter: bool = True,
                          whitelist: StrTup = (),
                          blacklist: StrTup = (),
                          dir_ignores: StrTup = (),
                          parts_ignores: StrTup = (),
                          suffix_ignores: StrTup = (),
                          regex_ignores: StrTup = ()):
    ignore_args = build_ignore_args_dict(blacklist, dir_ignores, parts_ignores,
                                         suffix_ignores, regex_ignores)
    kwargs = dict(whitelist=whitelist, **ignore_args)
    src_files = generate_fileset(src, apply_filter, **kwargs)
    dest_files = generate_fileset(dest, apply_filter, **kwargs)
    return src_files, dest_files


@log_func_call
def compare_filesets(src_files: FileSet, dest_files: FileSet):
    files_src_only = src_files.difference(dest_files)
    files_dest_only = dest_files.difference(src_files)
    files_on_both = src_files.intersection(dest_files)
    return files_src_only, files_dest_only, files_on_both


@log_func_call
def fileset_as_posix(fset: FileSet):
    return {x.as_posix() for x in fset}


@log_func_call
def fileset_max_chars(fset: FileSet):
    return iterable_max_chars(fileset_as_posix(fset))


@log_func_call
def compare_fileset_hashes(fset: FileSet, src: Path, dest: Path,
                           algorithm: str = 'md5', verbose: bool = True):
    not_matching = set()
    for f in FileSetTqdm(fset):
        srcfile = src/f
        srchash = filehash(srcfile, algorithm=algorithm)

        destfile = dest/f
        desthash = filehash(destfile, algorithm=algorithm)

        if desthash != srchash:
            if verbose:
                print(f'{f} | src: {srchash}, dest: {desthash}')

            not_matching.add(f)

    return not_matching


@log_func_call
def fileset_to_sorted_str_list(fset: FileSet):
    return sorted(fileset_as_posix(fset))


@log_func_call
def sorted_bulleted_list(x: Iterable[str], sep: str = BULLETSEP):
    return sep + sep.join(sorted(x))


@log_func_call
def fileset_to_str(fset: FileSet, sep: str = BULLETSEP):
    return sorted_bulleted_list(fileset_to_sorted_str_list(fset), sep)


@log_func_call
def print_fileset(fset: FileSet):
    print(fileset_to_str(fset))


@log_func_call
def src_dest_pairs(src: Path, dest: Path, fset: FileSet):
    return {(src/f, dest/f) for f in fset}


@log_func_call
def generate_md5sum_file(fset: FileSet, md5file: Path = None,
                         base_path: Path = None):
    out = ''
    base_path = base_path or (md5file.parent if md5file else Path.cwd())
    relroot = md5file.parent if md5file else base_path
    for f in FileSetTqdm(fset, desc='Generating md5sum file'):
        p = f if f.is_absolute() else base_path/f
        md5 = filehash(p, algorithm='md5')  # hardcoding for `md5sum` compat
        out += f'{md5}  {p.relative_to(relroot).as_posix()}\n'

    if md5file:
        md5file.write_text(out)

    return out


@log_func_call
def parse_md5sum_file(md5file: Path, base_path: Path = None):
    base_path = base_path or md5file.parent
    return parse_md5sum_file_text(md5file.read_text(), base_path)


@log_func_call
def parse_md5sum_file_text(md5text: str, base_path: Path = None):
    base_path = base_path or Path.cwd()
    md5data: dict[Path, str] = dict()
    for line in md5text.splitlines():
        md5, f = line.split('  ', 1)
        f = Path(f)
        if not f.is_absolute():
            f = base_path/f

        md5data[f] = md5

    return md5data


@log_func_call
def check_md5sum_file(md5file: Path, base_path: Path = None,
                      verbose: bool = True):
    base_path = base_path or md5file.parent
    md5data = parse_md5sum_file(md5file, base_path)
    fset = set(md5data.keys())
    not_matching = set()
    for f in FileSetTqdm(fset, desc='Checking md5sum file'):
        theirhash = md5data[f]
        ourhash = filehash(f, algorithm='md5')
        if theirhash != ourhash:
            if verbose:
                print(f'{f} | ours: {ourhash}, theirs: {theirhash}')

            not_matching.add(f)

    return not_matching
