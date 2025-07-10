from collections.abc import Callable

from PySide2.QtWidgets import QApplication

from ...logging import log_func_call
from .styles import dark, light, vibedark, HAS_QDARKSTYLE

DEFAULT_THEME_NAME = '(default)'
STATUS_LABEL = 'status_label'  # used in stylesheet for status label


class ThemeMap:
    @log_func_call
    def __init__(self, app: QApplication):
        self.app = app
        self.__custom_themes: dict[str, Callable] = dict()
        self.__current: str = None
        self.init_themes()

    @log_func_call
    def create_theme(self, name: str, callback: Callable = None):
        themes = self.__custom_themes
        if name not in themes:
            themes[name.lower()] = callback if callback else self.default_theme

    @log_func_call
    def init_themes(self):
        self.create_theme('light', light)
        self.create_theme('dark', dark if HAS_QDARKSTYLE else vibedark)
        self.create_theme('vibedark', vibedark)

    @log_func_call
    def apply_theme(self, name: str = None):
        if not name or name == DEFAULT_THEME_NAME:
            self.default_theme(self.app)
        else:
            self.__custom_themes[name.lower()](self.app)

        self.__current = name

    @log_func_call
    def get_current_theme(self):
        return self.__current

    @log_func_call
    def list_themes(self, always_include_dark: bool = True,
                    include_default: bool = True):
        tmp = list(self.__custom_themes.keys())
        if not HAS_QDARKSTYLE and not always_include_dark and 'dark' in tmp:
            tmp.remove('dark')
        if include_default and DEFAULT_THEME_NAME not in tmp:
            tmp.append(DEFAULT_THEME_NAME)
        return tmp

    @classmethod
    @log_func_call
    def default_theme(cls, app: QApplication):
        app.setPalette(app.style().standardPalette())
        app.setStyleSheet('')
