import os
import requests
import colorama
from typing import Union
from enum import Enum, auto
from modules.print_util import print_clr, clr, json_term


def fetch_screenshot(screenshot_info: dict):
    attr = screenshot_info["attributes"]
    file_ext = os.path.splitext(attr["fileName"])[1]
    width = attr["imageAsset"]["width"]
    height = attr["imageAsset"]["height"]
    url_template = attr["imageAsset"]["templateUrl"]

    url = url_template.format(w=width, h=height, f=file_ext[1:])
    return requests.get(url)


def write_binary_file(path: str, content: bytes) -> None:
    with open(file=path, mode="wb") as file:
        file.write(content)


def write_txt_file(path: str, content: str) -> None:
    with open(file=path, mode="w") as file:
        file.write(content)


def read_txt_file(
    path: str,
) -> Union[str, None]:  # pylint: disable=unsubscriptable-object
    try:
        with open(file=path, mode="r") as file:
            return file.read()
    except FileNotFoundError:
        return None


def print_locale_status(locale: str, color: str, status: str):
    print_clr(f"  {color}{locale:5}{colorama.Style.RESET_ALL} - {status}")


def print_screenshot_set_status(display_type: str, color: str, status: str):
    print_clr(f"    {color}{display_type}{colorama.Style.RESET_ALL} - {status}")


def print_screenshot_status(file_name: str, color: str, status: str):
    print_clr(f"      {color}{file_name}{colorama.Style.RESET_ALL} - {status}")