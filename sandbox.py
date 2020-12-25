import jwt
import argparse
import time
import sys


def parseCommandLine():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose logging.')
    auth_group = parser.add_argument_group(
        title='authentication',
        description='Authentication details are configured and can be copied from AppStore Connect->Users & Access->Keys.')
    auth_group.add_argument('--issuer-id', required=True,
                            help='Issuer ID.')
    auth_group.add_argument('--key-id', required=True,
                            help='Key ID.')
    key_group = auth_group.add_mutually_exclusive_group(required=True)
    key_group.add_argument('--key',
                           help='Private Key as a string.')
    key_group.add_argument('--key-file', type=argparse.FileType('r'),
                           help='Private Key from a filepath.')
    return parser.parse_args()


args = parseCommandLine()

# Verbose logging mode
verbose = args.verbose


def createAppStoreToken(issuer_id: str, key_id: str, key: str) -> str:
    """Create an access token for use in the AppStore Connect API."""

    # The token's expiration time, in Unix epoch time; tokens that expire more than
    # 20 minutes in the future are not valid (Ex: 1528408800)
    experation = int(time.time()) + 20 * 60
    audience = "appstoreconnect-v1"

    # AppStore JWT
    # https://developer.apple.com/documentation/appstoreconnectapi/generating_tokens_for_api_requests
    access_token = jwt.encode({
        "iss": issuer_id,
        "exp": experation,
        "aud": audience
    }, key, algorithm="ES256", headers={
        "kid": key_id})
    return access_token


# Private Key created in the AppStore Connect Users/Keys
private_key = (args.key if args.key != None else args.key_file.read())
if verbose:
    print("private_key:")
    print(private_key)

try:
    access_token = createAppStoreToken(
        issuer_id=args.issuer_id, key_id=args.key_id, key=private_key)
except ValueError as error:
    sys.exit(error)

if verbose:
    print("access_token:")
    print(access_token)
