import jwt
import time
import requests
import json
import gzip
import colorama
import logging
from enum import Enum, auto
from .print_util import json_term, color_term

# TODO: remove pylint "disable" directives when pylint supports python 3.9 completely
from typing import TypedDict, Optional, Union, List, Literal, Sequence

APPSTORE_URI_ROOT = "https://api.appstoreconnect.apple.com/v1"
APPSTORE_AUDIENCE = "appstoreconnect-v1"
APPSTORE_JWT_ALGO = "ES256"


class ResourceNotFoundException(Exception):
    pass


class FetchMethod(Enum):
    GET = auto()
    POST = auto()
    PATCH = auto()


class Platform(Enum):
    IOS = auto()
    MAC_OS = auto()
    TV_OS = auto()


class ReleaseType(Enum):
    MANUAL = auto()
    AFTER_APPROVAL = auto()
    SCHEDULED = auto()


class VersionState(Enum):
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


editable_version_states = [
    VersionState.PREPARE_FOR_SUBMISSION,
    VersionState.WAITING_FOR_REVIEW,
    VersionState.WAITING_FOR_EXPORT_COMPLIANCE,
    VersionState.REJECTED,
    VersionState.METADATA_REJECTED,
    VersionState.DEVELOPER_REJECTED,
]

live_version_state = VersionState.READY_FOR_SALE

EnumList = Sequence[Union[Enum, str]]  # pylint: disable=unsubscriptable-object
PlatformList = Sequence[Union[Platform, str]]  # pylint: disable=unsubscriptable-object
VersionStateList = Sequence[
    Union[VersionState, str]  # pylint: disable=unsubscriptable-object
]


class InfoAttributes(TypedDict, total=False):  # pylint: disable=inherit-non-class
    primaryCategory: Optional[str]  # pylint: disable=unsubscriptable-object
    primarySubcategoryOne: Optional[str]  # pylint: disable=unsubscriptable-object
    primarySubcategoryTwo: Optional[str]  # pylint: disable=unsubscriptable-object
    secondaryCategory: Optional[str]  # pylint: disable=unsubscriptable-object
    secondarySubcategoryOne: Optional[str]  # pylint: disable=unsubscriptable-object
    secondarySubcategoryTwo: Optional[str]  # pylint: disable=unsubscriptable-object


class InfoLocalizationAttributes(
    TypedDict, total=False
):  # pylint: disable=inherit-non-class
    name: Optional[str]  # pylint: disable=unsubscriptable-object
    privacyPolicyText: Optional[str]  # pylint: disable=unsubscriptable-object
    privacyPolicyUrl: Optional[str]  # pylint: disable=unsubscriptable-object
    subtitle: Optional[str]  # pylint: disable=unsubscriptable-object


class VersionAttributes(TypedDict, total=False):  # pylint: disable=inherit-non-class
    copyright: Optional[str]  # pylint: disable=unsubscriptable-object
    earliestReleaseDate: Optional[str]  # pylint: disable=unsubscriptable-object
    releaseType: Optional[str]  # pylint: disable=unsubscriptable-object
    usesIdfa: Optional[bool]  # pylint: disable=unsubscriptable-object
    versionString: Optional[str]  # pylint: disable=unsubscriptable-object
    downloadable: Optional[bool]  # pylint: disable=unsubscriptable-object


class VersionLocalizationAttributes(
    TypedDict, total=False
):  # pylint: disable=inherit-non-class
    description: Optional[str]  # pylint: disable=unsubscriptable-object
    keywords: Optional[str]  # pylint: disable=unsubscriptable-object
    marketingUrl: Optional[str]  # pylint: disable=unsubscriptable-object
    promotionalText: Optional[str]  # pylint: disable=unsubscriptable-object
    supportUrl: Optional[str]  # pylint: disable=unsubscriptable-object
    whatsNew: Optional[str]  # pylint: disable=unsubscriptable-object


def __name(x: Union[Enum, str]):  # pylint: disable=unsubscriptable-object
    return x.name if isinstance(x, Enum) else x


def __names(x_list: EnumList):
    return (__name(x) for x in x_list)


def version_state_is_editable(
    version_state: Union[VersionState, str]  # pylint: disable=unsubscriptable-object
) -> bool:
    """Test whether or not the version state is 'editable' in the App Store."""
    return __name(version_state) in __names(editable_version_states)


def version_state_is_live(
    version_state: Union[VersionState, str]  # pylint: disable=unsubscriptable-object
) -> bool:
    """Test whether or not the version state is 'live' in the App Store."""
    return __name(version_state) == __name(live_version_state)


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


def fetch(path: str, method: FetchMethod, access_token: str, data=None):
    headers = {"Authorization": f"Bearer {access_token}"}

    url = APPSTORE_URI_ROOT + path if path.startswith("/") else path

    logging.debug(
        color_term(
            f"{colorama.Fore.GREEN}appstore.fetch: {method.name} {colorama.Fore.MAGENTA}{url}\n"
        )
        + color_term(f"{colorama.Fore.BLUE}request body:\n")
        + json_term(data)
    )

    if method == FetchMethod.GET:
        response = requests.get(url, headers=headers)
    elif method == FetchMethod.POST:
        headers["Content-Type"] = "application/json"
        response = requests.post(url=url, headers=headers, data=json.dumps(data))
    elif method == FetchMethod.PATCH:
        headers["Content-Type"] = "application/json"
        response = requests.patch(url=url, headers=headers, data=json.dumps(data))

    content_type = response.headers["content-type"]

    if content_type == "application/json":
        result = response.json()
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

    logging.debug(
        color_term(f"{colorama.Fore.BLUE}response body:\n") + json_term(result)
    )

    # raise exceptions for easier handling
    if response.status_code == 404:
        raise ResourceNotFoundException(
            f"Resource not found at {url} (HttpError {404})"
        )
    response.raise_for_status()

    return result


def get_categories(
    access_token: str,
    platforms: PlatformList = list(Platform),
):
    return fetch(
        path=f"/appCategories?filter[platforms]={','.join(__names(platforms))}&exists[parent]=false&include=subcategories",
        method=FetchMethod.GET,
        access_token=access_token,
    )["data"]


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


def get_infos(
    app_id: str,
    access_token: str,
    states: VersionStateList = list(VersionState),
):
    """Get the list of app infos, optionally filtering by appstore state."""
    versions = fetch(
        path=f"/apps/{app_id}/appInfos",
        method=FetchMethod.GET,
        access_token=access_token,
    )["data"]

    return [v for v in versions if v["attributes"]["appStoreState"] in __names(states)]


def update_info(
    info_id: str,
    info_attributes: InfoAttributes,
    access_token: str,
):
    """Update the non-localized AppInfo data."""
    relationships = {}
    for k, v in info_attributes.items():
        relationships[k] = {"data": {"id": v, "type": "appCategories"}}

    return fetch(
        path=f"/appInfos/{info_id}",
        method=FetchMethod.PATCH,
        access_token=access_token,
        data={
            "data": {
                "id": info_id,
                "relationships": relationships,
                "type": "appInfos",
            }
        },
    )["data"]


def get_info_localizations(
    info_id: str,
    access_token: str,
):
    """Get the list of app info localizations."""
    return fetch(
        path=f"/appInfos/{info_id}/appInfoLocalizations",
        method=FetchMethod.GET,
        access_token=access_token,
    )["data"]


def create_info_localization(
    info_id: str,
    locale: str,
    info_localization_attributes: InfoLocalizationAttributes,
    access_token: str,
):
    """Creates a new app store info localization."""
    return fetch(
        path=f"/appInfoLocalizations",
        method=FetchMethod.POST,
        access_token=access_token,
        data={
            "data": {
                "attributes": {"locale": locale, **info_localization_attributes},
                "relationships": {
                    "appInfo": {"data": {"id": info_id, "type": "appInfos"}}
                },
                "type": "appInfoLocalizations",
            }
        },
    )["data"]


def update_info_localization(
    info_localization_id: str,
    info_localization_attributes: InfoLocalizationAttributes,
    access_token: str,
):
    """Updates the meta data for the specified App Info Localization.
    Some data fields require the App Version to be in an editable state."""
    return fetch(
        path=f"/appInfoLocalizations/{info_localization_id}",
        method=FetchMethod.PATCH,
        access_token=access_token,
        data={
            "data": {
                "id": info_localization_id,
                "attributes": info_localization_attributes,
                "type": "appInfoLocalizations",
            }
        },
    )["data"]


def create_version(
    app_id: str,
    platform: Union[Platform, str],  # pylint: disable=unsubscriptable-object
    version_string: str,
    access_token: str,
):
    """Creates a new app version."""
    return fetch(
        path=f"/appStoreVersions/",
        method=FetchMethod.POST,
        access_token=access_token,
        data={
            "data": {
                "attributes": {
                    "platform": __name(platform),
                    "versionString": version_string,
                },
                "relationships": {"app": {"data": {"id": app_id, "type": "apps"}}},
                "type": "appStoreVersions",
            }
        },
    )["data"]


def update_version(
    version_id: str,
    version_attributes: VersionAttributes,
    access_token: str,
):
    """Update an app version."""
    return fetch(
        path=f"/appStoreVersions/{version_id}",
        method=FetchMethod.PATCH,
        access_token=access_token,
        data={
            "data": {
                "id": version_id,
                "attributes": version_attributes,
                "type": "appStoreVersions",
            }
        },
    )["data"]


def get_versions(
    app_id: str,
    access_token: str,
    platforms: PlatformList = list(Platform),
    states: VersionStateList = list(VersionState),
):
    """Get the list of app versions, optionally filtering by platform and/or state."""
    versions = fetch(
        path=f"/apps/{app_id}/appStoreVersions",
        method=FetchMethod.GET,
        access_token=access_token,
    )["data"]

    return [
        v
        for v in versions
        if v["attributes"]["platform"] in __names(platforms)
        and v["attributes"]["appStoreState"] in __names(states)
    ]


def get_versions_editable(
    app_id: str,
    access_token: str,
    platforms: PlatformList = list(Platform),
):
    return get_versions(
        app_id=app_id,
        access_token=access_token,
        platforms=platforms,
        states=[s.name for s in editable_version_states],
    )


def get_version_live(
    app_id: str,
    access_token: str,
    platforms: PlatformList = list(Platform),
):
    live_state = VersionState.READY_FOR_SALE.name
    versions = get_versions(
        app_id=app_id,
        access_token=access_token,
        platforms=platforms,
        states=[live_state],
    )

    if len(versions) == 0:
        raise ResourceNotFoundException(f'No app version matching state "{live_state}"')
    else:
        return versions[0]


def get_version_localizations(
    version_id: str,
    access_token: str,
):
    return fetch(
        path=f"/appStoreVersions/{version_id}/appStoreVersionLocalizations",
        method=FetchMethod.GET,
        access_token=access_token,
    )["data"]


def create_version_localization(
    version_id: str,
    locale: str,
    localization_attributes: VersionLocalizationAttributes,
    access_token: str,
):
    """Creates a new app store version localization."""
    return fetch(
        path=f"/appStoreVersionLocalizations",
        method=FetchMethod.POST,
        access_token=access_token,
        data={
            "data": {
                "attributes": {"locale": locale, **localization_attributes},
                "relationships": {
                    "appStoreVersion": {
                        "data": {"id": version_id, "type": "appStoreVersions"}
                    }
                },
                "type": "appStoreVersionLocalizations",
            }
        },
    )["data"]


def update_version_localization(
    localization_id: str,
    localization_attributes: VersionLocalizationAttributes,
    access_token: str,
):
    """Updates the meta data for the specified App Version Localization.
    Some data fields require the App Version to be in an editable state."""
    return fetch(
        path=f"/appStoreVersionLocalizations/{localization_id}",
        method=FetchMethod.PATCH,
        access_token=access_token,
        data={
            "data": {
                "id": localization_id,
                "attributes": localization_attributes,
                "type": "appStoreVersionLocalizations",
            }
        },
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
        path=f"/appPreviewSets/{preview_set_id}/appPreviews",
        method=FetchMethod.GET,
        access_token=access_token,
    )["data"]
