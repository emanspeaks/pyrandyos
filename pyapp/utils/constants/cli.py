# from ..logging import log_func_call
# see https://stackoverflow.com/a/33206814/13230486
CSI = '\033['  # https://en.wikipedia.org/wiki/ANSI_escape_code#CSIsection


class ConsoleText:
    Reset = f'{CSI}0m'
    ResetText = f'{CSI}39m'
    ResetBg = f'{CSI}49m'

    Bold = f'{CSI}1m'
    NoBold = f'{CSI}21m'
    Underline = f'{CSI}4m'
    NoUnderline = f'{CSI}24m'
    Strikethrough = f'{CSI}4m'
    NoStrikethrough = f'{CSI}24m'

    GrayText = f'{CSI}90m'
    RedText = f'{CSI}91m'
    GreenText = f'{CSI}92m'
    YellowText = f'{CSI}93m'
    BlueText = f'{CSI}94m'
    MagentaText = f'{CSI}95m'
    CyanText = f'{CSI}96m'
    WhiteText = f'{CSI}97m'

    BlackText = f'{CSI}30m'
    DarkRedText = f'{CSI}31m'
    DarkGreenText = f'{CSI}32m'
    DarkYellowText = f'{CSI}33m'
    DarkBlueText = f'{CSI}34m'
    DarkMagentaText = f'{CSI}35m'
    DarkCyanText = f'{CSI}36m'
    DarkWhiteText = f'{CSI}37m'

    GrayBg = f'{CSI}100m'
    RedBg = f'{CSI}101m'
    GreenBg = f'{CSI}102m'
    YellowBg = f'{CSI}103m'
    BlueBg = f'{CSI}104m'
    MagentaBg = f'{CSI}105m'
    CyanBg = f'{CSI}106m'
    WhiteBg = f'{CSI}107m'

    BlackBg = f'{CSI}40m'
    DarkRedBg = f'{CSI}41m'
    DarkGreenBg = f'{CSI}42m'
    DarkYellowBg = f'{CSI}43m'
    DarkBlueBg = f'{CSI}44m'
    DarkMagentaBg = f'{CSI}45m'
    DarkCyanBg = f'{CSI}46m'
    DarkWhiteBg = f'{CSI}47m'


class ScreenControlCmds:
    ClearLine = f'{CSI}2K'
    ClearScreen = f'{CSI}2J'
    EraseToEOL = f'{CSI}K'
    SaveCursor = f'{CSI}s'
    RestoreCursor = f'{CSI}u'
