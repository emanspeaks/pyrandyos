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


class ScreenControl:
    ClearLine = f'{CSI}2K'
    ClearScreen = f'{CSI}2J'
    EraseToEOL = f'{CSI}K'
    SaveCursor = f'{CSI}s'
    RestoreCursor = f'{CSI}u'

    @staticmethod
    # @log_func_call
    def put_cursor_at_line_col(line: int, col: int):
        # return ff'{CSI}{line};{col}f'
        return f'{CSI}{line};{col}H'

    @staticmethod
    # @log_func_call
    def move_cursor_up(n: int):
        return f'{CSI}{n}A'

    @staticmethod
    # @log_func_call
    def move_cursor_down(n: int):
        return f'{CSI}{n}B'

    @staticmethod
    # @log_func_call
    def move_cursor_fwd(n: int):
        return f'{CSI}{n}C'

    @staticmethod
    # @log_func_call
    def move_cursor_bwd(n: int):
        return f'{CSI}{n}D'


# @log_func_call
def render_console_string(s: str):
    """
    parses a string with ANSI control characters and generates the equivalent
    after all characters are played
    """
    lines = ['']
    col = 0
    row = 0
    esc = None
    mcol = None
    mrow = None
    for c in s:
        if esc is not None:
            if (esc + c) == CSI:
                esc = ''
            elif c in 'ABCDHfmKJsu':
                if c in 'ABCD':
                    esc = int(esc) if esc else 1
                    if c == 'A':
                        row -= esc

                    elif c == 'B':
                        row += esc

                    elif c == 'C':
                        col += esc

                    elif c == 'D':
                        col -= esc

                elif c == 'K':
                    esc = int(esc) if esc else 0
                    # if esc == 0:
                    #     pass  # clear to EOL
                    #
                    # elif esc == 1:
                    #     pass  # clear to BOL
                    #
                    # elif esc == 2:
                    #     pass  # clear line
                    raise NotImplementedError

                elif c == 'J':
                    esc = int(esc) if esc else 0
                    if esc == 2:
                        lines = ['']
                        col = 0
                        row = 0

                    else:
                        raise NotImplementedError

                elif c == 's':
                    mcol = col
                    mrow = row

                elif c == 'u':
                    col = mcol
                    row = mrow

                elif c in 'Hf':
                    row, col = esc.split(';')
                    row = int(row) - 1
                    col = int(col) - 1

                esc = None

            else:
                esc += c

        elif c == '\033':
            esc = c

        elif c == '\r':
            col = 0

        elif c == '\n':
            row += 1
            col = 0
            if row == len(lines):
                lines.append('')

        else:
            linediff = row - len(lines) + 1
            if linediff > 0:
                lines += ['']*linediff

            old = lines[row]
            n = len(old)
            if col > n:
                old = ' '*col
            lines[row] = old[:col] + c + old[col + 1:]
            col += 1

    return '\n'.join(lines)
