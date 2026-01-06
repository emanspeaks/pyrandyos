from ..config.keys import LOCAL_CFG_KEY, MONOFONT_KEY
from ..logging import log_exc, log_func_call, DEBUGLOW2, log_debug, log_info
from ..app import PyRandyOSApp
from . import GuiQtWrapper
from .styles import ThemeMap
from .window import GuiWindow
from .splash import GuiSplashScreen
from .loadstatus import load_status_step, splash_message
from .qrc import compile_qrc, import_qrc
from .qt import (
    QWidget, QApplication, qVersion, QObject, QEvent, QPixmap, Qt, QFont,
)

_GUI_APP_INST: 'GuiApp | None' = None


@log_func_call
def get_gui_app():
    global _GUI_APP_INST
    if not _GUI_APP_INST:
        raise RuntimeError("Qt application instance is not initialized.")
    return _GUI_APP_INST


class QtApp(QApplication):
    # only log user code, but can uncomment if you want to log all Qt events
    # @log_func_call(DEBUGLOW2)
    def notify(self, receiver: QObject, event: QEvent):
        try:
            # Add defensive checks to prevent the parameter mixup issue
            if isinstance(receiver, QEvent):
                receiver

            if not isinstance(receiver, QObject):
                raise RuntimeError("notify() called with invalid receiver "
                                   f"type: {type(receiver)}. Expected QObject")
            if not isinstance(event, QEvent):
                raise RuntimeError("notify() called with invalid event type: "
                                   f"{type(event)}. Expected QEvent")

            return super().notify(receiver, event)
        except BaseException as e:
            log_exc(e)
            return False


class GuiApp(GuiQtWrapper):
    INIT_GUI_IN_CONSTRUCTOR: bool = True

    @log_func_call(DEBUGLOW2, trace_only=True)
    def __init__(self, app_args: list[str], *firstwin_args, **firstwin_kwargs):
        log_debug('initializing application')
        global _GUI_APP_INST
        if _GUI_APP_INST is not None:
            raise RuntimeError(
                "A Qt application instance already exists for this Python "
                "process. Only one instance is allowed per Python process."
            )
        _GUI_APP_INST = self
        self.gui_initialized = False

        super().__init__(None)
        self.qtobj: QApplication

        self.themes: ThemeMap = None
        self.windows: list[GuiWindow] = list()
        self.splash: GuiSplashScreen = None
        if self.INIT_GUI_IN_CONSTRUCTOR:
            self.init_gui(app_args, *firstwin_args, **firstwin_kwargs)

    @log_func_call
    def create_splash(self, *args, **kwargs) -> GuiSplashScreen:
        return GuiSplashScreen(QPixmap(), *args, **kwargs)

    @load_status_step("GUI initialized", show_step_done=True,
                      show_step_start=False)
    @log_func_call
    def init_gui(self, app_args: list[str], *firstwin_args, **firstwin_kwargs):
        log_debug('starting app main')

        # Ensure Qt resources are registered before any widgets are created
        compile_qrc()
        import_qrc()

        app = self.create_qt_inst(app_args)
        super().__init__(app)
        PyRandyOSApp.set('Qt_version', qVersion())

        splash = self.create_splash()
        if splash:
            splash.show()
            app.processEvents()
            self.splash = splash

        from .icons.iconfont import init_iconfonts
        init_iconfonts()

        self.init_themes()
        self.set_theme()
        # set_high_dpi_support(log=log)
        self.create_first_window(*firstwin_args, **firstwin_kwargs)
        self.gui_initialized = True

    def process_events(self):
        qtobj = self.qtobj
        if qtobj:
            qtobj.processEvents()

    @log_func_call
    def main(self, *args, **kwargs):
        if not self.gui_initialized:
            self.init_gui(*args, **kwargs)

        log_debug('starting Qt main loop')
        splash_message("Main loop starting")
        self.qtobj.exec_()

    @log_func_call
    @load_status_step("Initializing themes")
    def init_themes(self):
        self.themes = ThemeMap(self.qtobj)

    @log_func_call
    def set_theme(self, t: str = None):
        tnew = t
        t = t or PyRandyOSApp[f'{LOCAL_CFG_KEY}.theme']
        log_debug(f'setting theme to {t}')
        if tnew:
            PyRandyOSApp.set(f'{LOCAL_CFG_KEY}.theme', t)

        themes = self.themes
        themes.apply_theme()  # reset theme to default
        themes.apply_theme(t)

    @log_func_call
    def get_theme(self):
        return self.themes.get_current_theme()

    @log_func_call
    def create_qt_inst(self, app_args: list[str] = []):
        self.set_high_dpi_support()
        return QtApp(list(app_args))

    @log_func_call
    def create_first_window(self, *args, **kwargs):
        "create and show the first window after app launch"
        raise NotImplementedError('Abstract method not implemented')

    @log_func_call
    def close_splash(self, delegate: QWidget = None):
        if self.splash:
            qtsplash = self.splash.gui_view.qtobj
            qtsplash.finish(delegate)
            self.splash = None

    @log_func_call
    def set_high_dpi_support(self):
        # Attribute Qt::AA_EnableHighDpiScaling must be set before
        # QCoreApplication is created.
        try:
            QtApp.setAttribute(Qt.AA_EnableHighDpiScaling)
            QtApp.setAttribute(Qt.AA_UseHighDpiPixmaps)
        except Exception as e:
            # log_info("Failed to set high DPI support", exc_info=e)
            # on second thought, we don't need a full traceback
            log_info(f"Failed to set high DPI support: {e}")

    @log_func_call
    def get_dpi(self):
        return self.qtobj.primaryScreen().logicalDotsPerInch()

    @log_func_call
    def get_dpi_scale(self):
        return self.get_dpi() / 96.0

    @log_func_call
    def get_monofont(self):
        font = QFont(PyRandyOSApp[MONOFONT_KEY])
        font.setStyleHint(QFont.Monospace)
        return font
