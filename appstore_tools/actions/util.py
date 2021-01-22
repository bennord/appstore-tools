import os
import requests
import colorama
from typing import Union
from enum import Enum, auto
from appstore_tools.print_util import print_clr, clr, json_term


def fetch_screenshot(screenshot: dict):
    """Fetches screenshot data. Retuns None if screenshot has no asset."""
    attr = screenshot["attributes"]
    file_ext = os.path.splitext(attr["fileName"])[1]
    if attr["imageAsset"] is None:
        return None

    width = attr["imageAsset"]["width"]
    height = attr["imageAsset"]["height"]
    url_template = attr["imageAsset"]["templateUrl"]

    url = url_template.format(w=width, h=height, f=file_ext[1:])
    return requests.get(url)


def fetch_preview(preview: dict):
    """Fetches screenshot data. Retuns None if screenshot has no asset."""
    attr = preview["attributes"]
    url = attr["videoUrl"]
    if url is None:
        return None
    else:
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


def print_info_status(info_state: str, status: str):
    print_clr(f"{colorama.Fore.CYAN}{info_state}", f" - {status}")


def print_version_status(version_state: str, platform: str, status: str):
    print_clr(
        f"{colorama.Fore.CYAN}{version_state} ",
        f"{colorama.Fore.CYAN + colorama.Style.DIM}{{{platform}}}",
        f" - {status}",
    )


def print_locale_status(locale: str, color: str, status: str):
    print_clr(f"  {color}{locale:5}", f" - {status}")


def print_media_set_status(display_type: str, color: str, status: str):
    print_clr(f"    {color}{display_type}", f" - {status}")


def print_media_status(file_name: str, color: str, status: str):
    print_clr(f"      {color}{file_name}", f" - {status}")
