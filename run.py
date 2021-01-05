import colorama
import modules.argparse_util as argparse_util
import modules.appstore_api as appstore
import sys
import logging
from modules.print_util import color_term, json_term

colorama.init()

args = argparse_util.parse_command_line()

private_key = args.key

try:
    access_token = appstore.create_access_token(
        issuer_id=args.issuer_id, key_id=args.key_id, key=private_key
    )
except ValueError as error:
    sys.exit(error)

app_id = args.app_id
if app_id == None:
    app_id = appstore.get_app_id(bundle_id=args.bundle_id, access_token=access_token)

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


# appstore.fetch(
#     path=f"/apps/{app_id}?fields=bundleId",
#     method="get",
#     access_token=access_token,
#     verbose=verbose)

# appstore.fetch(
#     path=f"/apps/{app_id}/appInfos",
#     method="get",
#     access_token=access_token,
#     verbose=verbose)

# appstore.fetch(
#     path=f"/apps/{app_id}/appInfos?include=appInfoLocalizations",
#     method="get",
#     access_token=access_token,
#     verbose=verbose)
