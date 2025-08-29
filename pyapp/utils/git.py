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
            from ..app import PyApp
            download_dir = PyApp.mkdir_temp()

        download_dir.mkdir(parents=True, exist_ok=True)
        return download_dir/name

    @log_func_call(WARNING)
    def download(self, dest: Path):
        git = self.git_commit
        repo = git.git_repo_base_url
        commit = git.git_commit_hash
        relpath = self.repo_relpath
        return download_file(get_github_download_url(repo, commit, relpath),
                             dest)

    @log_func_call(DEBUGLOW2, trace_only=True)
    def get_or_download(self, download_dir: Path = None):
        p = self.get_local_path(download_dir)
        if not p.exists():
            p = self.download(p)
            if not p.exists():
                raise FileNotFoundError(f"Failed to find or download {p}")

        if self.md5sum and self.md5sum != filehash(p, algorithm='md5'):
            raise ValueError(f"MD5 checksum does not match for {p}")
        return p


class GitDependencySpec:
    pass
