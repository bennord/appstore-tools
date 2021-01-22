# appstore-tools

Tools for the AppStore Connect API.

This package provides methods to publish, download, and list information about AppStore meta-data (descriptions, keywords, screenshots, previews, etc).  Combined with a deployment workflow (such as github actions), the AppStore meta-data can be tracked and deployed along side the rest of the app's source code and assets.

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

## Code

The actions provided by the command line can also be accessed by import in a python script.

```python
# Import the package
from appstore_tools import appstore, actions

# Get the auth credentials
with open("AuthKey.p8", "r") as file:
    key = file.read()

issuer_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
key_id="XXXXXXXXXX"

# Create an access token
access_token = appstore.create_access_token(
    issuer_id=issuer_id, key_id=key_id, key=key
)

# Call the AppStore connect API
apps = appstore.get_apps(access_token=access_token)

# Or call one of the AppStore-Tools Actions
actions.list_apps(access_token=access_token)

```

## Asset Directory Structure

The `download` and `publish` actions look for assets in the following directory structure starting at `--asset-dir ASSET_DIR`. Screenshots and Previews are sorted alphabetically in the store listing.

To leave an attribute unaffected by the `publish` action, remove the corresponding text file from the tree. An empty text file can be used to set the attribute to an empty string.

Likewise, to leave the screenshots (or previews) unaffected, remove the entire `screenshots` folder. If `screenshots` is present, the `publish` action will add/remove screenshot-display-types and their screenshots to match.

```zsh
[ASSET_DIR]
└── com.example.myapp
    └── en-US
        ├── description.txt
        ├── keywords.txt
        ├── marketingUrl.txt
        ├── name.txt
        ├── previews
        ├── privacyPolicyText.txt
        ├── privacyPolicyUrl.txt
        ├── promotionalText.txt
        ├── screenshots
        │   ├── APP_IPAD_PRO_129
        │   │   ├── 10_Image.png
        │   │   ├── 20_AnotherImage.png
        │   │   ├── 30_MoreImages.png
        │   ├── APP_IPAD_PRO_3GEN_129
        │   │   ├── a_is_the_first_letter.png
        │   │   ├── b_is_the_second_letter.png
        │   │   ├── c_is_the_third_letter.png
        │   ├── APP_IPHONE_55
        │   │   ├── image01.png
        │   │   ├── image02.png
        │   │   ├── image03.png
        │   └── APP_IPHONE_65
        │   │   ├── image01.png
        │   │   ├── image02.png
        │   │   ├── image03.png
        ├── subtitle.txt
        ├── supportUrl.txt
        └── whatsNew.txt
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
