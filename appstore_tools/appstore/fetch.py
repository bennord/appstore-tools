import logging
import colorama
import json
import requests
import gzip
from enum import Enum, auto
from typing import Union
from appstore_tools.print_util import clr, json_term
from .util import enum_name
from .exceptions import ResourceNotFoundException

APPSTORE_URI_ROOT = "https://api.appstoreconnect.apple.com/v1"


class FetchMethod(Enum):
    GET = auto()
    POST = auto()
    PATCH = auto()
    DELETE = auto()


def fetch(
    method: Union[FetchMethod, str],  # pylint: disable=unsubscriptable-object
    path: str,
    access_token: str,
    headers: dict = {},
    data=None,
):
    """Fetch a URL resource via the AppStore connect api."""
    headers = {"Authorization": f"Bearer {access_token}", **headers}

    url = APPSTORE_URI_ROOT + path if path.startswith("/") else path

    logging.debug(
        clr(
            f"{colorama.Fore.GREEN}appstore.fetch: {enum_name(method)} {colorama.Fore.MAGENTA}{url}\n",
            f"{colorama.Fore.BLUE}request body:\n",
            json_term(data),
        )
    )

    if not isinstance(method, FetchMethod):
        try:
            method = FetchMethod[method]
        except KeyError:
            raise ValueError(
                f"{method} is not a valid FetchMethod. Options are {list(FetchMethod)}"
            )
    if method == FetchMethod.GET:
        response = requests.get(url=url, headers=headers)
    elif method == FetchMethod.POST:
        headers["Content-Type"] = "application/json"
        response = requests.post(url=url, headers=headers, data=json.dumps(data))
    elif method == FetchMethod.PATCH:
        headers["Content-Type"] = "application/json"
        response = requests.patch(url=url, headers=headers, data=json.dumps(data))
    elif method == FetchMethod.DELETE:
        response = requests.delete(url=url, headers=headers)

    content_type = response.headers["content-type"]

    if content_type == "application/json":
        result = response.json()
        logging.debug(clr(f"{colorama.Fore.BLUE}response body:\n", json_term(result)))
    elif content_type == "application/a-gzip":
        # TODO implement stream decompress
        zipped_data = b""
        for chunk in response.iter_content(1024 * 1024):
            if chunk:
                zipped_data += chunk

        unzipped_data = gzip.decompress(zipped_data)
        result = unzipped_data.decode("utf-8")
    else:
        result = response

    # raise exceptions for easier handling
    if response.status_code == 404:
        raise ResourceNotFoundException(
            f'{method.name} {url} (HttpError {response.status_code})\n{json_term({"request": data, "response":result})}'
        )
    elif not response.ok:
        raise requests.exceptions.HTTPError(
            f'{url} {method.name} (HttpError {response.status_code})\n{json_term({"request": data, "response":result})}'
        )

    return result
