import logging
import colorama
from enum import Enum, auto
from typing import Union, Optional
from appstore_tools import appstore
from appstore_tools.print_util import print_clr, clr, json_term


class Verbosity(Enum):
    SHORT = auto()
    LONG = auto()
    FULL = auto()


def list_categories(
    access_token: str,
    platforms: appstore.PlatformList,
    verbosity: Verbosity = Verbosity.SHORT,
):
    """List the appstore's heirachry of categories and subcategories."""
    categories = appstore.get_categories(access_token=access_token, platforms=platforms)
    categories.sort(key=lambda x: x["id"])

    if verbosity == Verbosity.SHORT:
        for x in categories:
            print_clr(
                x["id"],
                colorama.Fore.LIGHTBLACK_EX
                + f' {{{",".join(x["attributes"]["platforms"])}}}',
            )

            for sub in x["relationships"]["subcategories"]["data"]:
                print_clr(colorama.Style.DIM + f'  {sub["id"]}')

    else:
        print(json_term(categories))


def list_apps(access_token: str, verbosity: Verbosity = Verbosity.SHORT):
    """List the apps found on the appstore."""
    apps = appstore.get_apps(access_token=access_token)
    if verbosity == Verbosity.SHORT:
        apps = [
            {
                "id": v["id"],
                "name": v["attributes"]["name"],
                "bundleId": v["attributes"]["bundleId"],
                "primaryLocale": v["attributes"]["primaryLocale"],
            }
            for v in apps
        ]
    elif verbosity == Verbosity.LONG:
        apps = [
            {
                "id": v["id"],
                **v["attributes"],
            }
            for v in apps
        ]
    print(json_term(apps))


def list_versions(
    access_token: str,
    app_id: str,
    platforms: appstore.PlatformList,
    states: appstore.VersionStateList,
    verbosity: Verbosity = Verbosity.SHORT,
):
    """List the app versions found on the appstore."""
    versions = appstore.get_versions(
        app_id=app_id, access_token=access_token, platforms=platforms, states=states
    )
    if verbosity == Verbosity.SHORT:
        versions = [
            {
                "id": x["id"],
                "platform": x["attributes"]["platform"],
                "versionString": x["attributes"]["versionString"],
                "appStoreState": x["attributes"]["appStoreState"],
            }
            for x in versions
        ]
    print(json_term({"appId": app_id, "versions": versions}))


def list_infos(
    access_token: str,
    app_id: str,
    states: appstore.VersionStateList,
    verbosity: Verbosity = Verbosity.SHORT,
):
    """List the app infos found on the appstore."""
    infos = appstore.get_infos(app_id=app_id, access_token=access_token, states=states)

    if verbosity == Verbosity.SHORT:
        infos = [
            {
                "id": x["id"],
                "appStoreState": x["attributes"]["appStoreState"],
                "appStoreAgeRating": x["attributes"]["appStoreAgeRating"],
                "brazilAgeRating": x["attributes"]["brazilAgeRating"],
                "kidsAgeBand": x["attributes"]["kidsAgeBand"],
            }
            for x in infos
        ]
    elif verbosity == Verbosity.LONG:
        infos_selected = []
        for x in infos:
            relationships = {}
            for k in x["relationships"]:
                relationships[k] = x["relationships"][k]["links"]["related"]
            infos_selected.append(
                {
                    "id": x["id"],
                    "appStoreState": x["attributes"]["appStoreState"],
                    "appStoreAgeRating": x["attributes"]["appStoreAgeRating"],
                    "brazilAgeRating": x["attributes"]["brazilAgeRating"],
                    "kidsAgeBand": x["attributes"]["kidsAgeBand"],
                    **relationships,
                }
            )
        infos = infos_selected

    print(json_term({"appId": app_id, "infos": infos}))


def list_screenshots(
    access_token: str,
    app_id: str,
    platforms: appstore.PlatformList,
    states: appstore.VersionStateList,
    version_limit: Optional[int],  # pylint: disable=unsubscriptable-object
    verbosity: Verbosity = Verbosity.SHORT,
):
    """List screenhots for each screenshot set of each app version."""
    logging.info(clr(colorama.Fore.GREEN + "app_id: ", str(app_id)))

    versions = appstore.get_versions(
        app_id=app_id, access_token=access_token, platforms=platforms, states=states
    )
    for version in versions[:version_limit]:
        version_id = version["id"]
        version_state = version["attributes"]["appStoreState"]
        print_clr(
            f"{colorama.Fore.GREEN}{version_state} {colorama.Style.DIM}{version_id} "
        )

        localizations = appstore.get_version_localizations(
            version_id=version_id, access_token=access_token
        )

        for loc in localizations:
            loc_id = loc["id"]
            locale = loc["attributes"]["locale"]

            screenshot_sets = appstore.get_screenshot_sets(
                localization_id=loc_id, access_token=access_token
            )
            print_clr(
                f"{colorama.Fore.GREEN}{locale}: ",
                f"Found {colorama.Fore.CYAN}{len(screenshot_sets)}{colorama.Fore.RESET} screenshot sets.",
            )

            for screenshot_set in screenshot_sets:
                ss_set_id = screenshot_set["id"]
                ss_display_type = screenshot_set["attributes"]["screenshotDisplayType"]
                screenshots = appstore.get_screenshots(
                    screenshot_set_id=ss_set_id, access_token=access_token
                )
                if verbosity == Verbosity.SHORT:
                    print_clr(colorama.Fore.CYAN + ss_display_type)
                    for x in screenshots:
                        print_clr(
                            f'  {colorama.Style.DIM}{x["attributes"]["assetDeliveryState"]["state"]:15}',
                            f'  {x["attributes"]["fileName"]}',
                        )
                    continue
                if verbosity == Verbosity.LONG:
                    screenshots = [
                        (
                            {
                                "id": x["id"],
                                "fileSize": x["attributes"]["fileSize"],
                                "fileName": x["attributes"]["fileName"],
                                "sourceFileChecksum": x["attributes"][
                                    "sourceFileChecksum"
                                ],
                                "templateUrl": x["attributes"]["imageAsset"][
                                    "templateUrl"
                                ],
                                "width": x["attributes"]["imageAsset"]["width"],
                                "height": x["attributes"]["imageAsset"]["height"],
                                "assetDeliveryState": x["attributes"][
                                    "assetDeliveryState"
                                ]["state"],
                            }
                            if x["attributes"]["assetDeliveryState"]["state"]
                            == appstore.MediaAssetState.COMPLETE
                            else {
                                "id": x["id"],
                                "fileSize": x["attributes"]["fileSize"],
                                "fileName": x["attributes"]["fileName"],
                                "sourceFileChecksum": x["attributes"][
                                    "sourceFileChecksum"
                                ],
                                "assetDeliveryState": x["attributes"][
                                    "assetDeliveryState"
                                ]["state"],
                            }
                        )
                        for x in screenshots
                    ]
                print(
                    json_term(
                        {
                            "screenshotDisplayType": ss_display_type,
                            "screenshots": screenshots,
                        }
                    )
                )


def list_previews(
    access_token: str,
    app_id: str,
    platforms: appstore.PlatformList,
    states: appstore.VersionStateList,
    version_limit: Optional[int],  # pylint: disable=unsubscriptable-object
):
    """List previews for each preview set of each app version."""
    logging.info(clr(colorama.Fore.GREEN + "app_id: ", str(app_id)))

    versions = appstore.get_versions(
        app_id=app_id, access_token=access_token, platforms=platforms, states=states
    )
    for version in versions[:version_limit]:
        version_id = version["id"]
        version_state = version["attributes"]["appStoreState"]
        print_clr(
            f"{colorama.Fore.GREEN}version: {colorama.Fore.BLUE}{version_id} {version_state}"
        )

        localizations = appstore.get_version_localizations(
            version_id=version_id, access_token=access_token
        )

        localization_ids = (l["id"] for l in localizations)
        for loc_id in localization_ids:
            preview_sets = appstore.get_preview_sets(
                localization_id=loc_id, access_token=access_token
            )
            print_clr(
                f"{colorama.Fore.GREEN}loc_id {loc_id}: ",
                f"Found {colorama.Fore.CYAN}{len(preview_sets)}{colorama.Fore.RESET} preview sets.",
            )

            for preview_set in preview_sets:
                preview_set_id = preview_set["id"]
                preview_type = preview_set["attributes"]["previewType"]
                preview_set = appstore.get_previews(
                    preview_set_id=preview_set_id, access_token=access_token
                )
                print_clr(f"{colorama.Fore.GREEN}previewType: ", preview_type)
                print(json_term(preview_set))
