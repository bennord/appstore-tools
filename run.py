import colorama
import modules.command_line as command_line
import modules.actions as actions
import logging

colorama.init()

args = command_line.parse_command_line()

logging.getLogger().setLevel(args.log_level)

if args.action == "apps":
    actions.list_apps(args)
elif args.action == "versions":
    actions.list_versions(args)
elif args.action == "screenshots":
    actions.list_screenshots(args)
