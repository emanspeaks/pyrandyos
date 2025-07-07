from pathlib import Path
from json import loads as jloads

from ....logging import log_func_call, DEBUGLOW2
from ....utils.git import GitCommitSpec, GitFileSpec, GitDependencySpec

HERE = Path(__file__).parent
ICON_ASSETS_DIR = HERE.parent/'assets'
THIRDPARTY_DIR = HERE.parent/'thirdparty'
CharMap = dict[str, int]


class QIconFontGitCommit(GitCommitSpec):
    pass


class QIconFontGitFile(GitFileSpec):
    @log_func_call(DEBUGLOW2, trace_only=True)
    def __init__(self, git_commit: QIconFontGitCommit, repo_relpath: Path,
                 md5sum: str = None):
        super().__init__(git_commit, repo_relpath, md5sum)
        self.parent: 'QIconFontSpec'

    @log_func_call(DEBUGLOW2, trace_only=True)
    def get_local_path(self, download_dir: Path | None = None):
        classname = self.parent.classname
        p = ICON_ASSETS_DIR/classname

        if download_dir is None:
            from ....app import PyApp
            download_dir = PyApp.mkdir_temp()

        return super().get_local_path(download_dir/classname, p)


class QIconTtfFileSpec(QIconFontGitFile):
    pass


class QIconCharMapFileSpec(QIconFontGitFile):
    @log_func_call(DEBUGLOW2, trace_only=True)
    def __init__(self, git_commit: QIconFontGitCommit, repo_relpath: Path,
                 codepoint_base: int = 16, md5sum: str = None):
        super().__init__(git_commit, repo_relpath, md5sum)
        self.codepoint_base = codepoint_base

    @log_func_call
    def load_charmap(self) -> CharMap:
        jsonfile = self.get_local_path()
        charmap: dict[str, str | int] = jloads(jsonfile.read_text())
        cpbase = self.codepoint_base
        return {k: int(v, cpbase) if not isinstance(v, int) else v
                for k, v in charmap.items()}


class QIconFontSpec(GitDependencySpec):
    @log_func_call(DEBUGLOW2, trace_only=True)
    def __init__(self,  # target_relative_module_name: str,
                 ttf_filespec: QIconTtfFileSpec,
                 charmap_filespec: QIconCharMapFileSpec):
        self.target_relative_class_qualname = None

        self.ttf_filespec = ttf_filespec
        ttf_filespec.parent = self

        self.charmap_filespec = charmap_filespec
        charmap_filespec.parent = self

        self.charmap: CharMap = None
        self.classname: str = None
        self.relative_module_qualname: str = None

    @log_func_call(DEBUGLOW2, trace_only=True)
    def ensure_local_files(self, download_dir: Path = None):
        ttffile = self.ttf_filespec.get_or_download(download_dir)
        jsonfile = self.charmap_filespec.get_or_download(download_dir)
        return ttffile, jsonfile

    @log_func_call
    def initialize(self, target_relative_class_qualname: str,
                   download_dir: Path = None):
        tmpmodname = target_relative_class_qualname
        self.target_relative_class_qualname = tmpmodname
        self.relative_module_qualname = tmpmodname.lower()
        self.classname = tmpmodname.replace('.', '_')

        self.ttf_filespec.classname = self.classname

        self.ensure_local_files(download_dir)
        self.charmap = self.charmap_filespec.load_charmap()

    @log_func_call(DEBUGLOW2, trace_only=True)
    def relative_class_qualname(self):
        modname = self.relative_module_qualname
        classname = self.classname
        return f"{modname}.{classname}"
