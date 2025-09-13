from ..logging import log_func_call, DEBUGLOW2, DEBUG

from . import GuiPresenter
from .widgets import GuiWindowLikeView
from .qt import (
    QSplashScreen, QPixmap, QProgressBar, QLabel, Qt, QMouseEvent, QRect,
    QPalette,
)
from .loadstatus import LOAD_STEP_REGISTRY


class GuiSplashScreen(GuiPresenter['GuiSplashScreenView']):
    def __init__(self, pixmap: QPixmap = None, *view_args,
                 text: str = "Loading...", **view_kwargs):
        super().__init__(None, pixmap, *view_args, text=text, **view_kwargs)

    def create_gui_view(self, pixmap: QPixmap = None, *view_args,
                        text: str = "Loading...", **view_kwargs):
        return GuiSplashScreenView(self, pixmap, *view_args, text=text,
                                   **view_kwargs)

    def mousePressEvent(self, event: QMouseEvent):
        # Prevent the splash from being closed by mouse click
        pass

    def post_show_init(self):
        "Any initialization that should be executed after the window is shown"
        pass

    def show(self):
        self.gui_view.show()

    @log_func_call(DEBUGLOW2, trace_only=True)
    def set_progress(self, *, value: int = None, message: str = None,
                     process_events: bool = True):
        view = self.gui_view
        progress = view.progress
        mymax = progress.maximum()
        refresh = mymax // 200 or 1
        process_events = process_events and ((message and value is None)
                                             or (value
                                                 and value % refresh == 0)
                                             or value == mymax
                                             or value == 0
                                             )

        if value is not None:
            progress.setValue(value)

        if message:
            view.label.setText(message)
            # self.qtobj.showMessage(message,
            #                         Qt.AlignBottom | Qt.AlignHCenter,
            #                         Qt.white)

        if process_events:
            self.qt_app.processEvents()


class GuiSplashScreenView(GuiWindowLikeView[GuiSplashScreen, QSplashScreen]):
    @log_func_call(DEBUG)
    def __init__(self, presenter: GuiSplashScreen, pixmap: QPixmap = None,
                 *qtobj_args, text: str = "Loading...", **qtobj_kwargs):
        GuiWindowLikeView.__init__(self, text, presenter, pixmap, *qtobj_args,
                                   **qtobj_kwargs)
        qtobj = self.qtobj
        qtobj.mousePressEvent = presenter.mousePressEvent
        self.center_window_in_current_screen()

        self.rect = pixmap.rect() if pixmap else QRect(0, 0, 400, 400)
        self.gridsize = 20
        self.default_text = text
        self.create_pb()
        self.create_label()

    @log_func_call(DEBUGLOW2, trace_only=True)
    def create_qtobj(self, pixmap: QPixmap = None,
                     flags: Qt.WindowFlags = Qt.WindowStaysOnTopHint,
                     *args, **kwargs):
        return QSplashScreen(pixmap or QPixmap(), flags, *args, **kwargs)

    def create_pb(self):
        qtobj = self.qtobj
        gridsize = self.gridsize
        rect = self.rect

        pb = QProgressBar(qtobj)
        pb.setGeometry(gridsize, round((rect.height() + gridsize)*0.75),
                       rect.width() - 2*gridsize, gridsize)
        pb.setRange(0, len(LOAD_STEP_REGISTRY) or 1)
        pb.setValue(0)
        pb.setStyleSheet('''
            QProgressBar {
                background-color: #19232D;
                border: 1px solid #455364;
                color: #DFE1E2;
                border-radius: 4px;
                text-align: center;
            }

            QProgressBar:disabled {
                background-color: #19232D;
                border: 1px solid #455364;
                color: #788D9C;
                border-radius: 4px;
                text-align: center;
            }

            QProgressBar::chunk {
                background-color: #346792;
                color: #19232D;
                border-radius: 4px;
            }

            QProgressBar::chunk:disabled {
                background-color: #26486B;
                color: #788D9C;
                border-radius: 4px;
            }
        ''')
        self.progress = pb

    def create_label(self):
        qtobj = self.qtobj
        gridsize = self.gridsize
        rect = self.rect
        text = self.default_text

        lbl = QLabel(qtobj)
        lbl.setGeometry(gridsize, round((rect.height() - gridsize)*0.75),
                        rect.width() - 2*gridsize, gridsize)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setText(text)
        palette = lbl.palette()
        palette.setColor(QPalette.Window, lbl.palette().color(QPalette.Window))
        lbl.setAutoFillBackground(True)
        lbl.setPalette(palette)
        lbl.setStyleSheet('''
            QLabel {
                padding: 2px 8px;
                background: #444a5a;
                color: #fff;
                border-radius: 4px;
            }
        ''')
        self.label = lbl
