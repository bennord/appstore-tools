import time

import jwt

APPSTORE_AUDIENCE = "appstoreconnect-v1"
APPSTORE_JWT_ALGO = "ES256"


class AccessToken:
    _access_token = None
    _expiration = None

    def __str__(self):
        if time.time() > self._expiration:
            self._create_or_refresh_access_token()
        return self._access_token

    def __repr__(self):
        return self.__str__()

    def __unicode__(self):
        return self.__str__()

    def __init__(self, issuer_id: str, key_id: str, key: str):
        self.issuer_id = issuer_id
        self.key_id = key_id
        self.key = key
        self._create_or_refresh_access_token()

    def _create_or_refresh_access_token(self) -> None:
        """Create an access token for use in the AppStore Connect API."""

        # The token's expiration time, in Unix epoch time; tokens that expire more than
        # 20 minutes in the future are not valid (Ex: 1528408800)
        self._expiration = int(time.time()) + 20 * 60

        # AppStore JWT
        # https://developer.apple.com/documentation/appstoreconnectapi/generating_tokens_for_api_requests
        self._access_token = jwt.encode(
            {"iss": self.issuer_id, "exp": self._expiration, "aud": APPSTORE_AUDIENCE},
            self.key,
            algorithm=APPSTORE_JWT_ALGO,
            headers={"kid": self.key_id},
        )


def create_access_token(issuer_id: str, key_id: str, key: str) -> AccessToken:
    return AccessToken(issuer_id=issuer_id, key_id=key_id, key=key)
