import colorama
import sys
import os
import logging
import requests
from typing import Union, Optional
from appstore_tools import appstore
from appstore_tools.print_util import print_clr, clr, json_term
from appstore_tools.tqdm_util import tqdm_with_redirect
from .util import (
    write_txt_file,
    write_binary_file,
    fetch_screenshot,
    fetch_preview,
    print_info_status,
    print_version_status,
    print_locale_status,
    print_media_set_status,
    print_media_status,
)


def download_version(
    access_token: str,
    app_dir: str,
    app_id: str,
    bundle_id: str,
    platforms: appstore.PlatformList,
    version_states: appstore.VersionStateList = list(appstore.VersionState),
):
    """Download the app version localized strings and media (screenshots/previews) to the app directory."""
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

    print_version_status(
        version_state,
        version_platform,
        "downloading app version asset list",
    )

    # Build a full list of needed assets
    localizations = appstore.get_version_localizations(
        version_id=version_id, access_token=access_token
    )
    asset_total = 0
    asset_size_total = 0
    for loc in localizations:
        loc["screenshotSets"] = appstore.get_screenshot_sets(
            localization_id=loc["id"], access_token=access_token
        )
        for screenshot_set in loc["screenshotSets"]:
            screenshots = appstore.get_screenshots(
                screenshot_set_id=screenshot_set["id"], access_token=access_token
            )
            asset_total += len(screenshots)
            asset_size_total += sum(x["attributes"]["fileSize"] for x in screenshots)
            screenshot_set["screenshots"] = screenshots

        loc["previewSets"] = appstore.get_preview_sets(
            localization_id=loc["id"], access_token=access_token
        )
        for preview_set in loc["previewSets"]:
            previews = appstore.get_previews(
                preview_set_id=preview_set["id"], access_token=access_token
            )
            asset_total += len(previews)
            asset_size_total += sum(x["attributes"]["fileSize"] for x in previews)
            preview_set["previews"] = previews

    # Download/Write all the assets
    with tqdm_with_redirect(
        total=asset_size_total, unit="B", unit_scale=True, colour="green", leave=False
    ) as progress_bar:
        for loc in localizations:
            loc_attr = loc["attributes"]
            locale = loc_attr["locale"]
            loc_dir = os.path.join(app_dir, locale)
            screenshots_dir = os.path.join(loc_dir, "screenshots")
            previews_dir = os.path.join(loc_dir, "previews")

            print_locale_status(
                locale, colorama.Fore.CYAN, "downloading version locale"
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

            for screenshot_set in loc["screenshotSets"]:
                display_type = screenshot_set["attributes"]["screenshotDisplayType"]
                screenshot_set_dir = os.path.join(screenshots_dir, display_type)

                # Screenshot Set directory
                print_media_set_status(
                    display_type, colorama.Fore.CYAN, "downloading screenshot set"
                )
                os.makedirs(name=screenshot_set_dir, exist_ok=True)

                for screenshot in screenshot_set["screenshots"]:
                    file_name = screenshot["attributes"]["fileName"]
                    file_size = screenshot["attributes"]["fileSize"]
                    file_path = os.path.join(screenshot_set_dir, file_name)

                    response = fetch_screenshot(screenshot)
                    if response is None:
                        print_media_status(
                            file_name, colorama.Fore.RED, "no asset (in processing)"
                        )
                    elif response.ok:
                        print_media_status(
                            file_name, colorama.Fore.CYAN, "writing to disk"
                        )
                        write_binary_file(
                            path=file_path,
                            content=response.content,
                        )
                    else:
                        print_media_status(
                            file_name, colorama.Fore.RED, "download failed"
                        )
                    progress_bar.update(file_size)

            for preview_set in loc["previewSets"]:
                preview_type = preview_set["attributes"]["previewType"]
                preview_set_dir = os.path.join(previews_dir, preview_type)

                # Preview Set directory
                print_media_set_status(
                    preview_type, colorama.Fore.CYAN, "downloading preview set"
                )
                os.makedirs(name=preview_set_dir, exist_ok=True)

                for preview in preview_set["previews"]:
                    file_name = preview["attributes"]["fileName"]
                    file_path = os.path.join(preview_set_dir, file_name)

                    response = fetch_preview(preview)
                    if response is None:
                        print_media_status(
                            file_name,
                            colorama.Fore.RED,
                            "no asset (in processing)",
                        )
                    elif response.ok:
                        print_media_status(
                            file_name, colorama.Fore.CYAN, "writing to disk"
                        )
                        write_binary_file(
                            path=file_path,
                            content=response.content,
                        )
                    else:
                        print_media_status(
                            file_name, colorama.Fore.RED, "download failed"
                        )
                    progress_bar.update(file_size)


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

    print_info_status(info_state, "downloading app info")

    # Info Localizations
    localizations = appstore.get_info_localizations(
        info_id=info_id, access_token=access_token
    )

    for loc in localizations:
        loc_attr = loc["attributes"]
        locale = loc_attr["locale"]
        loc_dir = os.path.join(app_dir, locale)

        print_locale_status(locale, colorama.Fore.CYAN, "downloading info locale")

        # Locale directory
        os.makedirs(name=loc_dir, exist_ok=True)

        for key in appstore.InfoLocalizationAttributes.__annotations__.keys():
            content = loc_attr[key] if loc_attr[key] is not None else ""
            write_txt_file(
                path=os.path.join(loc_dir, key + ".txt"),
                content=content,
            )


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
