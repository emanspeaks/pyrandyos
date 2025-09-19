from pathlib import Path

from ..logging import log_func_call, DEBUGLOW2, WARNING
from .net import download_file, get_github_download_url
from .filemeta import filehash


class GitCommitSpec:
    @log_func_call(DEBUGLOW2, trace_only=True)
    def __init__(self, git_repo_base_url: str, git_commit_hash: str,
                 license_relpath: Path | tuple[Path] = None):
        self.git_repo_base_url = git_repo_base_url
        self.git_commit_hash = git_commit_hash
        self.license_relpath = license_relpath


class GitFileSpec:
    @log_func_call(DEBUGLOW2, trace_only=True)
    def __init__(self, git_commit: GitCommitSpec, repo_relpath: Path,
                 md5sum: str = None, local_path: Path = None):
        self.git_commit = git_commit
        self.repo_relpath = repo_relpath
        self.md5sum = md5sum
        self.local_path = local_path
        self.parent: 'GitDependencySpec' = None

    @log_func_call(DEBUGLOW2, trace_only=True)
    def get_local_path(self, download_dir: Path | None = None,
                       override_path: Path | None = None):
        name = self.repo_relpath.name
        p = self.local_path or override_path
        if not p:
            raise ValueError("Base path must be provided if local_path is "
                             "not set")
        if p.is_dir():
            p /= name

        if p.exists():
            return p

        if download_dir is None:
            from ..app import PyRandyOSApp
            download_dir = PyRandyOSApp.mkdir_temp()

        download_dir.mkdir(parents=True, exist_ok=True)
        return download_dir/name

    @log_func_call(WARNING)
    def download(self, dest: Path, use_tqdm: bool = True,
                 show_full_path: bool = False):
        git = self.git_commit
        repo = git.git_repo_base_url
        commit = git.git_commit_hash
        relpath = self.repo_relpath
        return download_file(get_github_download_url(repo, commit, relpath),
                             dest, use_tqdm, show_full_path)

    @log_func_call(DEBUGLOW2, trace_only=True)
    def get_or_download(self, download_dir: Path = None, use_tqdm: bool = True,
                        show_full_path: bool = False):
        p = self.get_local_path(download_dir)
        if not p.exists():
            p = self.download(p, use_tqdm, show_full_path)
            if not p.exists():
                raise FileNotFoundError(f"Failed to find or download {p}")

        if self.md5sum and self.md5sum != filehash(p, algorithm='md5'):
            raise ValueError(f"MD5 checksum does not match for {p}")
        return p

    @log_func_call
    def get_or_download_licenses(self, download_dir: Path = None,
                                 use_tqdm: bool = True,
                                 show_full_path: bool = True):
        # get the directory of the corresponding main file
        # also serves as the download dir for get_or_download later here
        p = self.get_local_path(download_dir).parent
        gitcommit = self.git_commit
        license_paths = gitcommit.license_relpath
        if not license_paths:
            return
        if not isinstance(license_paths, tuple):
            license_paths = (license_paths,)

        return tuple(GitFileSpec(gitcommit, lic,
                                 local_path=p).get_or_download(p, use_tqdm,
                                                               show_full_path)
                     for lic in license_paths)


class GitDependencySpec:
    pass
