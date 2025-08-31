# The MIT License
#
# Copyright (c) 2015 The Spyder development team
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from ...qt import QThread, QFontDatabase, QFont, QRawFont
from ....logging import log_func_call, DEBUGLOW2
from .sources import THIRDPARTY_FONTSPEC

_DEFHINT = QFont.PreferDefaultHinting


class IconFontNotInitializedError(RuntimeError):
    pass


class IconFontCacheEntry:
    @log_func_call(DEBUGLOW2, trace_only=True)
    def __init__(self):
        self.ttf_data: bytes = None
        self.id_: int | None = None
        self.font_name: str = None
        self.rawfont: dict[str, QRawFont] = dict()


class IconFontMeta(type):
    @log_func_call(DEBUGLOW2, trace_only=True)
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        cls._cache = IconFontCacheEntry()


class IconFont(metaclass=IconFontMeta):
    _SPECNAME: str

    @classmethod
    @log_func_call(DEBUGLOW2, trace_only=True)
    def get_spec(cls):
        return THIRDPARTY_FONTSPEC[cls._SPECNAME]

    @log_func_call
    def __init__(self):
        self.ensure_font_loaded()

    @classmethod
    @log_func_call(DEBUGLOW2, trace_only=True)
    def get_font(cls, size: float | int):
        "Return a QFont corresponding to the given prefix and size."
        cls.ensure_font_loaded()
        spec = cls.get_spec()
        cache = cls._cache
        font = QFont()
        font.setFamily(cache.font_name)
        font.setPixelSize(round(size))
        if spec.solid:  # solid style
            font.setStyleName("Solid")
        return font

    @classmethod
    @log_func_call(DEBUGLOW2, trace_only=True)
    def get_rawfont(cls, size: float | int,
                    hintingpref: QFont.HintingPreference = _DEFHINT):
        cls.ensure_font_loaded()
        clscache = cls._cache
        cache = clscache.rawfont
        thread = QThread.currentThread()
        tid = str(thread)
        tc = cache.get(tid)
        if not tc:
            tc = dict()
            cache[tid] = tc
            thread.finished.connect(lambda: cache.pop(tid, None))

        key = (size, hintingpref)
        rawfont = tc.get(key)
        if not rawfont:
            rawfont = QRawFont(clscache.ttf_data, size, hintingpref)
            tc[key] = rawfont

        return rawfont

    @classmethod
    @log_func_call(DEBUGLOW2, trace_only=True)
    def ensure_font_loaded(cls):
        cache = cls._cache
        if cache.id_ is None:
            spec = cls.get_spec()
            ttf_path = spec.ttf_filespec.get_local_path()
            fontdata = ttf_path.read_bytes()
            id_ = QFontDatabase.addApplicationFontFromData(fontdata)
            loadedFontFamilies = QFontDatabase.applicationFontFamilies(id_)
            if loadedFontFamilies:
                cache.ttf_data = fontdata
                cache.id_ = id_
                cache.font_name = loadedFontFamilies[0]
            else:
                raise RuntimeError(
                    f"Font '{ttf_path}' appears to be empty. "
                    "If you are on Windows 10, please read "
                    "https://support.microsoft.com/en-us/kb/3053676 "
                    "to know how to prevent Windows from blocking "
                    "the fonts that come with the package."
                )

    @classmethod
    @log_func_call(DEBUGLOW2, trace_only=True)
    def get_codepoint_by_name(cls, icon_name: str):
        charmap = cls.get_spec().charmap
        if charmap:
            return charmap.get(icon_name, None)
        raise IconFontNotInitializedError("Qt application must be initialized "
                                          "before using icon font methods "
                                          "that require the fonts to "
                                          "be loaded.")

    @classmethod
    @log_func_call(DEBUGLOW2, trace_only=True)
    def get_glyph(cls, name_or_codepoint: str | int):
        i = name_or_codepoint
        if isinstance(name_or_codepoint, str):
            i = cls.get_codepoint_by_name(name_or_codepoint)
            if i is None:
                raise ValueError(f"Glyph '{name_or_codepoint}' not found "
                                 "in charmap.")
        return chr(i)
