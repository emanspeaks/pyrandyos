from collections.abc import Callable

from PySide2.QtWidgets import QApplication

from ...logging import log_func_call
from .dark import dark_theme

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
            themes[name] = callback if callback else self.default_theme

    @log_func_call
    def init_themes(self):
        self.create_theme('Light', self.default_theme)
        self.create_theme('Dark', dark_theme)

    @log_func_call
    def apply_theme(self, name: str = None):
        if not name or name == DEFAULT_THEME_NAME:
            self.default_theme(self.app)
        else:
            self.__custom_themes[name](self.app)

        self.__current = name

    @log_func_call
    def get_current_theme(self):
        return self.__current

    @log_func_call
    def list_themes(self):
        return list(self.__custom_themes.keys())

    @classmethod
    @log_func_call
    def default_theme(cls, app: QApplication):
        app.setPalette(app.style().standardPalette())
        app.setStyleSheet('')
