import sys

from .gui.icons.browser.app import IconBrowserApp

# from pathlib import Path
# HERE = Path(__file__).parent
# BROWSERDIR = HERE.parent
# ICONSDIR = BROWSERDIR.parent
# GUIDIR = ICONSDIR.parent
# PYAPPDIR = GUIDIR.parent
# REPO_DIR = PYAPPDIR.parent

args = sys.argv[1:]
if args[0] == 'log_func_call':
    from .tools.add_log_func_call_decorators import main as main_log_func_call
    if len(args) > 1:
        config_path = args[1]
        main_log_func_call(['.'], config_path=config_path)
    else:
        main_log_func_call(['.'])

else:
    IconBrowserApp.run_cmdline()
