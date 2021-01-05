import colorama
import modules.argparse_util as argparse_util
import modules.appstore_api as appstore
import sys
import logging
from modules.print_util import color_term, json_term

colorama.init()

args = argparse_util.parse_command_line()

private_key = args.key
logging.debug(
    color_term(colorama.Fore.GREEN + "private_key:\n") +
    private_key)

try:
    access_token = appstore.create_access_token(
        issuer_id=args.issuer_id, key_id=args.key_id, key=private_key)
except ValueError as error:
    sys.exit(error)

logging.debug(
    color_term(colorama.Fore.GREEN + "access_token:\n") +
    access_token)

app_id = args.app_id
if app_id == None:
    app_id = appstore.get_app_id(
        bundle_id=args.bundle_id,
        access_token=access_token)

logging.debug(
    color_term(colorama.Fore.GREEN + "app_id:\n") +
    json_term(app_id))


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

# appstore.fetch(
#     path=f"/apps/{app_id}/appStoreVersions",
#     method="get",
#     access_token=access_token,
#     verbose=verbose)

# appstoreversion_id = "f013a7f5-46e4-4fc4-a377-27de199dee7b"
# localizations_result = appstore.fetch(
#     path=f"/appStoreVersions/{appstoreversion_id}/appStoreVersionLocalizations",
#     method="get",
#     access_token=access_token,
#     verbose=verbose)

# appstoreversionlocalization_id = localizations_result["data"][0]["id"]
# appstore.fetch(
#     path=f"/appStoreVersionLocalizations/{appstoreversionlocalization_id}/appScreenshotSets",
#     method="get",
#     access_token=access_token,
#     verbose=verbose)


# appstore.fetch(
#     path=f"/appScreenshotSets/{app_id}/appScreenshots",
#     method="get",
#     access_token=access_token,
#     verbose=verbose)
