import configargparse
import argparse
import logging
import modules.actions as actions

DEFAULT_CONFIG_FILES = ["run.config"]


def add_subparser(subparsers: argparse._SubParsersAction, name: str, help: str):
    parser = subparsers.add_parser(
        name=name,
        help=help,
        default_config_files=DEFAULT_CONFIG_FILES,
    )
    parser.add_argument(
        "-c", "--config-file", is_config_file=True, help="Config filepath."
    )
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


def parse_command_line():
    global_parser = configargparse.ArgParser(
        default_config_files=DEFAULT_CONFIG_FILES,
    )

    # Global args
    global_parser.add_argument(
        "-c", "--config-file", is_config_file=True, help="Config filepath."
    )
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

    # Parse
    args = global_parser.parse_known_args()[0]  # tuple { matched_args, remaining_args }

    # Handle loading the auth key from file
    if "key" in args and "key_file" in args and args.key == None:
        args.key = args.key_file.read()
        args.key_file.close()

    return args
