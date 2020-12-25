import jwt
import argparse

# Verbose logging mode
verbose = True

parser = argparse.ArgumentParser()
parser.add_argument('--issuer-id', required=True)
parser.add_argument('--key-id', required=True)
key_group = parser.add_mutually_exclusive_group(required=True)
key_group.add_argument('--key')
key_group.add_argument('--key-file', type=argparse.FileType('r'))
args = parser.parse_args()
print(args)

# AppStore JWT
# https://developer.apple.com/documentation/appstoreconnectapi/generating_tokens_for_api_requests

# Private Key created in the AppStore Connect Users/Keys
private_key = (args.key if args.key != None else args.key_file.read())
if verbose:
    print("private_key:")
    print(private_key)

# Key ID copied from AppStore Connect
key_id = args.key_id

# Issuer ID copied from AppStore Connect
issuer_id = args.issuer_id

# The token's expiration time, in Unix epoch time; tokens that expire more than
# 20 minutes in the future are not valid (Ex: 1528408800)
experation = 1528408800

audience = "appstoreconnect-v1"

access_type = "Bearer"

access_token = jwt.encode({
    "iss": issuer_id,
    "exp": experation,
    "aud": audience
}, private_key, algorithm="ES256", headers={
    "kid": key_id})

if verbose:
    print("access_token:")
    print(access_token)

# decoded_jwt = jwt.decode(encoded_jwt, "secret", algorithms=["ES256"])
# if verbose:
#    print(decoded_jwt)
