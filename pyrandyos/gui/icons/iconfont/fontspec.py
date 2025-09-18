from pathlib import Path
from json import loads as jloads
from importlib import import_module

from ....logging import log_func_call, DEBUGLOW2
from ....utils.git import GitCommitSpec, GitFileSpec, GitDependencySpec
from .. import thirdparty

HERE = Path(__file__).parent
ICON_ASSETS_DIR = HERE.parent/'assets'
# THIRDPARTY_DIR = HERE.parent/'thirdparty'
THIRDPARTY_DIR = Path(thirdparty.__file__).parent
CharMap = dict[str, int]


class IconFontGitCommit(GitCommitSpec):
    pass


class IconFontGitFile(GitFileSpec):
    @log_func_call(DEBUGLOW2, trace_only=True)
    def __init__(self, filetype: str, git_commit: IconFontGitCommit,
                 repo_relpath: Path, md5sum: str = None):
        super().__init__(git_commit, repo_relpath, md5sum)
        self.parent: 'IconFontSpec'
        self.filetype = filetype

    @log_func_call(DEBUGLOW2, trace_only=True)
    def get_local_path(self, download_dir: Path | None = None):
        classname = self.parent.classname
        filetype = self.filetype
        p = ICON_ASSETS_DIR/classname/filetype

        if download_dir is None:
            from ....app import PyRandyOSApp
            download_dir = PyRandyOSApp.mkdir_temp()

        return super().get_local_path(download_dir/classname/filetype, p)


class IconTtfFileSpec(IconFontGitFile):
    @log_func_call(DEBUGLOW2, trace_only=True)
    def __init__(self, git_commit: IconFontGitCommit, repo_relpath: Path,
                 md5sum: str = None):
        super().__init__('ttf', git_commit, repo_relpath, md5sum)
        self.parent: 'IconFontSpec'


class IconCharMapFileSpec(IconFontGitFile):
    @log_func_call(DEBUGLOW2, trace_only=True)
    def __init__(self, git_commit: IconFontGitCommit, repo_relpath: Path,
                 codepoint_base: int = 16, md5sum: str = None):
        super().__init__('charmap', git_commit, repo_relpath, md5sum)
        self.codepoint_base = codepoint_base

    @log_func_call
    def load_charmap(self) -> CharMap:
        jsonfile = self.get_local_path()
        charmap: dict[str, str | int] = jloads(jsonfile.read_text())
        cpbase = self.codepoint_base
        return {k: int(v, cpbase) if not isinstance(v, int) else v
                for k, v in charmap.items()}


class IconFontSpec(GitDependencySpec):
    @log_func_call(DEBUGLOW2, trace_only=True)
    def __init__(self,  # target_relative_module_name: str,
                 ttf_filespec: IconTtfFileSpec,
                 charmap_filespec: IconCharMapFileSpec,
                 solid: bool = False):
        self.target_relative_class_qualname = None

        self.ttf_filespec = ttf_filespec
        ttf_filespec.parent = self

        self.charmap_filespec = charmap_filespec
        charmap_filespec.parent = self

        self.solid = solid
        self.charmap: CharMap = None
        self.classname: str = None
        self.shortname: str = None
        self.relative_module_qualname: str = None
        self._initialized = False

    @log_func_call(DEBUGLOW2, trace_only=True)
    def ensure_local_files(self, download_dir: Path = None):
        ttfspec = self.ttf_filespec
        ttffile = ttfspec.get_or_download(download_dir)
        ttflicenses = ttfspec.get_or_download_licenses(download_dir)

        charmapspec = self.charmap_filespec
        charmapfile = charmapspec.get_or_download(download_dir)
        charmaplicenses = charmapspec.get_or_download_licenses(download_dir)

        return ttffile, charmapfile, ttflicenses, charmaplicenses

    @log_func_call(DEBUGLOW2, trace_only=True)
    def initialize(self, target_relative_class_qualname: str,
                   download_dir: Path = None):
        if not self._initialized:
            tmpmodname = target_relative_class_qualname
            self.target_relative_class_qualname = tmpmodname
            self.relative_module_qualname = tmpmodname.lower()
            tmpmodname_parts = tmpmodname.split('.')
            classname = '_'.join(tmpmodname_parts)
            self.classname = classname
            # self.ttf_filespec.classname = classname
            shortnameparts = tmpmodname_parts.copy()
            if len(shortnameparts) > 1:
                shortnameparts[-1] = shortnameparts[-1][0]
            self.shortname = '_'.join(shortnameparts).lower()

            self.ensure_local_files(download_dir)
            self.charmap = self.charmap_filespec.load_charmap()
            self._initialized = True

    @log_func_call(DEBUGLOW2, trace_only=True)
    def relative_class_qualname(self):
        modname = self.relative_module_qualname
        classname = self.classname
        return f"{modname}.{classname}"

    @log_func_call(DEBUGLOW2, trace_only=True)
    def module_qualname(self):
        thirdpartymod = thirdparty.__name__
        relqualname = self.relative_module_qualname
        return f'{thirdpartymod}.{relqualname}'

    @log_func_call(DEBUGLOW2, trace_only=True)
    def import_font(self):
        return import_module(self.module_qualname())

    @log_func_call(DEBUGLOW2, trace_only=True)
    def get_font_class(self):
        mod = self.import_font()
        classname = self.classname
        return getattr(mod, classname)
