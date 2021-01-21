import colorama
import modules.appstore as appstore
import modules.command_line as command_line
import sys
import os
import logging
import requests
from typing import Union, Optional
from modules.print_util import print_clr, clr, json_term
from .util import write_txt_file, write_binary_file, fetch_screenshot


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
