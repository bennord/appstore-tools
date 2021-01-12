import colorama
import modules.appstore_api as appstore
import sys
import os
import logging
import requests
from modules.print_util import color_term, json_term


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


def write_binary_file(path: str, content: bytes):
    file = open(file=path, mode="wb")
    file.write(content)
    file.close()


def write_txt_file(path: str, content: str):
    file = open(file=path, mode="w")
    file.write(content)
    file.close()


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

    app_versions = appstore.get_app_versions(app_id=app_id, access_token=access_token)
    app_versions_selected = [
        {
            "id": v["id"],
            "versionString": v["attributes"]["versionString"],
            "appStoreState": v["attributes"]["appStoreState"],
        }
        for v in app_versions
    ]
    print(json_term({"appId": app_id, "versions": app_versions_selected}))


def list_screenshots(args):
    access_token = get_access_token(args)
    app_id = get_app_id(args, access_token)

    logging.info(color_term(colorama.Fore.GREEN + "app_id: ") + str(app_id))

    live_id = appstore.get_app_live(app_id=app_id, access_token=access_token)["id"]
    logging.info(color_term(colorama.Fore.GREEN + "app_live_id: ") + str(live_id))

    localizations = appstore.get_localizations(
        version_id=live_id, access_token=access_token
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
            print(
                color_term(colorama.Fore.GREEN + f"screenshotDisplayType: ")
                + ss_display_type
            )
            print(json_term(screenshots))


def list_previews(args):
    access_token = get_access_token(args)
    app_id = get_app_id(args, access_token)

    logging.info(color_term(colorama.Fore.GREEN + "app_id: ") + str(app_id))

    live_id = appstore.get_app_live(app_id=app_id, access_token=access_token)["id"]
    logging.info(color_term(colorama.Fore.GREEN + "app_live_id: ") + str(live_id))

    localizations = appstore.get_localizations(
        version_id=live_id, access_token=access_token
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

    print(
        color_term(
            colorama.Fore.GREEN
            + "Downloading assets to local dir: "
            + colorama.Fore.MAGENTA
            + asset_dir
        )
    )

    live_id = appstore.get_app_live(app_id=app_id, access_token=access_token)["id"]

    print(
        color_term(
            f"{colorama.Fore.GREEN}App: "
            + f"{colorama.Fore.MAGENTA}{bundle_id}{colorama.Fore.RESET} "
            + f"(app_id: {colorama.Fore.BLUE}{app_id}{colorama.Fore.RESET}, "
            + f"version_id [Live]: {colorama.Fore.BLUE}{live_id}{colorama.Fore.RESET})"
        )
    )

    localizations = appstore.get_localizations(
        version_id=live_id, access_token=access_token
    )

    for loc in localizations:
        loc_id = loc["id"]
        loc_attr = loc["attributes"]
        locale = loc_attr["locale"]
        loc_dir = os.path.join(asset_dir, bundle_id, locale)

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

        # Save Meta Data
        meta_fields = [
            "description",
            "keywords",
            "marketingUrl",
            "promotionalText",
            "supportUrl",
            "whatsNew",
        ]

        for name in meta_fields:
            content = loc_attr[name] if loc_attr[name] is not None else ""
            write_txt_file(
                path=os.path.join(loc_dir, name + ".txt"),
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
