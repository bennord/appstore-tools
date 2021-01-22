import os
import hashlib
import colorama
import requests
from typing import Union, Sequence
from appstore_tools import appstore
from appstore_tools.print_util import print_clr, clr, json_term
from .util import (
    read_txt_file,
    print_locale_status,
    print_media_set_status,
    print_media_status,
)


def media_checksum_ok(media, media_asset_dir: str) -> bool:
    """Checks if the appstore checksum matches the asset checksum."""
    file_name = media["attributes"]["fileName"]
    file_path = os.path.join(media_asset_dir, file_name)
    appstore_checksum = media["attributes"]["sourceFileChecksum"]

    if appstore_checksum is None:
        print_media_status(
            file_name,
            colorama.Fore.CYAN,
            "checksum missing (in processing)",
        )
        return False

    if not os.path.isfile(file_path):
        print_media_status(
            file_name,
            colorama.Fore.RED,
            "no source file",
        )
        return False

    with open(file_path, "rb") as file:
        asset_checksum = hashlib.md5(file.read()).hexdigest()
        if asset_checksum == appstore_checksum:
            print_media_status(
                file_name,
                colorama.Fore.CYAN + colorama.Style.DIM,
                clr(
                    f"checksum matched: ",
                    f"{colorama.Style.DIM}{asset_checksum}",
                ),
            )
        else:
            print_media_status(
                file_name,
                colorama.Fore.CYAN,
                clr(
                    f"checksum changed: ",
                    f"{colorama.Style.DIM}{appstore_checksum} -> {asset_checksum}",
                ),
            )
        return asset_checksum == appstore_checksum


def upload_media(media, media_asset_path: str) -> str:
    """Upload media asset (screenshot or preview) to the appstore.

    Returns:
        str: checksum
    """
    file_hash = hashlib.md5()
    upload_operations = media["attributes"]["uploadOperations"]

    for op in upload_operations:
        method: str = op["method"]
        url: str = op["url"]
        headers: dict = {}
        for h in op["requestHeaders"]:
            headers[h["name"]] = h["value"]
        length: int = op["length"]
        offset: int = op["offset"]

        with open(media_asset_path, "rb") as file:
            file.seek(offset)
            file_chunk = file.read(length)

        file_hash.update(file_chunk)
        print_media_status(
            media_asset_path,
            colorama.Fore.CYAN,
            f"uploading chunk (offset: {offset}, length: {length})",
        )
        requests.request(method=method, url=url, headers=headers, data=file_chunk)
    return file_hash.hexdigest()


def get_media_file_names(media: Sequence[dict]):
    return [x["attributes"]["fileName"] for x in media]


def get_asset_file_names(asset_dir: str):
    return [
        x for x in os.listdir(asset_dir) if os.path.isfile(os.path.join(asset_dir, x))
    ]


def get_new_file_paths(media: Sequence[dict], asset_dir: str):
    media_file_names = get_media_file_names(media)
    asset_file_names = get_asset_file_names(asset_dir)
    return [
        os.path.join(asset_dir, x)
        for x in asset_file_names
        if x not in media_file_names
    ]


def publish_screenshot(
    access_token: str,
    screenshot_path: str,
    screenshot_set_id: str,
):
    if not os.path.isfile(screenshot_path):
        raise FileNotFoundError(f"Screenshot path does not exist: {screenshot_path}")

    _, file_name = os.path.split(screenshot_path)
    file_stat = os.stat(screenshot_path)

    # Create
    print_media_status(
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
    # Upload
    checksum = upload_media(media=screenshot, media_asset_path=screenshot_path)

    # Commit
    print_media_status(
        file_name,
        colorama.Fore.CYAN,
        "commiting upload",
    )
    screenshot = appstore.update_screenshot(
        screenshot_id=screenshot["id"],
        uploaded=True,
        sourceFileChecksum=checksum,
        access_token=access_token,
    )


def publish_screenshots(
    access_token: str,
    screenshot_set_dir: str,
    screenshot_set_id: str,
    display_type: str,
):
    print_media_set_status(display_type, colorama.Fore.CYAN, "checking for changes")

    # Delete outdated screenshots
    screenshots = appstore.get_screenshots(
        screenshot_set_id=screenshot_set_id, access_token=access_token
    )
    for screenshot in screenshots:
        if not media_checksum_ok(media=screenshot, media_asset_dir=screenshot_set_dir):
            appstore.delete_screenshot(
                screenshot_id=screenshot["id"], access_token=access_token
            )

    # Create new screenshots
    screenshots = appstore.get_screenshots(
        screenshot_set_id=screenshot_set_id, access_token=access_token
    )

    # Publish
    new_file_paths = get_new_file_paths(screenshots, screenshot_set_dir)
    for file_path in new_file_paths:
        publish_screenshot(
            access_token=access_token,
            screenshot_path=file_path,
            screenshot_set_id=screenshot_set_id,
        )

    # Reorder the screenshots
    print_media_set_status(display_type, colorama.Fore.CYAN, "sorting screenshots")
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
        print_media_set_status(
            display_type, colorama.Fore.YELLOW, "creating display type"
        )
        screenshot_set = appstore.create_screenshot_set(
            localization_id=localization_id,
            display_type=display_type,
            access_token=access_token,
        )
        screenshot_sets.append(screenshot_set)

    for screenshot_set in screenshot_sets:
        screenshot_set_id = screenshot_set["id"]
        display_type = screenshot_set["attributes"]["screenshotDisplayType"]
        screenshot_set_dir = os.path.join(screenshots_dir, display_type)

        # Delete removed display types
        if not os.path.isdir(screenshot_set_dir):
            print_media_set_status(
                display_type, colorama.Fore.RED, "deleting display type"
            )
            appstore.delete_screenshot_set(
                screenshot_set_id=screenshot_set_id, access_token=access_token
            )
            continue

        # Publish
        publish_screenshots(
            access_token=access_token,
            screenshot_set_dir=screenshot_set_dir,
            screenshot_set_id=screenshot_set_id,
            display_type=display_type,
        )


def publish_preview(
    access_token: str,
    preview_path: str,
    preview_set_id: str,
):
    if not os.path.isfile(preview_path):
        raise FileNotFoundError(f"Preview path does not exist: {preview_path}")

    _, file_name = os.path.split(preview_path)
    file_stat = os.stat(preview_path)

    # Create
    print_media_status(
        file_name,
        colorama.Fore.CYAN,
        "reserving asset",
    )
    preview = appstore.create_preview(
        preview_set_id=preview_set_id,
        file_name=file_name,
        file_size=file_stat.st_size,
        access_token=access_token,
    )
    # Upload
    checksum = upload_media(media=preview, media_asset_path=preview_path)

    # Commit
    print_media_status(
        file_name,
        colorama.Fore.CYAN,
        "commiting upload",
    )
    preview = appstore.update_preview(
        preview_id=preview["id"],
        uploaded=True,
        sourceFileChecksum=checksum,
        access_token=access_token,
    )


def publish_previews(
    access_token: str,
    preview_set_dir: str,
    preview_set_id: str,
    display_type: str,
):
    print_media_set_status(display_type, colorama.Fore.CYAN, "checking for changes")

    # Delete outdated previews
    previews = appstore.get_previews(
        preview_set_id=preview_set_id, access_token=access_token
    )
    for preview in previews:
        if not media_checksum_ok(media=preview, media_asset_dir=preview_set_dir):
            appstore.delete_preview(preview_id=preview["id"], access_token=access_token)

    # Create new previews
    previews = appstore.get_previews(
        preview_set_id=preview_set_id, access_token=access_token
    )
    new_file_paths = get_new_file_paths(previews, preview_set_dir)

    # Publish
    for file_path in new_file_paths:
        publish_preview(
            access_token=access_token,
            preview_path=file_path,
            preview_set_id=preview_set_id,
        )

    # Reorder the previews
    print_media_set_status(display_type, colorama.Fore.CYAN, "sorting previews")
    previews = appstore.get_previews(
        preview_set_id=preview_set_id, access_token=access_token
    )
    previews.sort(key=lambda x: x["attributes"]["fileName"])
    preview_ids = [x["id"] for x in previews]
    appstore.update_preview_order(
        preview_set_id=preview_set_id,
        preview_ids=preview_ids,
        access_token=access_token,
    )


def publish_preview_sets(
    access_token: str,
    localization_dir: str,
    localization_id: str,
):
    """Publish the previews sets from assets on disk."""
    previews_dir = os.path.join(localization_dir, "previews")
    if not os.path.isdir(previews_dir):
        print_clr(
            f"    No previews: directory {colorama.Fore.CYAN}{previews_dir}{colorama.Fore.RESET} not found.",
        )
        return

    preview_sets = appstore.get_preview_sets(
        localization_id=localization_id, access_token=access_token
    )

    asset_display_types = [
        x
        for x in os.listdir(previews_dir)
        if os.path.isdir(os.path.join(previews_dir, x))
    ]

    # Create new display types
    loc_preview_types = [x["attributes"]["previewType"] for x in preview_sets]
    new_preview_types = [x for x in asset_display_types if x not in loc_preview_types]
    for preview_type in new_preview_types:
        print_media_set_status(
            preview_type, colorama.Fore.YELLOW, "creating preview type"
        )
        preview_set = appstore.create_preview_set(
            localization_id=localization_id,
            preview_type=preview_type,
            access_token=access_token,
        )
        preview_sets.append(preview_set)

    for preview_set in preview_sets:
        preview_set_id = preview_set["id"]
        preview_type = preview_set["attributes"]["previewType"]
        preview_set_dir = os.path.join(previews_dir, preview_type)

        # Delete removed display types
        if not os.path.isdir(preview_set_dir):
            print_media_set_status(
                preview_type, colorama.Fore.RED, "deleting preview type"
            )
            appstore.delete_preview_set(
                preview_set_id=preview_set_id, access_token=access_token
            )
            continue

        # Publish
        publish_previews(
            access_token=access_token,
            preview_set_dir=preview_set_dir,
            preview_set_id=preview_set_id,
            display_type=preview_type,
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

        # Previews
        publish_preview_sets(
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
