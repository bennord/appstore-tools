import colorama
import modules.appstore as appstore
import modules.command_line as command_line
import sys
import os
import logging
import requests
import hashlib
from modules.print_util import print_clr, clr, json_term
from typing import Union, Optional
from enum import Enum, auto


class Verbosity(Enum):
    SHORT = auto()
    LONG = auto()
    FULL = auto()


def fetch_screenshot(screenshot_info: dict):
    attr = screenshot_info["attributes"]
    file_ext = os.path.splitext(attr["fileName"])[1]
    width = attr["imageAsset"]["width"]
    height = attr["imageAsset"]["height"]
    url_template = attr["imageAsset"]["templateUrl"]

    url = url_template.format(w=width, h=height, f=file_ext[1:])
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


def print_locale_status(locale: str, color: str, status: str):
    print_clr(f"  {color}{locale:5}{colorama.Style.RESET_ALL} - {status}")


def print_screenshot_set_status(display_type: str, color: str, status: str):
    print_clr(f"    {color}{display_type}{colorama.Style.RESET_ALL} - {status}")


def print_screenshot_status(file_name: str, color: str, status: str):
    print_clr(f"      {color}{file_name}{colorama.Style.RESET_ALL} - {status}")


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


def download_info(
    access_token: str,
    app_dir: str,
    app_id: str,
    bundle_id: str,
    version_states: appstore.VersionStateList = list(appstore.VersionState),
):
    """Download the app info to the local app directory."""
    infos = appstore.get_infos(
        app_id=app_id,
        access_token=access_token,
        states=version_states,
    )
    if len(infos) == 0:
        message = f"No app infos found"
        if version_states != list(appstore.VersionState):
            message += f": {colorama.Fore.CYAN}{version_states}{colorama.Fore.RESET}"
        raise appstore.ResourceNotFoundException(clr(message))

    info = infos[0]
    info_id = info["id"]
    info_state = info["attributes"]["appStoreState"]

    print_clr(
        f"{colorama.Fore.GREEN}Downloading app info: ",
        f"{colorama.Fore.BLUE}{info_id}{colorama.Fore.RESET}, ",
        f"{colorama.Fore.CYAN}{info_state}",
    )

    # Info Localizations
    localizations = appstore.get_info_localizations(
        info_id=info_id, access_token=access_token
    )

    for loc in localizations:
        loc_id = loc["id"]
        loc_attr = loc["attributes"]
        locale = loc_attr["locale"]
        loc_dir = os.path.join(app_dir, locale)

        print_clr(
            f"{colorama.Fore.GREEN}Locale: ",
            f"{colorama.Fore.MAGENTA}{locale} ",
            f"{colorama.Fore.BLUE}{loc_id}",
        )

        # Locale directory
        os.makedirs(name=loc_dir, exist_ok=True)

        for key in appstore.InfoLocalizationAttributes.__annotations__.keys():
            content = loc_attr[key] if loc_attr[key] is not None else ""
            write_txt_file(
                path=os.path.join(loc_dir, key + ".txt"),
                content=content,
            )


def download_version(
    access_token: str,
    app_dir: str,
    app_id: str,
    bundle_id: str,
    platforms: appstore.PlatformList,
    version_states: appstore.VersionStateList = list(appstore.VersionState),
):
    """Download the app version localized data and screenshots to the local app directory."""
    versions = appstore.get_versions(
        app_id=app_id,
        access_token=access_token,
        platforms=platforms,
        states=version_states,
    )
    if len(versions) == 0:
        message = f"No app version found: {colorama.Fore.CYAN}{platforms}{colorama.Fore.RESET}"
        if version_states != list(appstore.VersionState):
            message += f", {colorama.Fore.CYAN}{version_states}{colorama.Fore.RESET}"
        raise appstore.ResourceNotFoundException(clr(message))

    version = versions[0]
    version_id = version["id"]
    version_state = version["attributes"]["appStoreState"]
    version_platform = version["attributes"]["platform"]

    print_clr(
        f"{colorama.Fore.GREEN}Downloading app version: ",
        f"{colorama.Fore.BLUE}{version_id}{colorama.Fore.RESET}, ",
        f"{colorama.Fore.CYAN}{version_platform}, ",
        f"{colorama.Fore.CYAN}{version_state}",
    )

    # Version Localizations
    localizations = appstore.get_version_localizations(
        version_id=version_id, access_token=access_token
    )

    for loc in localizations:
        loc_id = loc["id"]
        loc_attr = loc["attributes"]
        locale = loc_attr["locale"]
        loc_dir = os.path.join(app_dir, locale)
        screenshots_dir = os.path.join(loc_dir, "screenshots")
        previews_dir = os.path.join(loc_dir, "previews")

        print_clr(
            f"{colorama.Fore.GREEN}Locale: ",
            f"{colorama.Fore.MAGENTA}{locale} ",
            f"{colorama.Fore.BLUE}{loc_id}",
        )

        # Locale directories
        os.makedirs(name=loc_dir, exist_ok=True)
        os.makedirs(name=screenshots_dir, exist_ok=True)
        os.makedirs(name=previews_dir, exist_ok=True)

        for key in appstore.VersionLocalizationAttributes.__annotations__.keys():
            content = loc_attr[key] if loc_attr[key] is not None else ""
            write_txt_file(
                path=os.path.join(loc_dir, key + ".txt"),
                content=content,
            )

        screenshot_sets = appstore.get_screenshot_sets(
            localization_id=loc_id, access_token=access_token
        )

        for ss_set in screenshot_sets:
            ss_set_id = ss_set["id"]
            ss_display_type = ss_set["attributes"]["screenshotDisplayType"]
            ss_set_dir = os.path.join(screenshots_dir, ss_display_type)

            # Screenshot Set directory
            os.makedirs(name=ss_set_dir, exist_ok=True)

            screenshots = appstore.get_screenshots(
                screenshot_set_id=ss_set_id, access_token=access_token
            )

            for screenshot in screenshots:
                ss_filename = screenshot["attributes"]["fileName"]
                ss_path = os.path.join(ss_set_dir, ss_filename)
                print(ss_path)

                response = fetch_screenshot(screenshot)
                if response.ok:
                    write_binary_file(
                        path=ss_path,
                        content=response.content,
                    )
                else:
                    print_clr(colorama.Fore.RED + "FAILED")

        preview_sets = appstore.get_preview_sets(
            localization_id=loc_id, access_token=access_token
        )

        for preview_set in preview_sets:
            preview_set_id = preview_set["id"]
            preview_type = ss_set["attributes"]["previewType"]
            preview_set_dir = os.path.join(previews_dir, preview_type)

            # Preview Set directory
            os.makedirs(name=preview_set_dir, exist_ok=True)

            previews = appstore.get_previews(
                preview_set_id=preview_set_id, access_token=access_token
            )

            for preview in previews:
                preview_filename = preview["attributes"]["fileName"]
                preview_path = os.path.join(preview_set_dir, preview_filename)
                print(preview_path)

                json_term(preview)
                print_clr(colorama.Fore.RED + "PREVIEW DOWNLOAD NOT IMPLEMENTED")
                # TODO: add fetch_preview functionality similar to screenshots

                # response = fetch_screenshot(screenshot)
                # if response.ok:
                #     write_binary_file(
                #         path=ss_path,
                #         content=response.content,
                #     )
                # else:
                #     print_clr(colorama.Fore.RED + "FAILED")


def download(
    access_token: str,
    asset_dir: str,
    app_id: str,
    bundle_id: str,
    platforms: appstore.PlatformList,
    version_states: appstore.VersionStateList = list(appstore.VersionState),
    overwrite: bool = False,
):
    """Download all the app meta data to the local app directory."""
    app_dir = os.path.join(asset_dir, bundle_id)

    print_clr(
        f"{colorama.Fore.CYAN}{bundle_id} ",
        f"{colorama.Fore.BLUE}{app_id} ",
        f"-> ",
        f"{colorama.Fore.CYAN}{app_dir}",
    )

    # App
    if os.path.isdir(app_dir) and not overwrite:
        raise FileExistsError(
            f"App directory {colorama.Fore.CYAN}{app_dir}{colorama.Fore.RESET} already exists. "
            + "Specify '--overwrite' if you wish to force downloading to an existing directory."
        )

    download_info(
        access_token=access_token,
        app_dir=app_dir,
        app_id=app_id,
        bundle_id=bundle_id,
        version_states=version_states,
    )
    download_version(
        access_token=access_token,
        app_dir=app_dir,
        app_id=app_id,
        bundle_id=bundle_id,
        platforms=platforms,
        version_states=version_states,
    )
    print_clr(colorama.Fore.GREEN + "Download complete")


def publish_screenshot(
    access_token: str,
    screenshot_path: str,
    screenshot_set_id: str,
):
    if not os.path.isfile(screenshot_path):
        raise FileNotFoundError("Screenshot path does not exist: {screenshot_path}")

    _, file_name = os.path.split(screenshot_path)
    file_stat = os.stat(screenshot_path)
    file_hash = hashlib.md5()

    # Create
    print_screenshot_status(
        file_name,
        colorama.Fore.CYAN,
        "reserving asset",
    )
    screenshot = appstore.create_screenshot(
        screenshot_set_id=screenshot_set_id,
        file_name=file_name,
        file_size=file_stat.st_size,
        access_token=access_token,
    )

    screenshot_id = screenshot["id"]
    upload_operations = screenshot["attributes"]["uploadOperations"]

    # Upload
    for op in upload_operations:
        method: str = op["method"]
        url: str = op["url"]
        headers: dict = {}
        for h in op["requestHeaders"]:
            headers[h["name"]] = h["value"]
        length: int = op["length"]
        offset: int = op["offset"]

        with open(screenshot_path, "rb") as file:
            file.seek(offset)
            file_chunk = file.read(length)

        file_hash.update(file_chunk)
        print_screenshot_status(
            file_name,
            colorama.Fore.CYAN,
            f"uploading chunk (offset: {offset}, length: {length})",
        )
        requests.request(method=method, url=url, headers=headers, data=file_chunk)

    # Commit
    print_screenshot_status(
        file_name,
        colorama.Fore.CYAN,
        "commiting upload",
    )
    checksum = file_hash.hexdigest()
    screenshot = appstore.update_screenshot(
        screenshot_id=screenshot_id,
        uploaded=True,
        sourceFileChecksum=checksum,
        access_token=access_token,
    )


def screenshot_checksum_matches(screenshot, screenshot_set_dir: str) -> bool:
    """Checks if the appstore checksum matches the asset checksum"""
    file_name = screenshot["attributes"]["fileName"]
    file_path = os.path.join(screenshot_set_dir, file_name)

    appstore_checksum = screenshot["attributes"]["sourceFileChecksum"]

    if appstore_checksum is None:
        print_screenshot_status(
            file_name,
            colorama.Fore.CYAN,
            "checksum missing (in processing)",
        )
        return False

    if not os.path.isfile(file_path):
        print_screenshot_status(
            file_name,
            colorama.Fore.RED,
            "no source file",
        )
        return False

    with open(file_path, "rb") as file:
        checksum = hashlib.md5(file.read()).hexdigest()
        if checksum == appstore_checksum:
            print_screenshot_status(
                file_name,
                colorama.Fore.CYAN + colorama.Style.DIM,
                clr(
                    f"checksum matched: ",
                    f"{colorama.Style.DIM}{checksum}",
                ),
            )
        else:
            print_screenshot_status(
                file_name,
                colorama.Fore.CYAN,
                clr(
                    f"checksum changed: ",
                    f"{colorama.Style.DIM}{appstore_checksum} -> {checksum}",
                ),
            )
        return checksum == appstore_checksum


def publish_screenshots(
    access_token: str,
    screenshot_set_dir: str,
    screenshot_set_id: str,
    display_type: str,
):
    print_screenshot_set_status(
        display_type, colorama.Fore.CYAN, "checking for changes"
    )

    # Delete outdated screenshots
    screenshots = appstore.get_screenshots(
        screenshot_set_id=screenshot_set_id, access_token=access_token
    )
    for screenshot in screenshots:
        if not screenshot_checksum_matches(
            screenshot=screenshot, screenshot_set_dir=screenshot_set_dir
        ):
            appstore.delete_screenshot(
                screenshot_id=screenshot["id"], access_token=access_token
            )

    # Create new screenshots
    screenshots = appstore.get_screenshots(
        screenshot_set_id=screenshot_set_id, access_token=access_token
    )
    screenshot_file_names = [s["attributes"]["fileName"] for s in screenshots]
    asset_file_names = [
        x
        for x in os.listdir(screenshot_set_dir)
        if os.path.isfile(os.path.join(screenshot_set_dir, x))
    ]
    new_file_names = [x for x in asset_file_names if x not in screenshot_file_names]

    for file_name in new_file_names:
        file_path = os.path.join(screenshot_set_dir, file_name)
        publish_screenshot(
            access_token=access_token,
            screenshot_path=file_path,
            screenshot_set_id=screenshot_set_id,
        )

    # Reorder the screenshots
    print_screenshot_set_status(display_type, colorama.Fore.CYAN, "sorting screenshots")
    screenshots = appstore.get_screenshots(
        screenshot_set_id=screenshot_set_id, access_token=access_token
    )
    screenshots.sort(key=lambda x: x["attributes"]["fileName"])
    screenshot_ids = [x["id"] for x in screenshots]
    appstore.update_screenshot_order(
        screenshot_set_id=screenshot_set_id,
        screenshot_ids=screenshot_ids,
        access_token=access_token,
    )


def publish_screenshot_sets(
    access_token: str,
    localization_dir: str,
    localization_id: str,
):
    """Publish the screenshot sets from assets on disk."""
    screenshots_dir = os.path.join(localization_dir, "screenshots")
    if not os.path.isdir(screenshots_dir):
        print_clr(
            f"    No screenshots: directory {colorama.Fore.CYAN}{screenshots_dir}{colorama.Fore.RESET} not found.",
        )
        return

    screenshot_sets = appstore.get_screenshot_sets(
        localization_id=localization_id, access_token=access_token
    )

    asset_display_types = [
        x
        for x in os.listdir(screenshots_dir)
        if os.path.isdir(os.path.join(screenshots_dir, x))
    ]

    # Create new display types
    loc_display_types = [
        x["attributes"]["screenshotDisplayType"] for x in screenshot_sets
    ]
    new_display_types = [x for x in asset_display_types if x not in loc_display_types]
    for display_type in new_display_types:
        print_screenshot_set_status(
            display_type, colorama.Fore.YELLOW, "creating display type"
        )
        ss_set = appstore.create_screenshot_set(
            localization_id=localization_id,
            display_type=display_type,
            access_token=access_token,
        )
        screenshot_sets.append(ss_set)

    for ss_set in screenshot_sets:
        ss_set_id = ss_set["id"]
        display_type = ss_set["attributes"]["screenshotDisplayType"]
        ss_set_dir = os.path.join(screenshots_dir, display_type)

        # Delete removed display types
        if not os.path.isdir(ss_set_dir):
            print_screenshot_set_status(
                display_type, colorama.Fore.RED, "deleting display type"
            )
            appstore.delete_screenshot_set(
                screenshot_set_id=ss_set_id, access_token=access_token
            )
            continue

        # Publish
        publish_screenshots(
            access_token=access_token,
            screenshot_set_dir=ss_set_dir,
            screenshot_set_id=ss_set_id,
            display_type=display_type,
        )


def publish_version_localizations(
    access_token: str,
    app_dir: str,
    version_id: str,
    allow_create_locale: bool = True,
    allow_delete_locale: bool = True,
):
    localizations = appstore.get_version_localizations(
        version_id=version_id, access_token=access_token
    )

    asset_locales = [
        x for x in os.listdir(app_dir) if os.path.isdir(os.path.join(app_dir, x))
    ]

    # create new localizations
    version_locales = [loc["attributes"]["locale"] for loc in localizations]
    new_locales = [x for x in asset_locales if x not in version_locales]
    if allow_create_locale:
        for locale in new_locales:
            print_locale_status(locale, colorama.Fore.YELLOW, "creating locale")
            loc = appstore.create_version_localization(
                version_id=version_id,
                locale=locale,
                localization_attributes={},
                access_token=access_token,
            )
            localizations.append(loc)
    else:
        for locale in new_locales:
            print_locale_status(
                locale, colorama.Fore.LIGHTBLACK_EX, "locale creation not allowed"
            )

    # publish localizations
    for loc in localizations:
        loc_id = loc["id"]
        loc_attr = loc["attributes"]
        locale = loc_attr["locale"]
        loc_dir = os.path.join(app_dir, locale)

        # Delete removed locales
        if not os.path.isdir(loc_dir):
            if allow_delete_locale:
                print_locale_status(locale, colorama.Fore.RED, "deleting locale")
                appstore.delete_version_localization(
                    localization_id=loc_id, access_token=access_token
                )
            else:
                print_locale_status(
                    locale, colorama.Fore.LIGHTBLACK_EX, "locale deletion not allowed"
                )
            continue

        # Normalize all attribute values to strings
        for key in appstore.VersionLocalizationAttributes.__annotations__.keys():
            if loc_attr[key] is None:
                loc_attr[key] = ""

        # Load local data from disk
        asset_loc_data: appstore.VersionLocalizationAttributes = {}
        for key in appstore.VersionLocalizationAttributes.__annotations__.keys():
            path = os.path.join(loc_dir, key + ".txt")
            content = read_txt_file(path)
            if content is not None:
                asset_loc_data[key] = content  # type: ignore

        # Only need to update if there are differences
        loc_diff_keys = [
            key
            for key, value in asset_loc_data.items()
            if value is not None and value != loc_attr[key]
        ]
        if len(loc_diff_keys) > 0:
            print_locale_status(
                locale,
                colorama.Fore.CYAN,
                f"updating locale {colorama.Fore.CYAN}{colorama.Style.DIM}{loc_diff_keys}",
            )
            appstore.update_version_localization(
                localization_id=loc_id,
                localization_attributes=asset_loc_data,
                access_token=access_token,
            )
        else:
            print_locale_status(
                locale, colorama.Fore.CYAN, "no changes in version settings"
            )

        # Screenshots
        publish_screenshot_sets(
            access_token=access_token,
            localization_dir=loc_dir,
            localization_id=loc_id,
        )


def publish_version(
    access_token: str,
    app_dir: str,
    app_id: str,
    bundle_id: str,
    platform: Union[appstore.Platform, str],  # pylint: disable=unsubscriptable-object
    version_string: str,
    update_version_string: bool,
    allow_create_version: bool = True,
    allow_create_locale: bool = True,
    allow_delete_locale: bool = True,
):
    # Get Versions
    versions = appstore.get_versions(
        app_id=app_id,
        access_token=access_token,
        platforms=[platform],
        states=appstore.editable_version_states,
    )
    print_clr(
        f"Found {colorama.Fore.CYAN}{len(versions)}{colorama.Fore.RESET} editable app versions ",
        f"for {colorama.Fore.CYAN}{platform}{colorama.Fore.RESET}.",
    )

    if len(versions) == 0 and allow_create_version:
        print(
            f"Creating new version: {colorama.Fore.BLUE}{version_string}{colorama.Fore.RESET}"
        )
        created_version = appstore.create_version(
            app_id=app_id,
            platform=platform,
            version_string=version_string,
            access_token=access_token,
        )
        versions.append(created_version)
    elif update_version_string:
        for v in versions:
            version_id = v["id"]
            version_state = v["attributes"]["appStoreState"]

            version_attributes: appstore.VersionAttributes = {
                "versionString": version_string,
            }
            print_clr(
                f"{colorama.Fore.GREEN}Version ",
                f"{colorama.Fore.BLUE}{version_state} ",
                f": updating version ",
                f"{colorama.Fore.CYAN}{version_attributes}",
            )

            appstore.update_version(
                version_id=version_id,
                version_attributes=version_attributes,
                access_token=access_token,
            )

    for v in versions:
        version_id = v["id"]
        version_state = v["attributes"]["appStoreState"]

        print_clr(
            f"{colorama.Fore.GREEN}Version ",
            f"{colorama.Fore.BLUE}{version_id} ",
            f"{colorama.Fore.CYAN}{version_state} ",
        )
        publish_version_localizations(
            access_token=access_token,
            app_dir=app_dir,
            version_id=version_id,
            allow_create_locale=allow_create_locale,
            allow_delete_locale=allow_delete_locale,
        )


def publish_info(
    access_token: str,
    app_dir: str,
    app_id: str,
    bundle_id: str,
    platform: Union[appstore.Platform, str],  # pylint: disable=unsubscriptable-object
):
    # Get Infos
    infos = appstore.get_infos(
        app_id=app_id,
        access_token=access_token,
        states=appstore.editable_version_states,
    )
    print_clr(
        f"Found {colorama.Fore.CYAN}{len(infos)}{colorama.Fore.RESET} editable app infos."
    )

    asset_locales = [
        x for x in os.listdir(app_dir) if os.path.isdir(os.path.join(app_dir, x))
    ]

    for info in infos:
        info_id = info["id"]
        version_state = info["attributes"]["appStoreState"]

        print_clr(
            colorama.Fore.GREEN + "AppInfo ",
            colorama.Fore.BLUE + f"{info_id} ",
            colorama.Fore.CYAN + f"{version_state}",
        )

        localizations = appstore.get_info_localizations(
            info_id=info_id, access_token=access_token
        )

        # create new localizations
        info_locales = [loc["attributes"]["locale"] for loc in localizations]
        new_locales = [x for x in asset_locales if x not in info_locales]
        for locale in new_locales:
            print_locale_status(
                locale, colorama.Fore.LIGHTBLACK_EX, "locale creation not allowed"
            )

        for loc in localizations:
            loc_id = loc["id"]
            loc_attr = loc["attributes"]
            locale = loc_attr["locale"]
            loc_dir = os.path.join(app_dir, locale)

            # Delete removed locales
            if not os.path.isdir(loc_dir):
                print_locale_status(
                    locale, colorama.Fore.LIGHTBLACK_EX, "locale deletion not allowed"
                )
                continue

            # Normalize all attribute values to strings
            for key in appstore.InfoLocalizationAttributes.__annotations__.keys():
                if loc_attr[key] is None:
                    loc_attr[key] = ""

            # Load local data from disk
            asset_loc_data: appstore.InfoLocalizationAttributes = {}
            for key in appstore.InfoLocalizationAttributes.__annotations__.keys():
                path = os.path.join(loc_dir, key + ".txt")
                content = read_txt_file(path)
                if content is not None:
                    asset_loc_data[key] = content  # type: ignore

            # Only need to update if there are differences
            loc_diff_keys = [
                key
                for key, value in asset_loc_data.items()
                if value is not None and value != loc_attr[key]
            ]
            if len(loc_diff_keys) > 0:
                print_locale_status(
                    locale,
                    colorama.Fore.CYAN,
                    f"updating app info {colorama.Fore.CYAN}{colorama.Style.DIM}{loc_diff_keys}",
                )
                appstore.update_info_localization(
                    info_localization_id=loc_id,
                    info_localization_attributes=asset_loc_data,
                    access_token=access_token,
                )
            else:
                print_locale_status(
                    locale, colorama.Fore.CYAN, "no changes in app settings"
                )


def publish(
    access_token: str,
    asset_dir: str,
    app_id: str,
    bundle_id: str,
    platform: Union[appstore.Platform, str],  # pylint: disable=unsubscriptable-object
    version_string: str,
    update_version_string: bool,
    allow_create_version: bool = True,
    allow_create_locale: bool = True,
    allow_delete_locale: bool = True,
):
    """Publish all the app meta data app store, using any editable app versions found.
    If none are found, a new version can be created for the specified target platform."""
    print_clr("Publishing assets from directory: ", colorama.Fore.CYAN + asset_dir)

    # Application directory
    app_dir = os.path.join(asset_dir, bundle_id)
    if not os.path.isdir(app_dir):
        raise FileNotFoundError(
            f"App directory {colorama.Fore.CYAN}{app_dir}{colorama.Fore.RESET} not found. "
        )

    publish_version(
        access_token=access_token,
        app_dir=app_dir,
        app_id=app_id,
        bundle_id=bundle_id,
        platform=platform,
        version_string=version_string,
        update_version_string=update_version_string,
        allow_create_version=allow_create_version,
        allow_create_locale=allow_create_locale,
        allow_delete_locale=allow_delete_locale,
    )
    publish_info(
        access_token=access_token,
        app_dir=app_dir,
        app_id=app_id,
        bundle_id=bundle_id,
        platform=platform,
    )
    print_clr(colorama.Fore.GREEN + "Publish complete")
