import os
import platform
import sysconfig
from pathlib import Path
from typing import Optional

import typer

from src.drive_handler import DriveHandler
from src.file_handler import FileHandler

__VERSION: Optional[str] = "1.5.1-alpha"
__APP_NAME: Optional[str] = "kodi-strm"

# Switch to flip all flags to be case in/sensitive
__CASE_SENSITIVE: bool = False


def __callback_version(fired: bool):
    """
    Callback function - fired when the `--version` flag is invoked. Check the value
    of `fired` to know if the user has actually used the flag
    """

    if not fired:
        return  # flag was not invoked

    typer.echo(
        f"{__APP_NAME} v{__VERSION}\n"
        + f"- os/kernel: {platform.release()}\n"
        + f"- os/type: {sysconfig.get_platform()}\n"
        + f"- os/machine: {platform.machine()}\n"
        + f"- os/arch: {platform.architecture()[0]}\n"
        + f"- python/version: {platform.python_version()}\n",
    )

    raise typer.Exit()  # direct exit


def __callback_destination(dst: str) -> Optional[str]:
    """
    Validates if the destination directory exists. Converts to absolute path
    """

    if dst is None:
        return dst
    elif not os.path.exists(dst):
        raise typer.BadParameter("invalid destination")

    return Path(dst).absolute()  # return absolute path


def cmd_interface(
    source: Optional[str] = typer.Option(
        None,
        "--source",
        show_default=False,
        case_sensitive=__CASE_SENSITIVE,
        help="Folder ID for source directory on Google Drive",
    ),
    destination: Optional[str] = typer.Option(
        None,
        "--dest",
        "--destination",
        case_sensitive=__CASE_SENSITIVE,
        callback=__callback_destination,
        help="Set a destination directory where strm files will be placed",
    ),
    root_name: Optional[str] = typer.Option(
        None,
        "--root",
        "--rootname",
        case_sensitive=__CASE_SENSITIVE,
        help="Set a custom name for the source directory",
    ),
    rem_extensions: bool = typer.Option(
        False,
        "--no-ext",
        "--no-extensions",
        show_default=False,
        case_sensitive=__CASE_SENSITIVE,
        help="Remove original extensions from generated strm files",
    ),
    updates: bool = typer.Option(
        True,
        show_default=False,
        case_sensitive=__CASE_SENSITIVE,
        help="Show progress during transfers",
    ),
    version: bool = typer.Option(
        None,
        "--version",
        is_eager=True,
        callback=__callback_version,
        case_sensitive=__CASE_SENSITIVE,
        help="Display current app version",
    ),
) -> None:
    drive_handler = DriveHandler()  # authenticate drive api

    # Replace destination directory with the current directory path if not supplied
    destination = destination if destination else os.getcwd()
    file_handler = FileHandler(
        destination=destination,
        include_extensions=not rem_extensions,
        live_updates=updates,
    )

    if not source or len(source) == 0:
        # No source directory is provided, get a list of all teamdrives
        drive_handler.get_teamdrives()
        source = drive_handler.select_teamdrive()  # force user to choose one of these
    else:
        # If directory ID is being used, fetch
        drive_handler.get_dir_details(dir_id=source)

    typer.secho(
        f"Walking  through `{drive_handler.drive_name(source)}`",
        err=True,
        fg=typer.colors.GREEN,
    )

    drive_handler.walk(
        source=source,
        change_dir=file_handler.switch_dir,
        generator=file_handler.strm_generator,
        orig_path=destination,
        custom_root=root_name,
    )


def main():
    typer.run(cmd_interface)
