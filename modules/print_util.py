import pygments
from pygments.lexers.data import JsonLexer
from pygments.formatters.terminal import TerminalFormatter
import json
import colorama


def json_term(obj: any):
    """Stringifies the object with json syntax highlighting for the terminal."""
    obj_formatted = json.dumps(obj, indent=2)
    return pygments.highlight(
        code=obj_formatted,
        lexer=JsonLexer(),
        formatter=TerminalFormatter())


def color_term(text: str):
    """Add the reset code for text using colorama color/style codes."""
    return text + colorama.Style.RESET_ALL
