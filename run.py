import colorama
import modules.argparse_util as argparse_util
import modules.appstore_api as appstore
import sys
from modules.print_util import print_color_reset

colorama.init()

args = argparse_util.parseCommandLine()

# Verbose logging mode
verbose = args.verbose

# Private Key created in the AppStore Connect Users/Keys
private_key = (args.key if args.key != None else args.key_file.read())
if verbose:
    print_color_reset(colorama.Fore.GREEN + "private_key:")
    print(private_key)

try:
    access_token = appstore.create_access_token(
        issuer_id=args.issuer_id, key_id=args.key_id, key=private_key)
except ValueError as error:
    sys.exit(error)

if verbose:
    print_color_reset(colorama.Fore.GREEN + "access_token:")
    print(access_token)

# https://apps.apple.com/us/app/lionbridge-ai/id1534701695#?platform=iphone
app_id = 1534701695
localization_id = "2d4ae30d-7227-4f25-99e8-fca502d1844"

# appstore.fetch(
#     path=f"/apps/{app_id}",
#     method="get",
#     access_token=access_token,
#     verbose=verbose)

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

appstoreversion_id = "f013a7f5-46e4-4fc4-a377-27de199dee7b"
localizations_result = appstore.fetch(
    path=f"/appStoreVersions/{appstoreversion_id}/appStoreVersionLocalizations",
    method="get",
    access_token=access_token,
    verbose=verbose)

appstoreversionlocalization_id = localizations_result["data"][0]["id"]
appstore.fetch(
    path=f"/appStoreVersionLocalizations/{appstoreversionlocalization_id}/appScreenshotSets",
    method="get",
    access_token=access_token,
    verbose=verbose)


# appstore.fetch(
#     path=f"/appScreenshotSets/{app_id}/appScreenshots",
#     method="get",
#     access_token=access_token,
#     verbose=verbose)
