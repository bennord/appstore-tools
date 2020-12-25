import modules.argparse_util as argparse_util
import modules.appstore_api as appstore
import sys

args = argparse_util.parseCommandLine()

# Verbose logging mode
verbose = args.verbose

# Private Key created in the AppStore Connect Users/Keys
private_key = (args.key if args.key != None else args.key_file.read())
if verbose:
    print("private_key:")
    print(private_key)

try:
    access_token = appstore.create_access_token(
        issuer_id=args.issuer_id, key_id=args.key_id, key=private_key)
except ValueError as error:
    sys.exit(error)

if verbose:
    print("access_token:")
    print(access_token)

# https://apps.apple.com/us/app/lionbridge-ai/id1534701695#?platform=iphone
response = appstore.fetch(
    path="/apps/{id}/appInfos".format(id=1534701695), method="get", access_token=access_token, verbose=verbose)