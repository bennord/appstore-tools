import configargparse
import argparse
import logging
import modules.actions as actions
import requests
import sys
from modules.print_util import color_term
import colorama

DEFAULT_CONFIG_FILES = ["run.config"]
DEFAULT_ASSET_DIR = "appstore"


def help_color(text: str):
    return color_term(colorama.Fore.LIGHTBLACK_EX + text)


def add_config_argument(parser: configargparse.ArgumentParser):
    parser.add_argument(
        "-c",
        "--config-file",
        is_config_file=True,
        help=help_color(
            "Args that start with '--' (eg. --log-level) can also be set in a config file (run.config or specified via -c). "
            + "Config file syntax allows: key=value, flag=true, stuff=[a,b,c] (for details, see syntax at https://goo.gl/R74nmi). "
            + "If an arg is specified in more than one place, then commandline values override config file values which override defaults."
        ),
    )


def add_asset_dir_argument(parser: configargparse.ArgumentParser):
    parser.add_argument(
        "--asset-dir",
        default=DEFAULT_ASSET_DIR,
        help=help_color("The directory where appstore assets are placed."),
    )


def add_subparser(subparsers: argparse._SubParsersAction, name: str, help: str):
    parser = subparsers.add_parser(
        name=name,
        help=help_color(help),
        default_config_files=DEFAULT_CONFIG_FILES,
        add_config_file_help=False,
    )
    add_config_argument(parser)
    return parser


def add_authentication_group(parser: configargparse.ArgumentParser):
    auth_group = parser.add_argument_group(
        title="authentication",
        description=help_color(
            "Authentication details are configured (and can be copied from) AppStore Connect->Users & Access->Keys."
        ),
    )
    auth_group.add_argument("--issuer-id", required=True, help=help_color("Issuer ID."))
    auth_group.add_argument("--key-id", required=True, help=help_color("Key ID."))
    key_group = auth_group.add_mutually_exclusive_group(required=True)
    key_group.add_argument("--key", help=help_color("Private Key as a string."))
    key_group.add_argument(
        "--key-file",
        type=configargparse.FileType(mode="r"),
        help=help_color("Private Key from a filepath."),
    )


def add_app_id_group(parser: configargparse.ArgumentParser):
    app_group = parser.add_argument_group(
        title="app",
        description=help_color(
            "App can either be identified by App ID (integer) or Bundle ID (string)."
        ),
    )
    key_group = app_group.add_mutually_exclusive_group(required=True)
    key_group.add_argument(
        "--app-id",
        type=int,
        help=help_color("The integer App ID assigned by the appstore."),
    )
    key_group.add_argument(
        "--bundle-id",
        help=help_color('The App\'s Bundle ID in the form "com.example.myapp".'),
    )


def run_command_line():
    global_parser = configargparse.ArgParser(
        default_config_files=DEFAULT_CONFIG_FILES,
        add_config_file_help=False,
    )

    # Global args
    add_config_argument(global_parser)
    log_level_choices = list(logging._levelToName.values())
    global_parser.add_argument(
        "--log-level",
        choices=log_level_choices,
        default=logging.getLevelName(logging.WARNING),
        metavar="LOG_LEVEL",
        help=help_color(f"Set the logging level. {log_level_choices}"),
    )

    # Action subparsers
    action_subparsers = global_parser.add_subparsers(
        dest="action",
        metavar="action",
        help=help_color("Choose an action to run."),
        required=True,
        parser_class=configargparse.ArgParser,
    )

    # Action: apps
    apps_parser = add_subparser(
        action_subparsers,
        "apps",
        help=help_color("Lists all apps under the app store account."),
    )
    add_authentication_group(apps_parser)

    # Action: versions
    versions_parser = add_subparser(
        action_subparsers,
        "versions",
        help=help_color("Lists all app versions."),
    )
    add_authentication_group(versions_parser)
    add_app_id_group(versions_parser)

    # Action: screenshots
    screenshots_parser = add_subparser(
        action_subparsers,
        "screenshots",
        help=help_color("Lists the screnshots for an app."),
    )
    add_authentication_group(screenshots_parser)
    add_app_id_group(screenshots_parser)

    # Action: download
    download_parser = add_subparser(
        action_subparsers,
        "download",
        help=help_color("Download all assets for an app."),
    )
    add_authentication_group(download_parser)
    add_app_id_group(download_parser)
    add_asset_dir_argument(download_parser)

    # Action: publish
    publish_parser = add_subparser(
        action_subparsers,
        "publish",
        help=help_color("Publish all assets for an app."),
    )
    add_authentication_group(publish_parser)
    add_app_id_group(publish_parser)
    add_asset_dir_argument(publish_parser)

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
