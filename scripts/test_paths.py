"""Tests for paths.py: POSIX drive notations never land on the current drive."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path, PureWindowsPath
from tempfile import TemporaryDirectory

from paths import DriveRelativePathError, normalize_path, to_windows_path

SCRIPTS_DIR = Path(__file__).resolve().parent


def _git_bash_form(path: Path) -> str:
    """`C:\\x\\y` -> `/c/x/y`, the spelling Git Bash hands to native programs."""
    win = PureWindowsPath(path)
    return "/" + win.drive[0].lower() + "/" + "/".join(win.parts[1:])


def _wsl_form(path: Path) -> str:
    return "/mnt" + _git_bash_form(path)


class TestToWindowsPath(unittest.TestCase):
    def test_git_bash_drive_notation(self) -> None:
        self.assertEqual(to_windows_path("/c/Users/demo/scratch"), PureWindowsPath(r"C:\Users\demo\scratch"))

    def test_wsl_drive_notation(self) -> None:
        self.assertEqual(to_windows_path("/mnt/d/data/results"), PureWindowsPath(r"D:\data\results"))

    def test_cygwin_drive_notation(self) -> None:
        self.assertEqual(to_windows_path("/cygdrive/e/x"), PureWindowsPath(r"E:\x"))

    def test_bare_drive_notation(self) -> None:
        self.assertEqual(to_windows_path("/c"), PureWindowsPath("C:\\"))

    def test_windows_paths_unchanged(self) -> None:
        for raw in (r"C:\Users\demo", "C:/Users/demo", r"\\server\share\dir"):
            self.assertEqual(to_windows_path(raw), PureWindowsPath(raw))

    def test_relative_paths_unchanged(self) -> None:
        self.assertEqual(to_windows_path(r"sub\report.md"), PureWindowsPath(r"sub\report.md"))

    def test_rooted_path_without_drive_rejected(self) -> None:
        for raw in (r"\c\Users\demo", r"\mnt\c\Users", "/home/demo/results", "/tmp"):
            with self.subTest(raw=raw), self.assertRaises(DriveRelativePathError):
                to_windows_path(raw)


@unittest.skipUnless(os.name == "nt", "drive-relative resolution only exists on Windows")
class TestNoDirectoryOnCurrentDrive(unittest.TestCase):
    """The incident: a POSIX path created `<current drive>:\\c\\...` / `\\mnt\\c\\...`."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name).resolve()
        self.drive_root = Path(Path.cwd().drive + "\\")
        self.stray = [self.drive_root / "c", self.drive_root / "mnt"]
        self.stray_before = {p: p.exists() for p in self.stray}

    def tearDown(self) -> None:
        for path, existed in self.stray_before.items():
            self.assertEqual(path.exists(), existed, f"stray directory appeared: {path}")

    def test_normalize_path_maps_both_notations_to_real_dir(self) -> None:
        self.assertEqual(normalize_path(_git_bash_form(self.dir)), self.dir)
        self.assertEqual(normalize_path(_wsl_form(self.dir)), self.dir)

    def test_save_cli_with_git_bash_target_writes_to_named_drive(self) -> None:
        content = self.dir / "content.md"
        content.write_text("synthetic", encoding="utf-8")
        target = _git_bash_form(self.dir / "results" / "report.md")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "save_versioned_result.py"),
             "--target", target, "--content-file", _wsl_form(content)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(Path(proc.stdout.strip()), self.dir / "results" / "report_v01.md")

    def test_save_cli_rejects_drive_relative_target(self) -> None:
        content = self.dir / "content.md"
        content.write_text("synthetic", encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "save_versioned_result.py"),
             "--target", r"\c\synthetic-fpi-test\report.md", "--content-file", str(content)],
            capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("no drive letter", proc.stderr)

    def test_save_function_rejects_drive_relative_target(self) -> None:
        from save_versioned_result import save_versioned_result

        with self.assertRaises(DriveRelativePathError):
            save_versioned_result(Path(r"\mnt\c\synthetic-fpi-test\report.md"), "synthetic")


if __name__ == "__main__":
    unittest.main()
