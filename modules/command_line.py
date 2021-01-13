import configargparse
import argparse
import logging
import modules.actions as actions
import modules.appstore_api as appstore
import requests
import sys
from modules.print_util import color_term
import colorama
import argparse_color_formatter
import modules.version as version

DEFAULT_CONFIG_FILES = ["run.config"]
DEFAULT_ASSET_DIR = "appstore"

LOGO_ART = """                                                           
 _____         _____ _                  _____         _     
|  _  |___ ___|   __| |_ ___ ___ ___   |_   _|___ ___| |___ 
|     | . | . |__   |  _| . |  _| -_|    | | | . | . | |_ -|
|__|__|  _|  _|_____|_| |___|_| |___|    |_| |___|___|_|___|
      |_| |_|                                               
"""

EXTRA_INFO_COLOR = colorama.Style.DIM
KEYWORD_COLOR = colorama.Style.DIM + colorama.Fore.LIGHTCYAN_EX
USAGE_COLOR = colorama.Style.DIM + colorama.Fore.CYAN

clr_extra = lambda x: EXTRA_INFO_COLOR + x + colorama.Style.RESET_ALL
clr_keyword = lambda x: KEYWORD_COLOR + x + colorama.Style.RESET_ALL
clr_usage = lambda x: USAGE_COLOR + x + colorama.Style.RESET_ALL


class PrettyHelpFormatter(argparse_color_formatter.ColorRawDescriptionHelpFormatter):
    def _get_help_string(self, action):
        help = action.help
        if action.choices is not None:
            choice_strs = [str(choice) for choice in action.choices]
            choices_colored = [clr_keyword(choice) for choice in choice_strs]
            choices_joined = clr_extra(", ").join(choices_colored)
            help += clr_extra(" {") + choices_joined + clr_extra("}")

        if "%(default)" not in action.help:
            if (
                action.default is not configargparse.SUPPRESS
                and action.default is not None
            ):
                defaulting_nargs = [
                    configargparse.OPTIONAL,
                    configargparse.ZERO_OR_MORE,
                ]
                if action.option_strings or action.nargs in defaulting_nargs:
                    help += (
                        clr_extra(" (default:")
                        + clr_extra("%(default)s")
                        + clr_extra(")")
                    )
        return help

    def _format_usage(self, usage, actions, groups, prefix):
        if prefix is not None or usage is not None:
            return super()._format_usage(usage, actions, groups, prefix)

        prefix = f"{LOGO_ART}\nUsage:\n  "
        usage_colored = clr_usage(
            super()._format_usage(
                usage,
                actions,
                groups,
                "",
            )
        )
        return prefix + usage_colored

    def _format_action(self, action):
        action_invocation = super()._format_action_invocation(action)
        action_invocation_colored = clr_keyword(action_invocation)
        action_text = super()._format_action(action)
        return action_text.replace(action_invocation, action_invocation_colored, 1)


def add_config_argument(parser: configargparse.ArgumentParser):
    parser.add_argument(
        "-c",
        "--config-file",
        is_config_file=True,
        help="Args that start with '--' (eg. --log-level) can also be set in a config file (run.config or specified via -c). "
        + "Config file syntax allows: key=value, flag=true, stuff=[a,b,c] "
        + clr_extra("(details here https://goo.gl/R74nmi)")
        + ". "
        + "If an arg is specified in more than one place, then commandline values override config file values which override defaults.",
    )


def add_version_argument(parser: configargparse.ArgumentParser):
    parser.add_argument(
        "--version",
        action="version",
        version=version.version,
    )


def add_help_argument(parser: configargparse.ArgumentParser):
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="Show this help message."
        + clr_extra(" (help for actions: ")
        + clr_keyword("action --help")
        + clr_extra(")"),
    )


def add_log_level_argument(parser: configargparse.ArgumentParser):
    log_level_choices = list(logging._levelToName.values())
    parser.add_argument(
        "--log-level",
        choices=log_level_choices,
        default=logging.getLevelName(logging.WARNING),
        metavar="LOG_LEVEL",
        help="Set the logging level.",
    )


def add_global_group(parser: configargparse.ArgumentParser):
    global_group = parser.add_argument_group(
        title="General",
    )
    add_help_argument(global_group)
    add_version_argument(global_group)
    add_config_argument(global_group)
    add_log_level_argument(global_group)


def add_asset_dir_argument(parser: configargparse.ArgumentParser):
    parser.add_argument(
        "--asset-dir",
        default=DEFAULT_ASSET_DIR,
        help="The directory where appstore assets are placed.",
    )


def add_subparser(subparsers: argparse._SubParsersAction, name: str, help: str):
    parser = subparsers.add_parser(
        name=name,
        help=help,
        default_config_files=DEFAULT_CONFIG_FILES,
        add_config_file_help=False,
        add_help=False,
        epilog=" ",  # leave an empty line after the message
        formatter_class=PrettyHelpFormatter,
    )
    add_global_group(parser)
    return parser


def add_authentication_group(parser: configargparse.ArgumentParser):
    auth_group = parser.add_argument_group(
        title="Authentication",
        description=clr_extra(
            "Authentication details are configured (and can be copied from) AppStore Connect->Users & Access->Keys."
        ),
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
        title="App ID",
        description=clr_extra(
            "App can either be identified by App ID (integer) or Bundle ID (string)."
        ),
    )
    key_group = app_group.add_mutually_exclusive_group(required=True)
    key_group.add_argument(
        "--app-id",
        type=int,
        help="The integer App ID assigned by the appstore.",
    )
    key_group.add_argument(
        "--bundle-id",
        help='The App\'s Bundle ID in the form "com.example.myapp".',
    )


def run_command_line():
    # Global
    global_parser = configargparse.ArgParser(
        default_config_files=DEFAULT_CONFIG_FILES,
        add_config_file_help=False,
        formatter_class=PrettyHelpFormatter,
        add_help=False,
        epilog=" ",  # leave an empty line after the message
    )
    add_global_group(global_parser)

    # Action subparsers
    action_subparsers = global_parser.add_subparsers(
        title="Action commands",
        dest="action",
        metavar="action",
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
    versions_group = versions_parser.add_argument_group(
        title="Versions",
    )
    versions_group.add_argument(
        "--editable",
        action="store_true",
        help='Filters for versions in an "editable" state.'
        + clr_extra(
            " (details here https://help.apple.com/app-store-connect/#/dev18557d60e)"
        ),
    )
    versions_group.add_argument(
        "--live", action="store_true", help='Filters for versions in an "live" state.'
    )
    add_authentication_group(versions_parser)
    add_app_id_group(versions_parser)

    # Action: screenshots
    screenshots_parser = add_subparser(
        action_subparsers,
        "screenshots",
        help="Lists the screenshots for an app.",
    )
    add_authentication_group(screenshots_parser)
    add_app_id_group(screenshots_parser)

    # Action: previews
    previews_parser = add_subparser(
        action_subparsers,
        "previews",
        help="Lists the previews for an app.",
    )
    add_authentication_group(previews_parser)
    add_app_id_group(previews_parser)

    # Action: download
    download_parser = add_subparser(
        action_subparsers,
        "download",
        help="Download all assets for an app.",
    )
    download_group = download_parser.add_argument_group(
        title="Download",
    )
    add_asset_dir_argument(download_group)
    download_group.add_argument(
        "--overwrite",
        action="store_true",
        help="Allows downloading into an existing app directory and potentially overwriting existing files.",
    )
    download_group.add_argument(
        "--version-state",
        choices=list(x.name for x in appstore.VersionState),
        metavar="VERSION_STATE",
        help="Specify the required appstore version state.  The first matching version will be downloaded. "
        + "By default, the first version listed by the app store is used.",
    )
    add_authentication_group(download_parser)
    add_app_id_group(download_parser)

    # Action: publish
    publish_parser = add_subparser(
        action_subparsers,
        "publish",
        help="Publish all assets for an app.",
    )
    publish_group = publish_parser.add_argument_group(
        title="Publish",
    )
    add_asset_dir_argument(publish_group)
    add_authentication_group(publish_parser)
    add_app_id_group(publish_parser)

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
        elif args.action == "previews":
            actions.list_previews(args)
        elif args.action == "download":
            actions.download_assets(args)
        elif args.action == "publish":
            actions.publish_assets(args)
    except requests.exceptions.SSLError as error:
        sys.exit(error)
    except requests.exceptions.ConnectionError as error:
        sys.exit(error)
    except requests.exceptions.HTTPError as error:
        sys.exit(error)
    except appstore.ResourceNotFoundException as error:
        sys.exit(error)

    return parsed_args
