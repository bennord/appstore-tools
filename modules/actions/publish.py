import os
import hashlib
import colorama
import requests
import modules.appstore as appstore
from modules.print_util import print_clr, clr, json_term
from .util import (
    read_txt_file,
    print_locale_status,
    print_screenshot_set_status,
    print_screenshot_status,
)
from typing import Union


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
