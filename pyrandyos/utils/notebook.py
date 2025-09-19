from typing import TYPE_CHECKING
if TYPE_CHECKING:
    def get_ipython():
        pass

from ..logging import log_func_call, DEBUGLOW


@log_func_call
def is_notebook() -> bool:  # pragma: no cover
    return get_interpreter() == 'notebook'


@log_func_call(DEBUGLOW)
def get_ipython_if_running():
    try:
        return get_ipython()
    except NameError:
        return None


@log_func_call
def get_interpreter():
    # adapted from: https://stackoverflow.com/a/39662359/13230486
    ipy = get_ipython_if_running()
    if ipy:
        cls = ipy.__class__
        shell = cls.__name__
        if shell == 'ZMQInteractiveShell':
            return 'notebook'   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return 'ipython'  # Terminal running IPython
        elif cls.__module__ == "google.colab._shell":
            # https://stackoverflow.com/questions/15411967/how-can-i-check-if-code-is-executed-in-the-ipython-notebook#comment93642570_39662359  # noqa: E501
            return 'google'  # Google Colab...but maybe should be true?
        return 'unknown'  # Other type (?)
    return 'python'  # Probably standard Python interpreter
