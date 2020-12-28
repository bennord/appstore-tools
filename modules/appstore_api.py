import jwt
import time
import requests
import json
import gzip
import colorama
from .print_util import print_json, print_color_reset

APPSTORE_URI_ROOT = "https://api.appstoreconnect.apple.com/v1"
APPSTORE_AUDIENCE = "appstoreconnect-v1"
APPSTORE_JWT_ALGO = "ES256"


def create_access_token(issuer_id: str, key_id: str, key: str) -> str:
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
        post_data=None,
        verbose:        bool = False):
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

    if verbose:
        print_color_reset(
            f"{colorama.Fore.GREEN}appstore_api.fetchApi: {colorama.Fore.MAGENTA}{url}")
        print_json(result)
    return result
