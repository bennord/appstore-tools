import requests
import json
import gzip
import colorama
import logging
from enum import Enum, auto
from appstore_tools.print_util import json_term, clr
from .types import (
    Platform,
    PlatformList,
    ScreenshotDisplayType,
    PreviewType,
    VersionState,
    VersionStateList,
    InfoAttributes,
    InfoLocalizationAttributes,
    VersionAttributes,
    VersionLocalizationAttributes,
)
from .util import enum_name, enum_names, editable_version_states
from .fetch import fetch
from .exceptions import ResourceNotFoundException
from .fetch import fetch, FetchMethod

# TODO: remove pylint "disable" directives when pylint supports python 3.9 completely
from typing import TypedDict, Optional, Union, Literal, Sequence


def get_categories(
    access_token: str,
    platforms: PlatformList = list(Platform),
):
    """Get this list of possible categories/subcategories on the app store."""
    return fetch(
        method=FetchMethod.GET,
        path=f"/appCategories?filter[platforms]={','.join(enum_names(platforms))}&exists[parent]=false&include=subcategories",
        access_token=access_token,
    )["data"]


def get_apps(
    access_token: str,
):
    """Get all apps under the users app store account."""
    return fetch(method=FetchMethod.GET, path=f"/apps", access_token=access_token)[
        "data"
    ]


def get_app(
    app_id: str,
    access_token: str,
):
    """Get app by id."""
    return fetch(
        method=FetchMethod.GET, path=f"/apps/{app_id}", access_token=access_token
    )["data"]


def get_app_id(
    bundle_id: str,
    access_token: str,
) -> int:
    """Get the app id for the specified bundle id."""
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
    """Get the bundle id for the specified app id."""
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

    return [
        v for v in versions if v["attributes"]["appStoreState"] in enum_names(states)
    ]


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
                    "platform": enum_name(platform),
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
        if v["attributes"]["platform"] in enum_names(platforms)
        and v["attributes"]["appStoreState"] in enum_names(states)
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
                "attributes": {"screenshotDisplayType": enum_name(display_type)},
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


def create_preview_set(
    localization_id: str,
    preview_type: Union[PreviewType, str],  # pylint: disable=unsubscriptable-object
    access_token: str,
):
    """Create a new preview set in the specified App Version Localization."""
    return fetch(
        method=FetchMethod.POST,
        path=f"/appPreviewSets",
        access_token=access_token,
        data={
            "data": {
                "attributes": {"previewType": enum_name(preview_type)},
                "relationships": {
                    "appStoreVersionLocalization": {
                        "data": {
                            "id": localization_id,
                            "type": "appStoreVersionLocalizations",
                        }
                    }
                },
                "type": "appPreviewSets",
            }
        },
    )["data"]


def delete_preview_set(
    preview_set_id: str,
    access_token: str,
):
    """Delete a preview set from the App Version Localization."""
    fetch(
        method=FetchMethod.DELETE,
        path=f"/appPreviewSets/{preview_set_id}",
        access_token=access_token,
    )


def update_preview_order(
    preview_set_id: str,
    preview_ids: Sequence[str],
    access_token: str,
):
    """Update the order of the previews in a preview set."""
    fetch(
        method=FetchMethod.PATCH,
        path=f"/appPreviewSets/{preview_set_id}/relationships/appPreviews",
        access_token=access_token,
        data={"data": [{"id": p_id, "type": "appPreviews"} for p_id in preview_ids]},
    )


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


def get_preview(
    preview_id: str,
    access_token: str,
):
    """Get the preview info."""
    return fetch(
        method=FetchMethod.GET,
        path=f"/appPreviews/{preview_id}",
        access_token=access_token,
    )["data"]


def create_preview(
    preview_set_id: str,
    file_name: str,
    file_size: int,
    access_token: str,
):
    """Create a preview asset reservation in the specified preview set.
    Use the upload operations in the response to upload the file parts."""

    # TODO: add support for previewFrameTimeCode
    return fetch(
        method=FetchMethod.POST,
        path=f"/appPreviews",
        access_token=access_token,
        data={
            "data": {
                "attributes": {"fileName": file_name, "fileSize": file_size},
                "relationships": {
                    "appPreviewSet": {
                        "data": {
                            "id": preview_set_id,
                            "type": "appPreviewSets",
                        }
                    }
                },
                "type": "appPreviews",
            }
        },
    )["data"]


def update_preview(
    preview_id: str,
    uploaded: bool,
    sourceFileChecksum: str,
    access_token: str,
):
    """Update the preview to commit it after a successful upload."""

    # TODO: add support for previewFrameTimeCode
    return fetch(
        method=FetchMethod.PATCH,
        path=f"/appPreviews/{preview_id}",
        access_token=access_token,
        data={
            "data": {
                "id": preview_id,
                "attributes": {
                    "uploaded": uploaded,
                    "sourceFileChecksum": sourceFileChecksum,
                },
                "type": "appPreviews",
            }
        },
    )["data"]


def delete_preview(
    preview_id: str,
    access_token: str,
):
    """Delete a preview from its preview set."""
    fetch(
        method=FetchMethod.DELETE,
        path=f"/appPreviews/{preview_id}",
        access_token=access_token,
    )
