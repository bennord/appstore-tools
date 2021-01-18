import modules.appstore as appstore
import modules.command_line as command_line
import modules.actions as actions
import sys
import os


def get_access_token(args):
    try:
        access_token = appstore.create_access_token(
            issuer_id=args.issuer_id, key_id=args.key_id, key=args.key
        )
        return access_token
    except ValueError as error:
        sys.exit(error)


def get_app_id(args, access_token):
    if args.app_id == None:
        args.app_id = appstore.get_app_id(
            bundle_id=args.bundle_id, access_token=access_token
        )
    return args.app_id


def get_bundle_id(args, access_token):
    if args.bundle_id == None:
        args.bundle_id = appstore.get_bundle_id(
            app_id=args.app_id, access_token=access_token
        )
    return args.bundle_id


def list_apps(args):
    access_token = get_access_token(args)
    actions.list_apps(access_token=access_token)


def list_versions(args):
    access_token = get_access_token(args)
    app_id = get_app_id(args, access_token)
    platforms = command_line.create_platform_filter_list(args)
    states = command_line.create_version_state_filter_list(args)
    verbosity = args.verbosity

    actions.list_versions(
        access_token=access_token,
        app_id=app_id,
        platforms=platforms,
        states=states,
        verbosity=verbosity,
    )


def list_infos(args):
    access_token = get_access_token(args)
    app_id = get_app_id(args, access_token)
    states = command_line.create_version_state_filter_list(args)
    verbosity = args.verbosity

    actions.list_infos(
        access_token=access_token, app_id=app_id, states=states, verbosity=verbosity
    )


def list_screenshots(args):
    access_token = get_access_token(args)
    app_id = get_app_id(args, access_token)
    platforms = command_line.create_platform_filter_list(args)
    states = command_line.create_version_state_filter_list(args)
    verbosity = args.verbosity

    actions.list_screenshots(
        access_token=access_token,
        app_id=app_id,
        platforms=platforms,
        states=states,
        version_limit=args.version_limit,
        verbosity=verbosity,
    )


def list_previews(args):
    access_token = get_access_token(args)
    app_id = get_app_id(args, access_token)
    platforms = command_line.create_platform_filter_list(args)
    states = command_line.create_version_state_filter_list(args)

    actions.list_previews(
        access_token=access_token,
        app_id=app_id,
        platforms=platforms,
        states=states,
        version_limit=args.version_limit,
    )


def download_assets(args):
    access_token = get_access_token(args)
    app_id = get_app_id(args, access_token)
    bundle_id = get_bundle_id(args, access_token)
    asset_dir = args.asset_dir
    platforms = [args.platform]
    version_states = (
        [args.version_state]
        if args.version_state is not None
        else list(appstore.VersionState)
    )
    overwrite = args.overwrite

    actions.download_assets(
        access_token=access_token,
        asset_dir=asset_dir,
        app_id=app_id,
        bundle_id=bundle_id,
        platforms=platforms,
        version_states=version_states,
        overwrite=overwrite,
    )


def publish_assets(args):
    access_token = get_access_token(args)
    app_id = get_app_id(args, access_token)
    bundle_id = get_bundle_id(args, access_token)
    asset_dir = args.asset_dir
    platform = args.platform
    version_string = args.version_string

    actions.publish_assets(
        access_token=access_token,
        asset_dir=asset_dir,
        app_id=app_id,
        bundle_id=bundle_id,
        platform=platform,
        version_string=version_string,
    )