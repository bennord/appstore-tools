import jwt
import time
import requests
import json
import gzip
import colorama
import logging
from .print_util import json_term, color_term

APPSTORE_URI_ROOT = "https://api.appstoreconnect.apple.com/v1"
APPSTORE_AUDIENCE = "appstoreconnect-v1"
APPSTORE_JWT_ALGO = "ES256"


def create_access_token(
    issuer_id: str,
    key_id: str,
    key: str
) -> str:
    """Create an access token for use in the AppStore Connect API."""

    # The token's expiration time, in Unix epoch time; tokens that expire more than
    # 20 minutes in the future are not valid (Ex: 1528408800)
    experation = int(time.time()) + 20 * 60

    # AppStore JWT
    # https://developer.apple.com/documentation/appstoreconnectapi/generating_tokens_for_api_requests
    access_token = jwt.encode({
        "iss": issuer_id,
        "exp": experation,
        "aud": APPSTORE_AUDIENCE
    }, key, algorithm=APPSTORE_JWT_ALGO, headers={
        "kid": key_id})
    return access_token


def fetch(
        path: str,
        method: str,
        access_token: str,
        post_data=None
):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = {}

    url = (APPSTORE_URI_ROOT + path if path.startswith("/") else path)

    method = method.lower()
    if method == "get":
        response = requests.get(url, headers=headers)
    elif method == "post":
        headers["Content-Type"] = "application/json"
        response = requests.post(
            url=url, headers=headers, data=json.dumps(post_data))
    elif method == "patch":
        headers["Content-Type"] = "application/json"
        response = requests.patch(url=url, headers=headers,
                                  data=json.dumps(post_data))

    content_type = response.headers['content-type']

    if content_type == "application/json":
        result = response.json()
    elif content_type == 'application/a-gzip':
        # TODO implement stream decompress
        data_gz = b""
        for chunk in response.iter_content(1024 * 1024):
            if chunk:
                data_gz = data_gz + chunk

        data = gzip.decompress(data_gz)
        result = data.decode("utf-8")
    else:
        result = response

    logging.info(
        color_term(f"{colorama.Fore.GREEN}appstore_api.fetchApi: {colorama.Fore.MAGENTA}{url}\n") +
        json_term(result))
    return result


def get_apps(
    access_token: str,
):
    return fetch(
        path=f"/apps",
        method="get",
        access_token=access_token)


def get_app_id(
    bundle_id: str,
    access_token: str,
) -> int:
    apps = fetch(
        path=f"/apps",
        method="get",
        access_token=access_token)["data"]

    app_id = next(app["id"] for app in apps
                  if app["attributes"]["bundleId"] == bundle_id)
    return int(app_id)


def get_app(
    app_id: str,
    access_token: str,
):
    return fetch(
        path=f"/apps/{app_id}",
        method="get",
        access_token=access_token)["data"]
