# appstore-tools

Tools for the AppStore Connect API.

This package is designed to provide a way to store AppStore data (descriptions, keywords, screenshots, previews, etc) in a `git` repo and publish changes from the command line or python script.

## Install

```zsh
pip install appstore-tools
```

## Usage

```zsh
appstore-tools [-h] [--version] action [args]
```

Examples:

```zsh
# List all apps under the app store account
appstore-tools apps

# Download the assets for an app
appstore-tools download --bundle-id com.example.myapp --asset-dir myassets

# Publish the assets for an app
appstore-tools publish --bundle-id com.example.myapp --asset-dir myassets
```

## Usage Config

Most actions will require authentication with the AppStore Connect API, as well as specifying which app to target.

All these parameters can be passed via command line argument, but for convenience, they (and any others) can also be loaded from a config file.

Use the default config file path of `appstore_tools.config`, or specify another with `--config-file CONFIG_FILE`.

```ini
; appstore_tools.config
; sample contents
issuer-id=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
key-id=XXXXXXXXXX
key-file=/home/me/AppStoreConnect_AuthKey_XXXXXXXXXX.p8
bundle-id=com.example.myapp
```

## Code Usage

```python
# Import the package
from appstore_tools import appstore

# Get the auth credentials
with open("AuthKey.p8", "r") as file:
    key = file.read()

issuer_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
key_id="XXXXXXXXXX"

# Create an access token
access_token = appstore.create_access_token(
    issuer_id=issuer_id, key_id=key_id, key=key
)

# Call the API
apps = appstore.get_apps(access_token=access_token)

```

## Source

Clone the source code

```zsh
git clone https://github.com/bennord/appstore-tools.git
```

Install dependencies

```zsh
poetry install
```

Run from within project environment

```zsh
poetry shell
appstore-tools --version
```
