#!/usr/bin/env python3
"""Path normalization shared by the filename-pattern-inductor scripts.

A path handed to these scripts may have been written in another shell's
notation: Git Bash spells `C:\\Users` as `/c/Users`, WSL as `/mnt/c/Users`.
Native Windows Python reads both as *drive-relative* paths (`\\c\\Users`),
silently resolved against whatever drive is current -- a run started on `D:`
then creates `D:\\c\\Users\\...`. This module maps both notations back to the
drive they name and rejects any remaining rooted path without a drive, so no
file or directory is ever created on the wrong drive.

On non-Windows platforms paths pass through unchanged.

Usage:
    python paths.py <path>    prints the normalized path, or an error
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path, PureWindowsPath

# `/mnt/c` or `/mnt/c/...` (WSL) and `/c` or `/c/...` (Git Bash / MSYS / Cygwin `/cygdrive/c`).
_POSIX_DRIVE_RE = re.compile(r"^/(?:mnt/|cygdrive/)?([a-zA-Z])(?=/|$)(.*)$", re.DOTALL)


class DriveRelativePathError(ValueError):
    """A rooted path without a drive letter, which Windows resolves against the current drive."""


def to_windows_path(raw: str) -> PureWindowsPath:
    """Return `raw` as a Windows path, mapping POSIX drive notations to their drive.

    Relative paths stay relative. Raises DriveRelativePathError for a rooted
    path without a drive (`\\foo`, `/foo/bar`) that is not a drive notation.
    """
    match = _POSIX_DRIVE_RE.match(raw)
    if match:
        drive, rest = match.groups()
        raw = f"{drive.upper()}:\\{rest.lstrip('/')}"
    path = PureWindowsPath(raw)
    if path.root and not path.drive:
        raise DriveRelativePathError(
            f"path has no drive letter and would resolve against the current drive: {raw!r}; "
            "pass an absolute path such as 'C:/Users/...'"
        )
    return path


def normalize_path(raw: str | os.PathLike[str]) -> Path:
    """Return `raw` as a native Path, applying `to_windows_path` on Windows."""
    raw = os.fspath(raw)
    if os.name == "nt":
        return Path(to_windows_path(raw))
    return Path(raw)


def path_arg(raw: str) -> Path:
    """argparse `type=` adapter: normalize, or fail with the reason as the CLI error."""
    try:
        return normalize_path(raw)
    except DriveRelativePathError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", type=path_arg)
    args = parser.parse_args()
    print(args.path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
