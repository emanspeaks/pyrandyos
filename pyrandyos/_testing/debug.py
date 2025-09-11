import sys


def is_debug_enabled():
    # see https://stackoverflow.com/a/77627047/13230486
    try:
        if sys.gettrace() is not None:
            return True
    except AttributeError:
        pass

    try:
        if sys.monitoring.get_tool(sys.monitoring.DEBUGGER_ID) is not None:
            return True
    except AttributeError:
        pass

    return False


def hide_splash():
    from pyrandyos.gui.gui_app import get_gui_app
    gui_app = get_gui_app()
    if gui_app and gui_app.splash:
        splash = gui_app.splash.gui_view.qtobj
        if splash.isVisible():
            splash.hide()
            if is_debug_enabled():
                print("Splash screen hidden, debugger is enabled")
            else:
                print("Splash screen hidden")
        else:
            print("Splash screen is already hidden")
    else:
        print("No splash screen to hide")
