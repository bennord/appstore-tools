import pygments
from pygments.lexers.data import JsonLexer
from pygments.formatters.terminal import TerminalFormatter
import json
import colorama


def print_json(obj: any):
    obj_formatted = json.dumps(obj, indent=2)
    obj_formatted_colored = pygments.highlight(
        code=obj_formatted,
        lexer=JsonLexer(),
        formatter=TerminalFormatter())
    print(obj_formatted_colored)


def print_color_reset(text: str):
    print(text + colorama.Style.RESET_ALL)
