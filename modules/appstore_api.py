import jwt
import time
import requests
import json
import gzip
import colorama
import logging
from enum import Enum, auto
from .print_util import json_term, color_term

APPSTORE_URI_ROOT = "https://api.appstoreconnect.apple.com/v1"
APPSTORE_AUDIENCE = "appstoreconnect-v1"
APPSTORE_JWT_ALGO = "ES256"


class AppStoreVersionState(Enum):
    DEVELOPER_REMOVED_FROM_SALE = auto()
    DEVELOPER_REJECTED = auto()
    IN_REVIEW = auto()
    INVALID_BINARY = auto()
    METADATA_REJECTED = auto()
    PENDING_APPLE_RELEASE = auto()
    PENDING_CONTRACT = auto()
    PENDING_DEVELOPER_RELEASE = auto()
    PREPARE_FOR_SUBMISSION = auto()
    PREORDER_READY_FOR_SALE = auto()
    PROCESSING_FOR_APP_STORE = auto()
    READY_FOR_SALE = auto()
    REJECTED = auto()
    REMOVED_FROM_SALE = auto()
    WAITING_FOR_EXPORT_COMPLIANCE = auto()
    WAITING_FOR_REVIEW = auto()
    REPLACED_WITH_NEW_VERSION = auto()


def create_access_token(issuer_id: str, key_id: str, key: str) -> str:
    """Create an access token for use in the AppStore Connect API."""

    # The token's expiration time, in Unix epoch time; tokens that expire more than
    # 20 minutes in the future are not valid (Ex: 1528408800)
    experation = int(time.time()) + 20 * 60

    # AppStore JWT
    # https://developer.apple.com/documentation/appstoreconnectapi/generating_tokens_for_api_requests
    access_token = jwt.encode(
        {"iss": issuer_id, "exp": experation, "aud": APPSTORE_AUDIENCE},
        key,
        algorithm=APPSTORE_JWT_ALGO,
        headers={"kid": key_id},
    )
    return access_token


def fetch(path: str, method: str, access_token: str, post_data=None):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = {}

    url = APPSTORE_URI_ROOT + path if path.startswith("/") else path

    method = method.lower()
    if method == "get":
        response = requests.get(url, headers=headers)
    elif method == "post":
        headers["Content-Type"] = "application/json"
        response = requests.post(url=url, headers=headers, data=json.dumps(post_data))
    elif method == "patch":
        headers["Content-Type"] = "application/json"
        response = requests.patch(url=url, headers=headers, data=json.dumps(post_data))

    content_type = response.headers["content-type"]

    if content_type == "application/json":
        result = response.json()
    elif content_type == "application/a-gzip":
        # TODO implement stream decompress
        data_gz = b""
        for chunk in response.iter_content(1024 * 1024):
            if chunk:
                data_gz = data_gz + chunk

        data = gzip.decompress(data_gz)
        result = data.decode("utf-8")
    else:
        result = response

    logging.debug(
        color_term(
            f"{colorama.Fore.GREEN}appstore_api.fetchApi: {colorama.Fore.MAGENTA}{url}\n"
        )
        + json_term(result)
    )
    return result


def get_apps(
    access_token: str,
):
    return fetch(path=f"/apps", method="get", access_token=access_token)["data"]


def get_app_id(
    bundle_id: str,
    access_token: str,
) -> int:
    apps = get_apps(access_token)
    app_id = next(
        app["id"] for app in apps if app["attributes"]["bundleId"] == bundle_id
    )
    return int(app_id)


def get_app(
    app_id: str,
    access_token: str,
):
    return fetch(path=f"/apps/{app_id}", method="get", access_token=access_token)[
        "data"
    ]


def get_app_store_versions(
    app_id: str,
    access_token: str,
):
    return fetch(
        path=f"/apps/{app_id}/appStoreVersions", method="get", access_token=access_token
    )["data"]


def get_app_store_version(
    app_id: str,
    app_store_state: AppStoreVersionState,
    access_token: str,
):
    app_store_versions = get_app_store_versions(app_id, access_token)
    return next(
        v
        for v in app_store_versions
        if v["attributes"]["appStoreState"] == app_store_state
    )


def get_live_app_store_version(
    app_id: str,
    access_token: str,
):
    return get_app_store_version(
        app_id=app_id,
        app_store_state=AppStoreVersionState.READY_FOR_SALE,
        access_token=access_token,
    )
