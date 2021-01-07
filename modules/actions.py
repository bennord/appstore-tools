import colorama
import modules.appstore_api as appstore
import sys
import logging
from modules.print_util import color_term, json_term


def get_access_token(args):
    try:
        access_token = appstore.create_access_token(
            issuer_id=args.issuer_id, key_id=args.key_id, key=args.key
        )
    except ValueError as error:
        sys.exit(error)
    return access_token


def get_app_id(args, access_token):
    app_id = args.app_id
    if app_id == None:
        app_id = appstore.get_app_id(
            bundle_id=args.bundle_id, access_token=access_token
        )
    return app_id


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

        screenshot_set_ids = (s["id"] for s in screenshot_sets)
        for ss_set_id in screenshot_set_ids:
            screenshot_sets = appstore.get_screenshots(
                screenshot_set_id=ss_set_id, access_token=access_token
            )
            print(json_term(screenshot_sets))
