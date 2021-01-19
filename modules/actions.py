import colorama
import modules.appstore as appstore
import modules.command_line as command_line
import sys
import os
import logging
import requests
from modules.print_util import color_term, json_term
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
            print(
                x["id"]
                + color_term(
                    colorama.Fore.LIGHTBLACK_EX
                    + f' {{{",".join(x["attributes"]["platforms"])}}}'
                )
            )
            for sub in x["relationships"]["subcategories"]["data"]:
                print(color_term(colorama.Style.DIM + f'  {sub["id"]}'))

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
    logging.info(color_term(colorama.Fore.GREEN + "app_id: ") + str(app_id))

    versions = appstore.get_versions(
        app_id=app_id, access_token=access_token, platforms=platforms, states=states
    )
    for version in versions[:version_limit]:
        version_id = version["id"]
        version_state = version["attributes"]["appStoreState"]
        print(
            color_term(
                f"{colorama.Fore.GREEN}version: {colorama.Fore.BLUE}{version_id} {version_state}"
            )
        )

        localizations = appstore.get_version_localizations(
            version_id=version_id, access_token=access_token
        )

        localization_ids = (l["id"] for l in localizations)
        for loc_id in localization_ids:
            screenshot_sets = appstore.get_screenshot_sets(
                localization_id=loc_id, access_token=access_token
            )
            print(
                color_term(colorama.Fore.GREEN + f"loc_id {loc_id}: ")
                + f"Found {colorama.Fore.CYAN}{len(screenshot_sets)}{colorama.Fore.RESET} screenshot sets."
            )

            for screenshot_set in screenshot_sets:
                ss_set_id = screenshot_set["id"]
                ss_display_type = screenshot_set["attributes"]["screenshotDisplayType"]
                screenshots = appstore.get_screenshots(
                    screenshot_set_id=ss_set_id, access_token=access_token
                )
                screenshots = (
                    screenshots
                    if verbosity == Verbosity.FULL
                    else [
                        {
                            "id": x["id"],
                            "fileSize": x["attributes"]["fileSize"],
                            "fileName": x["attributes"]["fileName"],
                            "sourceFileChecksum": x["attributes"]["sourceFileChecksum"],
                            "templateUrl": x["attributes"]["imageAsset"]["templateUrl"],
                            "width": x["attributes"]["imageAsset"]["width"],
                            "height": x["attributes"]["imageAsset"]["height"],
                        }
                        for x in screenshots
                    ]
                    if verbosity == Verbosity.LONG
                    else [x["attributes"]["fileName"] for x in screenshots]
                )
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
    logging.info(color_term(colorama.Fore.GREEN + "app_id: ") + str(app_id))

    versions = appstore.get_versions(
        app_id=app_id, access_token=access_token, platforms=platforms, states=states
    )
    for version in versions[:version_limit]:
        version_id = version["id"]
        version_state = version["attributes"]["appStoreState"]
        print(
            color_term(
                f"{colorama.Fore.GREEN}version: {colorama.Fore.BLUE}{version_id} {version_state}"
            )
        )

        localizations = appstore.get_version_localizations(
            version_id=version_id, access_token=access_token
        )

        localization_ids = (l["id"] for l in localizations)
        for loc_id in localization_ids:
            preview_sets = appstore.get_preview_sets(
                localization_id=loc_id, access_token=access_token
            )
            print(
                color_term(colorama.Fore.GREEN + f"loc_id {loc_id}: ")
                + f"Found {colorama.Fore.CYAN}{len(preview_sets)}{colorama.Fore.RESET} preview sets."
            )

            for preview_set in preview_sets:
                preview_set_id = preview_set["id"]
                preview_type = preview_set["attributes"]["previewType"]
                preview_set = appstore.get_previews(
                    preview_set_id=preview_set_id, access_token=access_token
                )
                print(color_term(colorama.Fore.GREEN + f"previewType: ") + preview_type)
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
        raise appstore.ResourceNotFoundException(color_term(message))

    info = infos[0]
    info_id = info["id"]
    info_state = info["attributes"]["appStoreState"]

    print(
        color_term(
            f"{colorama.Fore.GREEN}Downloading app info: "
            + f"{colorama.Fore.BLUE}{info_id}{colorama.Fore.RESET}, "
            + f"{colorama.Fore.CYAN}{info_state}{colorama.Fore.RESET}"
        )
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

        print(
            color_term(
                colorama.Fore.GREEN
                + "Locale: "
                + f"{colorama.Fore.MAGENTA}{locale}{colorama.Fore.RESET} "
                + f"{colorama.Fore.BLUE}{loc_id}{colorama.Fore.RESET}"
            )
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
        raise appstore.ResourceNotFoundException(color_term(message))

    version = versions[0]
    version_id = version["id"]
    version_state = version["attributes"]["appStoreState"]
    version_platform = version["attributes"]["platform"]

    print(
        color_term(
            f"{colorama.Fore.GREEN}Downloading app version: "
            + f"{colorama.Fore.BLUE}{version_id}{colorama.Fore.RESET}, "
            + f"{colorama.Fore.CYAN}{version_platform}{colorama.Fore.RESET}, "
            + f"{colorama.Fore.CYAN}{version_state}{colorama.Fore.RESET}"
        )
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

        print(
            color_term(
                colorama.Fore.GREEN
                + "Locale: "
                + f"{colorama.Fore.MAGENTA}{locale}{colorama.Fore.RESET} "
                + f"{colorama.Fore.BLUE}{loc_id}{colorama.Fore.RESET}"
            )
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
                    print(color_term(colorama.Fore.RED + "FAILED"))

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
                print(
                    color_term(colorama.Fore.RED + "PREVIEW DOWNLOAD NOT IMPLEMENTED")
                )
                # TODO: add fetch_preview functionality similar to screenshots

                # response = fetch_screenshot(screenshot)
                # if response.ok:
                #     write_binary_file(
                #         path=ss_path,
                #         content=response.content,
                #     )
                # else:
                #     print(color_term(colorama.Fore.RED + "FAILED"))


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

    print(
        color_term(
            f"{colorama.Fore.CYAN}{bundle_id} "
            + f"{colorama.Fore.BLUE}{app_id} "
            + f"{colorama.Fore.RESET}-> "
            + f"{colorama.Fore.CYAN}{app_dir}"
        )
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
    print(color_term(colorama.Fore.GREEN + "Download complete"))


def print_locale_status(locale: str, locale_color: str, status: str):
    print(
        color_term(f"  {locale_color}{locale:5}{colorama.Style.RESET_ALL} - {status}")
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
    print(
        color_term(
            f"Found {colorama.Fore.CYAN}{len(infos)}{colorama.Fore.RESET} editable app infos."
        )
    )

    file_locales = [
        x for x in os.listdir(app_dir) if os.path.isdir(os.path.join(app_dir, x))
    ]

    for info in infos:
        info_id = info["id"]
        version_state = info["attributes"]["appStoreState"]

        print(
            color_term(colorama.Fore.GREEN + "AppInfo ")
            + color_term(colorama.Fore.BLUE + f"{info_id} ")
            + color_term(colorama.Fore.CYAN + f"{version_state}")
        )

        localizations = appstore.get_info_localizations(
            info_id=info_id, access_token=access_token
        )

        # create new localizations
        info_locales = [loc["attributes"]["locale"] for loc in localizations]
        new_locales = [x for x in file_locales if x not in info_locales]
        for locale in new_locales:
            print_locale_status(
                locale, colorama.Fore.LIGHTBLACK_EX, "creation not allowed"
            )

        for loc in localizations:
            loc_id = loc["id"]
            loc_attr = loc["attributes"]
            locale = loc_attr["locale"]
            loc_dir = os.path.join(app_dir, locale)

            # Delete removed locales
            if not os.path.isdir(loc_dir):
                print_locale_status(
                    locale, colorama.Fore.LIGHTBLACK_EX, "deletion not allowed"
                )
                continue

            # Normalize all attribute values to strings
            for key in appstore.InfoLocalizationAttributes.__annotations__.keys():
                if loc_attr[key] is None:
                    loc_attr[key] = ""

            # Load local data from disk
            file_loc_data: appstore.InfoLocalizationAttributes = {}
            for key in appstore.InfoLocalizationAttributes.__annotations__.keys():
                path = os.path.join(loc_dir, key + ".txt")
                content = read_txt_file(path)
                if content is not None:
                    file_loc_data[key] = content  # type: ignore

            # Only need to update if there are differences
            loc_diff_keys = [
                key
                for key, value in file_loc_data.items()
                if value is not None and value != loc_attr[key]
            ]
            if len(loc_diff_keys) > 0:
                print_locale_status(
                    locale,
                    colorama.Fore.CYAN,
                    f"updating {colorama.Fore.CYAN}{colorama.Style.DIM}{loc_diff_keys}",
                )
                appstore.update_info_localization(
                    info_localization_id=loc_id,
                    info_localization_attributes=file_loc_data,
                    access_token=access_token,
                )
            else:
                print_locale_status(locale, colorama.Fore.CYAN, "no changes")


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
    print(
        color_term(
            f"Found {colorama.Fore.CYAN}{len(versions)}{colorama.Fore.RESET} editable app versions "
            + f"for {colorama.Fore.CYAN}{platform}{colorama.Fore.RESET}."
        )
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
            print(
                color_term(colorama.Fore.GREEN + "Version ")
                + color_term(colorama.Fore.BLUE + str(version_state))
                + ": updating version "
                + color_term(colorama.Fore.CYAN + str(version_attributes))
            )

            appstore.update_version(
                version_id=version_id,
                version_attributes=version_attributes,
                access_token=access_token,
            )

    file_locales = [
        x for x in os.listdir(app_dir) if os.path.isdir(os.path.join(app_dir, x))
    ]

    for v in versions:
        version_id = v["id"]
        version_state = v["attributes"]["appStoreState"]

        print(
            color_term(colorama.Fore.GREEN + "Version ")
            + color_term(colorama.Fore.BLUE + f"{version_id} ")
            + color_term(colorama.Fore.CYAN + f"{version_state}")
        )

        localizations = appstore.get_version_localizations(
            version_id=version_id, access_token=access_token
        )

        # create new localizations
        version_locales = [loc["attributes"]["locale"] for loc in localizations]
        new_locales = [x for x in file_locales if x not in version_locales]
        if allow_create_locale:
            for locale in new_locales:
                print_locale_status(locale, colorama.Fore.YELLOW, "creating")
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
                    locale, colorama.Fore.LIGHTBLACK_EX, "creation not allowed"
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
                    print_locale_status(locale, colorama.Fore.RED, "deleting")
                    appstore.delete_version_localization(
                        localization_id=loc_id, access_token=access_token
                    )
                else:
                    print_locale_status(
                        locale, colorama.Fore.LIGHTBLACK_EX, "deletion not allowed"
                    )
                continue

            # Normalize all attribute values to strings
            for key in appstore.VersionLocalizationAttributes.__annotations__.keys():
                if loc_attr[key] is None:
                    loc_attr[key] = ""

            # Load local data from disk
            file_loc_data: appstore.VersionLocalizationAttributes = {}
            for key in appstore.VersionLocalizationAttributes.__annotations__.keys():
                path = os.path.join(loc_dir, key + ".txt")
                content = read_txt_file(path)
                if content is not None:
                    file_loc_data[key] = content  # type: ignore

            # Only need to update if there are differences
            loc_diff_keys = [
                key
                for key, value in file_loc_data.items()
                if value is not None and value != loc_attr[key]
            ]
            if len(loc_diff_keys) > 0:
                print_locale_status(
                    locale,
                    colorama.Fore.CYAN,
                    f"updating {colorama.Fore.CYAN}{colorama.Style.DIM}{loc_diff_keys}",
                )
                appstore.update_version_localization(
                    localization_id=loc_id,
                    localization_attributes=file_loc_data,
                    access_token=access_token,
                )
            else:
                print_locale_status(locale, colorama.Fore.CYAN, "no changes")


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
    print(
        color_term(
            "Publishing assets from directory: " + colorama.Fore.CYAN + asset_dir
        )
    )

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
    print(color_term(colorama.Fore.GREEN + "Publish complete"))
