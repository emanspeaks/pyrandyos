from typing import TYPE_CHECKING
if TYPE_CHECKING:
    def get_ipython():
        pass

from ..logging import log_func_call, DEBUGLOW


@log_func_call
def is_notebook() -> bool:  # pragma: no cover
    # taken from: https://stackoverflow.com/a/39662359/13230486
    ipy = get_ipython_if_running()
    if ipy:
        shell = ipy.__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        elif ipy.__class__.__module__ == "google.colab._shell":
            # https://stackoverflow.com/questions/15411967/how-can-i-check-if-code-is-executed-in-the-ipython-notebook#comment93642570_39662359  # noqa: E501
            return False  # Google Colab...but maybe should be true?
    return False  # Probably standard Python interpreter or something unknown


@log_func_call(DEBUGLOW)
def get_ipython_if_running():
    try:
        return get_ipython()
    except NameError:
        return None
