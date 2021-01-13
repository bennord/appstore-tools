import colorama
import modules.appstore_api as appstore
import modules.command_line as command_line
import sys
import os
import logging
import requests
from modules.print_util import color_term, json_term
from typing import Union


def get_access_token(args):
    try:
        access_token = appstore.create_access_token(
            issuer_id=args.issuer_id, key_id=args.key_id, key=args.key
        )
        return access_token
    except ValueError as error:
        sys.exit(error)


def get_app_id(args, access_token):
    if args.app_id == None:
        args.app_id = appstore.get_app_id(
            bundle_id=args.bundle_id, access_token=access_token
        )
    return args.app_id


def get_bundle_id(args, access_token):
    if args.bundle_id == None:
        args.bundle_id = appstore.get_bundle_id(
            app_id=args.app_id, access_token=access_token
        )
    return args.bundle_id


def fetch_screenshot(screenshot_info: object):
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


def list_apps(args):
    access_token = get_access_token(args)

    apps = appstore.get_apps(access_token=access_token)
    apps_selected = [
        {
            "id": v["id"],
            "name": v["attributes"]["name"],
            "bundleId": v["attributes"]["bundleId"],
            "primaryLocale": v["attributes"]["primaryLocale"],
        }
        for v in apps
    ]
    print(json_term(apps_selected))


def list_versions(args):
    access_token = get_access_token(args)
    app_id = get_app_id(args, access_token)
    platforms = command_line.create_platform_filter_list(args)
    states = command_line.create_version_state_filter_list(args)

    versions = appstore.get_versions(
        app_id=app_id, access_token=access_token, platforms=platforms, states=states
    )
    versions_selected = [
        {
            "id": x["id"],
            "platform": x["attributes"]["platform"],
            "versionString": x["attributes"]["versionString"],
            "appStoreState": x["attributes"]["appStoreState"],
        }
        for x in versions
    ]
    print(json_term({"appId": app_id, "versions": versions_selected}))


def list_screenshots(args):
    access_token = get_access_token(args)
    app_id = get_app_id(args, access_token)
    platforms = command_line.create_platform_filter_list(args)
    states = command_line.create_version_state_filter_list(args)

    logging.info(color_term(colorama.Fore.GREEN + "app_id: ") + str(app_id))

    versions = appstore.get_versions(
        app_id=app_id, access_token=access_token, platforms=platforms, states=states
    )
    for version in versions[: args.version_limit]:
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
                    if args.full
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
                    if args.long
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


def list_previews(args):
    access_token = get_access_token(args)
    app_id = get_app_id(args, access_token)
    platforms = command_line.create_platform_filter_list(args)
    states = command_line.create_version_state_filter_list(args)

    logging.info(color_term(colorama.Fore.GREEN + "app_id: ") + str(app_id))

    versions = appstore.get_versions(
        app_id=app_id, access_token=access_token, platforms=platforms, states=states
    )
    for version in versions[: args.version_limit]:
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


def download_assets(args):
    access_token = get_access_token(args)
    app_id = get_app_id(args, access_token)
    bundle_id = get_bundle_id(args, access_token)
    asset_dir = args.asset_dir
    app_dir = os.path.join(asset_dir, bundle_id)

    print(
        color_term(
            colorama.Fore.GREEN
            + "Using local app directory: "
            + colorama.Fore.BLUE
            + app_dir
        )
    )

    if os.path.isdir(app_dir) and not args.overwrite:
        print(
            f"App directory already exists. Specify '--overwrite' if you wish to force downloading to an existing directory."
        )
        return

    # Get versions
    platforms = [args.platform]
    version_states = (
        [args.version_state]
        if args.version_state is not None
        else list(appstore.VersionState)
    )
    versions = appstore.get_versions(
        app_id=app_id,
        access_token=access_token,
        platforms=platforms,
        states=version_states,
    )
    if len(versions) == 0:
        message = (
            "No app version found: "
            + "platform "
            + f"{colorama.Fore.BLUE}{args.platform}{colorama.Fore.RESET}"
        )
        if args.version_state is not None:
            message += (
                ", version-state "
                + f"{colorama.Fore.BLUE}{args.version_state}{colorama.Fore.RESET}"
            )
        print(color_term(message))
        return

    version = versions[0]
    version_id = version["id"]
    version_state = version["attributes"]["appStoreState"]
    version_platform = version["attributes"]["platform"]

    print(
        color_term(
            f"{colorama.Fore.GREEN}Downloading app version: "
            + f"{colorama.Fore.MAGENTA}{bundle_id}{colorama.Fore.RESET} "
            + f"(app_id: {colorama.Fore.BLUE}{app_id}{colorama.Fore.RESET}, "
            + f"platform: {colorama.Fore.BLUE}{version_platform}{colorama.Fore.RESET}, "
            + f"version_id: {colorama.Fore.BLUE}{version_id}{colorama.Fore.RESET}, "
            + f"version_state: {colorama.Fore.BLUE}{version_state}{colorama.Fore.RESET})"
        )
    )

    localizations = appstore.get_version_localizations(
        version_id=version_id, access_token=access_token
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
                + f"(loc_id: {colorama.Fore.BLUE}{loc_id}{colorama.Fore.RESET}) "
            )
        )

        # Locale directory
        os.makedirs(name=loc_dir, exist_ok=True)

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
            ss_set_dir = os.path.join(loc_dir, ss_display_type)

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
            preview_set_dir = os.path.join(loc_dir, preview_type)

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

    print(color_term(colorama.Fore.GREEN + "Download complete"))


def publish_assets(args):
    access_token = get_access_token(args)
    app_id = get_app_id(args, access_token)
    bundle_id = get_bundle_id(args, access_token)
    asset_dir = args.asset_dir
    platform = args.platform
    version_string = args.version_string

    print(
        color_term(
            colorama.Fore.GREEN
            + "Publishing assets from local dir: "
            + colorama.Fore.MAGENTA
            + asset_dir
        )
    )

    # Application directory
    app_dir = os.path.join(asset_dir, bundle_id)
    if not os.path.isdir(app_dir):
        print(color_term(colorama.Fore.RED + "No app directory found: ") + app_dir)
        return

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

    if len(versions) == 0:
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

    for v in versions:
        version_id = v["id"]
        version_state = v["attributes"]["appStoreState"]

        localizations = appstore.get_version_localizations(
            version_id=version_id, access_token=access_token
        )

        for loc in localizations:
            loc_id = loc["id"]
            loc_attr = loc["attributes"]
            locale = loc_attr["locale"]
            loc_dir = os.path.join(app_dir, locale)

            if not os.path.isdir(loc_dir):
                print(
                    color_term(
                        colorama.Fore.RED + "No app localization directory found: "
                    )
                    + loc_dir
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
                file_loc_data[key] = read_txt_file(path)
                if file_loc_data[key] is None:
                    del file_loc_data[key]

            # Only need to update if there are differences
            if any(
                file_loc_data[key] is not None and file_loc_data[key] != loc_attr[key]
                for key in file_loc_data.keys()
            ):
                print(
                    color_term(colorama.Fore.GREEN + "Version ")
                    + color_term(colorama.Fore.BLUE + str(version_state))
                    + color_term(colorama.Fore.GREEN + ", locale ")
                    + color_term(colorama.Fore.BLUE + str(locale))
                    + ": "
                    + " detected changes... updating"
                )
                appstore.update_version_localization(
                    localization_id=loc_id,
                    access_token=access_token,
                    localization_attributes=file_loc_data,
                )
            else:
                print(
                    color_term(colorama.Fore.GREEN + "Version ")
                    + color_term(colorama.Fore.BLUE + str(version_state))
                    + color_term(colorama.Fore.GREEN + ", locale ")
                    + color_term(colorama.Fore.BLUE + str(locale))
                    + ": "
                    + " no changes... skipping"
                )
