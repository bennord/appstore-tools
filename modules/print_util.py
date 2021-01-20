import pygments
from pygments.lexers.data import JsonLexer
from pygments.formatters.terminal import TerminalFormatter
import json
import colorama
from typing import Any


def json_term(obj: Any):
    """Stringifies the object with json syntax highlighting for the terminal."""
    obj_formatted = json.dumps(obj, indent=2)
    return pygments.highlight(
        code=obj_formatted, lexer=JsonLexer(), formatter=TerminalFormatter()
    )


def clr(*colored_text: str, sep: str = "") -> str:
    """Add the color reset code after each colored_text."""
    return (sep + colorama.Style.RESET_ALL).join(
        colored_text
    ) + colorama.Style.RESET_ALL


def print_clr(*colored_text: str, sep: str = ""):
    """Add the color reset code after each colored_text."""
    print(clr(*colored_text, sep=sep))


EXTRA_INFO_COLOR = colorama.Style.DIM
KEYWORD_COLOR = colorama.Style.DIM + colorama.Fore.LIGHTCYAN_EX
USAGE_COLOR = colorama.Style.DIM + colorama.Fore.CYAN

clr_extra = lambda x: clr(EXTRA_INFO_COLOR + x)
clr_keyword = lambda x: clr(KEYWORD_COLOR + x)
clr_usage = lambda x: clr(USAGE_COLOR + x)
