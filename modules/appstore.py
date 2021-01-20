import jwt
import time
import requests
import json
import gzip
import colorama
import logging
from enum import Enum, auto
from .print_util import json_term, clr

# TODO: remove pylint "disable" directives when pylint supports python 3.9 completely
from typing import TypedDict, Optional, Union, Literal, Sequence

APPSTORE_URI_ROOT = "https://api.appstoreconnect.apple.com/v1"
APPSTORE_AUDIENCE = "appstoreconnect-v1"
APPSTORE_JWT_ALGO = "ES256"


class ResourceNotFoundException(Exception):
    pass


class FetchMethod(Enum):
    GET = auto()
    POST = auto()
    PATCH = auto()
    DELETE = auto()


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


class ScreenshotDisplayType(Enum):
    APP_IPHONE_65 = auto()
    APP_IPHONE_58 = auto()
    APP_IPHONE_55 = auto()
    APP_IPHONE_47 = auto()
    APP_IPHONE_40 = auto()
    APP_IPHONE_35 = auto()
    APP_IPAD_PRO_3GEN_129 = auto()
    APP_IPAD_PRO_3GEN_11 = auto()
    APP_IPAD_PRO_129 = auto()
    APP_IPAD_105 = auto()
    APP_IPAD_97 = auto()
    APP_DESKTOP = auto()
    APP_WATCH_SERIES_4 = auto()
    APP_WATCH_SERIES_3 = auto()
    APP_APPLE_TV = auto()
    IMESSAGE_APP_IPHONE_65 = auto()
    IMESSAGE_APP_IPHONE_58 = auto()
    IMESSAGE_APP_IPHONE_55 = auto()
    IMESSAGE_APP_IPHONE_47 = auto()
    IMESSAGE_APP_IPHONE_40 = auto()
    IMESSAGE_APP_IPAD_PRO_3GEN_129 = auto()
    IMESSAGE_APP_IPAD_PRO_3GEN_11 = auto()
    IMESSAGE_APP_IPAD_PRO_129 = auto()
    IMESSAGE_APP_IPAD_105 = auto()
    IMESSAGE_APP_IPAD_97 = auto()


class MediaAssetState(Enum):
    AWAITING_UPLOAD = auto()
    UPLOAD_COMPLETE = auto()
    COMPLETE = auto()
    FAILED = auto()


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
            f"{colorama.Fore.GREEN}appstore.fetch: {__name(method)} {colorama.Fore.MAGENTA}{url}\n",
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


def get_categories(
    access_token: str,
    platforms: PlatformList = list(Platform),
):
    return fetch(
        method=FetchMethod.GET,
        path=f"/appCategories?filter[platforms]={','.join(__names(platforms))}&exists[parent]=false&include=subcategories",
        access_token=access_token,
    )["data"]


def get_apps(
    access_token: str,
):
    return fetch(method=FetchMethod.GET, path=f"/apps", access_token=access_token)[
        "data"
    ]


def get_app(
    app_id: str,
    access_token: str,
):
    return fetch(
        method=FetchMethod.GET, path=f"/apps/{app_id}", access_token=access_token
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
        method=FetchMethod.GET,
        path=f"/apps/{app_id}/appInfos",
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
        method=FetchMethod.PATCH,
        path=f"/appInfos/{info_id}",
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
        method=FetchMethod.GET,
        path=f"/appInfos/{info_id}/appInfoLocalizations",
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
        method=FetchMethod.POST,
        path=f"/appInfoLocalizations",
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
        method=FetchMethod.PATCH,
        path=f"/appInfoLocalizations/{info_localization_id}",
        access_token=access_token,
        data={
            "data": {
                "id": info_localization_id,
                "attributes": info_localization_attributes,
                "type": "appInfoLocalizations",
            }
        },
    )["data"]


def delete_info_localization(
    info_localization_id: str,
    access_token: str,
):
    """Deletes the specified App Info Localization."""
    fetch(
        method=FetchMethod.DELETE,
        path=f"/appInfoLocalizations/{info_localization_id}",
        access_token=access_token,
    )


def create_version(
    app_id: str,
    platform: Union[Platform, str],  # pylint: disable=unsubscriptable-object
    version_string: str,
    access_token: str,
):
    """Creates a new app version."""
    return fetch(
        method=FetchMethod.POST,
        path=f"/appStoreVersions/",
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
        method=FetchMethod.PATCH,
        path=f"/appStoreVersions/{version_id}",
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
        method=FetchMethod.GET,
        path=f"/apps/{app_id}/appStoreVersions",
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
        method=FetchMethod.GET,
        path=f"/appStoreVersions/{version_id}/appStoreVersionLocalizations",
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
        method=FetchMethod.POST,
        path=f"/appStoreVersionLocalizations",
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
        method=FetchMethod.PATCH,
        path=f"/appStoreVersionLocalizations/{localization_id}",
        access_token=access_token,
        data={
            "data": {
                "id": localization_id,
                "attributes": localization_attributes,
                "type": "appStoreVersionLocalizations",
            }
        },
    )["data"]


def delete_version_localization(
    localization_id: str,
    access_token: str,
):
    """Deletes the specified App Version Localization."""
    fetch(
        method=FetchMethod.DELETE,
        path=f"/appStoreVersionLocalizations/{localization_id}",
        access_token=access_token,
    )


def get_screenshot_sets(
    localization_id: str,
    access_token: str,
):
    """Get the screenshot sets from the specified App Version Localization."""
    return fetch(
        method=FetchMethod.GET,
        path=f"/appStoreVersionLocalizations/{localization_id}/appScreenshotSets",
        access_token=access_token,
    )["data"]


def create_screenshot_set(
    localization_id: str,
    display_type: Union[
        ScreenshotDisplayType, str
    ],  # pylint: disable=unsubscriptable-object
    access_token: str,
):
    """Create a new screenshot set in the specified App Version Localization."""
    return fetch(
        method=FetchMethod.POST,
        path=f"/appScreenshotSets",
        access_token=access_token,
        data={
            "data": {
                "attributes": {"screenshotDisplayType": __name(display_type)},
                "relationships": {
                    "appStoreVersionLocalization": {
                        "data": {
                            "id": localization_id,
                            "type": "appStoreVersionLocalizations",
                        }
                    }
                },
                "type": "appScreenshotSets",
            }
        },
    )["data"]


def delete_screenshot_set(
    screenshot_set_id: str,
    access_token: str,
):
    """Delete a screenshot set from the App Version Localization."""
    fetch(
        method=FetchMethod.DELETE,
        path=f"/appScreenshotSets/{screenshot_set_id}",
        access_token=access_token,
    )


def update_screenshot_order(
    screenshot_set_id: str,
    screenshot_ids: Sequence[str],
    access_token: str,
):
    """Update the order of the screenshots in a screenshot set."""
    fetch(
        method=FetchMethod.PATCH,
        path=f"/appScreenshotSets/{screenshot_set_id}/relationships/appScreenshots",
        access_token=access_token,
        data={
            "data": [
                {"id": ss_id, "type": "appScreenshots"} for ss_id in screenshot_ids
            ]
        },
    )


def get_screenshots(
    screenshot_set_id: str,
    access_token: str,
):
    """Get the screenshots in a screenshot set."""
    return fetch(
        method=FetchMethod.GET,
        path=f"/appScreenshotSets/{screenshot_set_id}/appScreenshots",
        access_token=access_token,
    )["data"]


def get_screenshot(
    screenshot_id: str,
    access_token: str,
):
    """Get the screenshot info."""
    return fetch(
        method=FetchMethod.GET,
        path=f"/appScreenshots/{screenshot_id}",
        access_token=access_token,
    )["data"]


def create_screenshot(
    screenshot_set_id: str,
    file_name: str,
    file_size: int,
    access_token: str,
):
    """Create a screenshot asset reservation in the specified screenshot set.
    Use the upload operations in the response to upload the file parts."""
    return fetch(
        method=FetchMethod.POST,
        path=f"/appScreenshots",
        access_token=access_token,
        data={
            "data": {
                "attributes": {"fileName": file_name, "fileSize": file_size},
                "relationships": {
                    "appScreenshotSet": {
                        "data": {
                            "id": screenshot_set_id,
                            "type": "appScreenshotSets",
                        }
                    }
                },
                "type": "appScreenshots",
            }
        },
    )["data"]


def update_screenshot(
    screenshot_id: str,
    uploaded: bool,
    sourceFileChecksum: str,
    access_token: str,
):
    """Update the screenshot to commit it after a successful upload."""
    return fetch(
        method=FetchMethod.PATCH,
        path=f"/appScreenshots/{screenshot_id}",
        access_token=access_token,
        data={
            "data": {
                "id": screenshot_id,
                "attributes": {
                    "uploaded": uploaded,
                    "sourceFileChecksum": sourceFileChecksum,
                },
                "type": "appScreenshots",
            }
        },
    )["data"]


def delete_screenshot(
    screenshot_id: str,
    access_token: str,
):
    """Delete a screenshot from its screenshot set."""
    fetch(
        method=FetchMethod.DELETE,
        path=f"/appScreenshots/{screenshot_id}",
        access_token=access_token,
    )


def get_preview_sets(
    localization_id: str,
    access_token: str,
):
    """Get the preview sets in the specified App Version Localization."""
    return fetch(
        method=FetchMethod.GET,
        path=f"/appStoreVersionLocalizations/{localization_id}/appPreviewSets",
        access_token=access_token,
    )["data"]


def get_previews(
    preview_set_id: str,
    access_token: str,
):
    """Get the previews in a preview set."""
    return fetch(
        method=FetchMethod.GET,
        path=f"/appPreviewSets/{preview_set_id}/appPreviews",
        access_token=access_token,
    )["data"]
