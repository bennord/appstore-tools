import configargparse
import logging


def parse_command_line():
    parser = configargparse.ArgParser(default_config_files=["run.config"])

    # Optional args
    parser.add_argument(
        "-c", "--config-file", is_config_file=True, help="Config filepath."
    )
    parser.add_argument(
        "--log-level",
        choices=logging._levelToName.values(),
        default=logging.getLevelName(logging.WARNING),
        help="Set the logging level.",
    )

    # Authentication
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

    # App ID
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

    # Parse
    args = parser.parse_args()

    logging.getLogger().setLevel(args.log_level)

    if args.key == None:
        args.key = args.key_file.read()
        args.key_file.close()

    return args
