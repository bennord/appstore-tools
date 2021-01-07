import configargparse
import argparse
import logging
import modules.actions as actions
import requests
import sys

DEFAULT_CONFIG_FILES = ["run.config"]
DEFAULT_ASSET_DIR = "appstore"


def add_config_argument(parser: configargparse.ArgumentParser):
    parser.add_argument(
        "-c", "--config-file", is_config_file=True, help="Config filepath."
    )


def add_subparser(subparsers: argparse._SubParsersAction, name: str, help: str):
    parser = subparsers.add_parser(
        name=name,
        help=help,
        default_config_files=DEFAULT_CONFIG_FILES,
    )
    add_config_argument(parser)
    return parser


def add_authentication_group(parser: configargparse.ArgumentParser):
    auth_group = parser.add_argument_group(
        title="authentication",
        description="Authentication details are configured (and can be copied from) AppStore Connect->Users & Access->Keys.",
    )
    auth_group.add_argument("--issuer-id", required=True, help="Issuer ID.")
    auth_group.add_argument("--key-id", required=True, help="Key ID.")
    key_group = auth_group.add_mutually_exclusive_group(required=True)
    key_group.add_argument("--key", help="Private Key as a string.")
    key_group.add_argument(
        "--key-file",
        type=configargparse.FileType(mode="r"),
        help="Private Key from a filepath.",
    )


def add_app_id_group(parser: configargparse.ArgumentParser):
    app_group = parser.add_argument_group(
        title="app",
        description="App can either be identified by App ID (integer) or Bundle ID (string).",
    )
    key_group = app_group.add_mutually_exclusive_group(required=True)
    key_group.add_argument(
        "--app-id", type=int, help="The integer App ID assigned by the appstore."
    )
    key_group.add_argument(
        "--bundle-id", help='The App\'s Bundle ID in the form "com.example.myapp".'
    )


def run_command_line():
    global_parser = configargparse.ArgParser(
        default_config_files=DEFAULT_CONFIG_FILES,
        formatter_class=configargparse.ArgumentDefaultsHelpFormatter,
    )

    # Global args
    add_config_argument(global_parser)
    global_parser.add_argument(
        "--log-level",
        choices=logging._levelToName.values(),
        default=logging.getLevelName(logging.WARNING),
        help="Set the logging level.",
    )

    # Action subparsers
    action_subparsers = global_parser.add_subparsers(
        title="action",
        dest="action",
        required=True,
        parser_class=configargparse.ArgParser,
    )

    # Action: apps
    apps_parser = add_subparser(
        action_subparsers,
        "apps",
        help="Lists all apps under the app store account.",
    )
    add_authentication_group(apps_parser)

    # Action: versions
    versions_parser = add_subparser(
        action_subparsers,
        "versions",
        help="Lists all app versions.",
    )
    add_authentication_group(versions_parser)
    add_app_id_group(versions_parser)

    # Action: screenshots
    screenshots_parser = add_subparser(
        action_subparsers,
        "screenshots",
        help="Lists the screnshots for an app.",
    )
    add_authentication_group(screenshots_parser)
    add_app_id_group(screenshots_parser)

    # Action: download
    download_parser = add_subparser(
        action_subparsers,
        "download",
        help="Download all assets for an app.",
    )
    add_authentication_group(download_parser)
    add_app_id_group(download_parser)
    download_parser.add_argument(
        "--asset-dir",
        default=DEFAULT_ASSET_DIR,
        help="The directory where appstore assets are placed.",
    )

    # Parse
    parsed_args = global_parser.parse_known_args()

    # tuple { matched_args, remaining_args }
    args = parsed_args[0]

    # Handle loading the auth key from file
    if "key" in args and "key_file" in args and args.key == None:
        args.key = args.key_file.read()
        args.key_file.close()

    # Set LogLevel
    logging.getLogger().setLevel(args.log_level)

    # Run
    try:
        if args.action == "apps":
            actions.list_apps(args)
        elif args.action == "versions":
            actions.list_versions(args)
        elif args.action == "screenshots":
            actions.list_screenshots(args)
        elif args.action == "download":
            actions.download_assets(args)
    except requests.exceptions.SSLError as error:
        sys.exit(error)
    except requests.exceptions.ConnectionError as error:
        sys.exit(error)

    return parsed_args
