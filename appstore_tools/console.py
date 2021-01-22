import configargparse
import argparse
import logging
import appstore_tools.console_actions as console_actions
import appstore_tools.appstore as appstore
import appstore_tools.actions as actions
import requests
import sys
from appstore_tools.print_util import print_clr, clr, clr_extra, clr_keyword, clr_usage
import colorama
import argparse_color_formatter
import appstore_tools.version as version

DEFAULT_CONFIG_FILES = ["appstore_tools.config"]
DEFAULT_ASSET_DIR = "appstore"

LOGO_ART = """                                                           
 _____         _____ _                  _____         _     
|  _  |___ ___|   __| |_ ___ ___ ___   |_   _|___ ___| |___ 
|     | . | . |__   |  _| . |  _| -_|    | | | . | . | |_ -|
|__|__|  _|  _|_____|_| |___|_| |___|    |_| |___|___|_|___|
      |_| |_|                                               
"""


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


def arg_type_positive_int(arg):
    i = int(arg)
    if i < 1:
        raise configargparse.ArgumentTypeError(
            f"{arg} is an invalid positive int value"
        )
    return i


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


def add_platform_argument(parser: configargparse.ArgumentParser):
    parser.add_argument(
        "--platform",
        choices=list(x.name for x in appstore.Platform),
        default=appstore.Platform.IOS.name,
        metavar="PLATFORM",
        help="Specify the target platform.",
    )


def add_platform_filter_argument(parser: configargparse.ArgumentParser):
    parser.add_argument(
        "--platform",
        choices=list(x.name for x in appstore.Platform),
        metavar="PLATFORM",
        help="Filter by target platform.",
    )


def add_editable_filter_argument(parser: configargparse.ArgumentParser):
    parser.add_argument(
        "--editable",
        action="store_true",
        help='Filter for versions in an "editable" state.'
        + clr_extra(
            " (details here https://help.apple.com/app-store-connect/#/dev18557d60e)"
        ),
    )


def add_live_filter_argument(parser: configargparse.ArgumentParser):
    parser.add_argument(
        "--live", action="store_true", help='Filter for versions in an "live" state.'
    )


def add_version_state_filter_argument(parser: configargparse.ArgumentParser):
    parser.add_argument(
        "--version-state",
        choices=list(x.name for x in appstore.VersionState),
        metavar="VERSION_STATE",
        help="Filter by appstore version state.",
    )


def add_info_filters_group(parser: configargparse.ArgumentParser):
    filter_group = parser.add_argument_group(
        title="Result filters",
    )
    add_editable_filter_argument(filter_group)
    add_live_filter_argument(filter_group)
    add_version_state_filter_argument(filter_group)


def add_version_filters_group(parser: configargparse.ArgumentParser):
    filter_group = parser.add_argument_group(
        title="Result filters",
    )
    add_platform_filter_argument(filter_group)
    add_editable_filter_argument(filter_group)
    add_live_filter_argument(filter_group)
    add_version_state_filter_argument(filter_group)


def create_platform_filter_list(args):
    return [args.platform] if args.platform is not None else list(appstore.Platform)


def create_version_state_filter_list(args):
    return (
        appstore.editable_version_states
        if args.editable
        else appstore.live_version_state
        if args.live
        else [args.version_state]
        if args.version_state is not None
        else list(appstore.VersionState)
    )


def add_verbosity_arguments(parser: configargparse.ArgumentParser):
    parser.add_argument(
        "--long",
        action="store_const",
        default=actions.Verbosity.SHORT,
        const=actions.Verbosity.LONG,
        dest="verbosity",
        help="Print out more information.",
    )
    parser.add_argument(
        "--full",
        action="store_const",
        const=actions.Verbosity.FULL,
        dest="verbosity",
        help="Print out full information.",
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


def run():
    """Run appstore-tools from the command-line."""
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
        help="List all apps under the app store account.",
    )
    apps_group = apps_parser.add_argument_group(
        title="Apps",
    )
    add_verbosity_arguments(apps_group)
    add_authentication_group(apps_parser)

    # Action: infos
    infos_parser = add_subparser(
        action_subparsers,
        "infos",
        help="List all app infos.",
    )
    infos_group = infos_parser.add_argument_group(
        title="Infos",
    )
    add_verbosity_arguments(infos_group)
    add_info_filters_group(infos_parser)
    add_authentication_group(infos_parser)
    add_app_id_group(infos_parser)

    # Action: versions
    versions_parser = add_subparser(
        action_subparsers,
        "versions",
        help="List all app versions.",
    )
    versions_group = versions_parser.add_argument_group(
        title="Versions",
    )
    add_verbosity_arguments(versions_group)
    add_version_filters_group(versions_parser)
    add_authentication_group(versions_parser)
    add_app_id_group(versions_parser)

    # Action: screenshots
    screenshots_parser = add_subparser(
        action_subparsers,
        "screenshots",
        help="List the screenshots for an app.",
    )
    screenshots_group = screenshots_parser.add_argument_group(
        title="Screenshots",
    )
    add_verbosity_arguments(screenshots_group)
    screenshots_group.add_argument(
        "--version-limit",
        type=arg_type_positive_int,
        default=1,
        help="Limit the number of app versions displayed.",
    )
    add_version_filters_group(screenshots_parser)
    add_authentication_group(screenshots_parser)
    add_app_id_group(screenshots_parser)

    # Action: previews
    previews_parser = add_subparser(
        action_subparsers,
        "previews",
        help="List the previews for an app.",
    )
    previews_group = previews_parser.add_argument_group(
        title="Previews",
    )
    add_verbosity_arguments(previews_group)
    previews_group.add_argument(
        "--version-limit",
        type=arg_type_positive_int,
        default=1,
        help="Limit the number of app versions displayed.",
    )
    add_version_filters_group(previews_parser)
    add_authentication_group(previews_parser)
    add_app_id_group(previews_parser)

    # Action: categories
    categories_parser = add_subparser(
        action_subparsers,
        "categories",
        help="List the appstore's heirarchy of categories and subcategories.",
    )
    categories_group = categories_parser.add_argument_group(
        title="Categories",
    )
    add_platform_filter_argument(categories_group)
    add_verbosity_arguments(categories_group)
    add_authentication_group(categories_parser)

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
    add_platform_argument(download_group)
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
    add_platform_argument(publish_group)
    publish_group.add_argument(
        "--version-string",
        help="Update the version string in the app store version.",
    )
    publish_group.add_argument(
        "--created-version-string",
        default="NEW.APP.VERSION",
        help=f"If {clr_keyword('--version-string')} isn't specified, "
        + "use this as the version string when creating a new app store version.",
    )
    publish_group.add_argument(
        "--no-create-version",
        action="store_true",
        help="Prevent a new app version from being created when no versions are in an editable state.",
    )
    publish_group.add_argument(
        "--no-create-locale",
        action="store_true",
        help="Prevent new locales from being created.",
    )
    publish_group.add_argument(
        "--no-delete-locale",
        action="store_true",
        help="Prevent locales from being deleted.",
    )
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
        if args.action == "categories":
            console_actions.list_categories(args)
        if args.action == "apps":
            console_actions.list_apps(args)
        elif args.action == "infos":
            console_actions.list_infos(args)
        elif args.action == "versions":
            console_actions.list_versions(args)
        elif args.action == "screenshots":
            console_actions.list_screenshots(args)
        elif args.action == "previews":
            console_actions.list_previews(args)
        elif args.action == "download":
            console_actions.download(args)
        elif args.action == "publish":
            console_actions.publish(args)
    except requests.exceptions.SSLError as error:
        sys.exit(error)
    except requests.exceptions.ConnectionError as error:
        sys.exit(error)
    except requests.exceptions.HTTPError as error:
        sys.exit(error)
    except appstore.ResourceNotFoundException as error:
        sys.exit(error)
    except FileExistsError as error:
        sys.exit(error)
    except KeyboardInterrupt as error:
        sys.exit(error)
