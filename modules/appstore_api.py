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


class ResourceNotFoundException(Exception):
    pass


class FetchMethod(Enum):
    GET = auto()
    POST = auto()
    PATCH = auto()


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


def fetch(path: str, method: FetchMethod, access_token: str, post_data=None):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = {}

    url = APPSTORE_URI_ROOT + path if path.startswith("/") else path

    if method == FetchMethod.GET:
        response = requests.get(url, headers=headers)
    elif method == FetchMethod.POST:
        headers["Content-Type"] = "application/json"
        response = requests.post(url=url, headers=headers, data=json.dumps(post_data))
    elif method == FetchMethod.PATCH:
        headers["Content-Type"] = "application/json"
        response = requests.patch(url=url, headers=headers, data=json.dumps(post_data))

    if response.status_code == 404:
        raise ResourceNotFoundException(
            f"Resource not found at {url} (HttpError {404})"
        )

    response.raise_for_status()

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
            f"{colorama.Fore.GREEN}appstore_api.fetch: {colorama.Fore.MAGENTA}{url}\n"
        )
        + json_term(result)
    )
    return result


def get_apps(
    access_token: str,
):
    return fetch(path=f"/apps", method=FetchMethod.GET, access_token=access_token)[
        "data"
    ]


def get_app(
    app_id: str,
    access_token: str,
):
    return fetch(
        path=f"/apps/{app_id}", method=FetchMethod.GET, access_token=access_token
    )["data"]


def get_app_id(
    bundle_id: str,
    access_token: str,
) -> int:
    apps = get_apps(access_token)
    try:
        app_id = next(
            app["id"] for app in apps if app["attributes"]["bundleId"] == bundle_id
        )
        return int(app_id)
    except StopIteration:
        raise ResourceNotFoundException(f'No app matching bundle-id "{bundle_id}"')


def get_bundle_id(
    app_id: str,
    access_token: str,
) -> int:
    app = get_app(app_id=app_id, access_token=access_token)
    return app["attributes"]["bundleId"]


def get_app_versions(
    app_id: str,
    access_token: str,
):
    return fetch(
        path=f"/apps/{app_id}/appStoreVersions",
        method=FetchMethod.GET,
        access_token=access_token,
    )["data"]


def get_app_version(
    app_id: str,
    app_store_state: AppStoreVersionState,
    access_token: str,
):
    try:
        app_store_versions = get_app_versions(app_id, access_token)
        return next(
            v
            for v in app_store_versions
            if v["attributes"]["appStoreState"] == app_store_state.name
        )
    except StopIteration:
        raise ResourceNotFoundException(
            f'No app version matching state "{app_store_state.name}"'
        )


def get_app_live(
    app_id: str,
    access_token: str,
):
    return get_app_version(
        app_id=app_id,
        app_store_state=AppStoreVersionState.READY_FOR_SALE,
        access_token=access_token,
    )


def get_localizations(
    version_id: str,
    access_token: str,
):
    return fetch(
        path=f"/appStoreVersions/{version_id}/appStoreVersionLocalizations",
        method=FetchMethod.GET,
        access_token=access_token,
    )["data"]


def get_screenshot_sets(
    localization_id: str,
    access_token: str,
):
    return fetch(
        path=f"/appStoreVersionLocalizations/{localization_id}/appScreenshotSets",
        method=FetchMethod.GET,
        access_token=access_token,
    )["data"]


def get_screenshots(
    screenshot_set_id: str,
    access_token: str,
):
    return fetch(
        path=f"/appScreenshotSets/{screenshot_set_id}/appScreenshots",
        method=FetchMethod.GET,
        access_token=access_token,
    )["data"]


def get_preview_sets(
    localization_id: str,
    access_token: str,
):
    return fetch(
        path=f"/appStoreVersionLocalizations/{localization_id}/appPreviewSets",
        method=FetchMethod.GET,
        access_token=access_token,
    )["data"]


def get_previews(
    preview_set_id: str,
    access_token: str,
):
    return fetch(
        path=f"/appPreviewSets/{screenshot_set_id}/appPreviews",
        method=FetchMethod.GET,
        access_token=access_token,
    )["data"]
