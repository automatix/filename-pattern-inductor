"""Unit and CLI-level tests for save_versioned_result.py."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from save_versioned_result import parse_target, save_versioned_result

SCRIPT_PATH = Path(__file__).resolve().parent / "save_versioned_result.py"


class TempDirCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)


class TestSaveVersionedResult(TempDirCase):
    def test_empty_target_dir_first_run(self) -> None:
        out = save_versioned_result(self.dir / "sub" / "report.md", "hello")
        self.assertEqual(out, self.dir / "sub" / "report_v01.md")
        self.assertEqual(out.read_text(encoding="utf-8"), "hello")
        self.assertFalse((self.dir / "sub" / "archive").exists())

    def test_live_unsuffixed_promoted_and_versioned(self) -> None:
        (self.dir / "report.md").write_text("old", encoding="utf-8")
        out = save_versioned_result(self.dir / "report.md", "new")
        self.assertEqual(out, self.dir / "report_v02.md")
        self.assertEqual(out.read_text(encoding="utf-8"), "new")
        archived = self.dir / "archive" / "report_v01.md"
        self.assertTrue(archived.exists())
        self.assertEqual(archived.read_text(encoding="utf-8"), "old")
        self.assertFalse((self.dir / "report.md").exists())

    def test_live_suffixed_moved_as_is(self) -> None:
        (self.dir / "report_v02.md").write_text("v2", encoding="utf-8")
        out = save_versioned_result(self.dir / "report.md", "v3")
        self.assertEqual(out, self.dir / "report_v03.md")
        archived = self.dir / "archive" / "report_v02.md"
        self.assertTrue(archived.exists())
        self.assertEqual(archived.read_text(encoding="utf-8"), "v2")

    def test_archive_only_no_live_file(self) -> None:
        archive = self.dir / "archive"
        archive.mkdir()
        (archive / "report_v01.md").write_text("v1", encoding="utf-8")
        (archive / "report_v02.md").write_text("v2", encoding="utf-8")
        out = save_versioned_result(self.dir / "report.md", "v3")
        self.assertEqual(out, self.dir / "report_v03.md")

    def test_both_unsuffixed_and_suffixed_live_at_once(self) -> None:
        (self.dir / "report.md").write_text("unsuffixed", encoding="utf-8")
        (self.dir / "report_v01.md").write_text("suffixed", encoding="utf-8")
        out = save_versioned_result(self.dir / "report.md", "new")
        # unsuffixed promoted to v2, suffixed v01 moved unchanged, new write is v3
        self.assertEqual(out, self.dir / "report_v03.md")
        self.assertTrue((self.dir / "archive" / "report_v01.md").exists())
        self.assertTrue((self.dir / "archive" / "report_v02.md").exists())
        self.assertFalse((self.dir / "report.md").exists())
        self.assertFalse((self.dir / "report_v01.md").exists())

    def test_multiple_stray_live_suffixed_files(self) -> None:
        (self.dir / "report_v01.md").write_text("v1", encoding="utf-8")
        (self.dir / "report_v02.md").write_text("v2", encoding="utf-8")
        out = save_versioned_result(self.dir / "report.md", "new")
        self.assertEqual(out, self.dir / "report_v03.md")
        self.assertTrue((self.dir / "archive" / "report_v01.md").exists())
        self.assertTrue((self.dir / "archive" / "report_v02.md").exists())
        self.assertFalse((self.dir / "report_v01.md").exists())
        self.assertFalse((self.dir / "report_v02.md").exists())

    def test_version_beyond_99_not_truncated(self) -> None:
        (self.dir / "report_v99.md").write_text("v99", encoding="utf-8")
        out = save_versioned_result(self.dir / "report.md", "new")
        self.assertEqual(out.name, "report_v100.md")

    def test_case_insensitive_matching_stable_output_case(self) -> None:
        (self.dir / "Report_V02.MD").write_text("v2", encoding="utf-8")
        out = save_versioned_result(self.dir / "Report.md", "new")
        self.assertEqual(out, self.dir / "Report_v03.md")
        self.assertTrue((self.dir / "archive" / "Report_V02.MD").exists())

    def test_ignores_unrelated_similar_filenames(self) -> None:
        (self.dir / "report_foo.md").write_text("unrelated", encoding="utf-8")
        (self.dir / "report2_v01.md").write_text("unrelated2", encoding="utf-8")
        out = save_versioned_result(self.dir / "report.md", "new")
        self.assertEqual(out, self.dir / "report_v01.md")
        self.assertTrue((self.dir / "report_foo.md").exists())
        self.assertTrue((self.dir / "report2_v01.md").exists())
        self.assertFalse((self.dir / "archive").exists())

    def test_target_with_pre_suffixed_cli_arg_is_stripped(self) -> None:
        target_dir, base_name, ext = parse_target(self.dir / "report_v05.md")
        self.assertEqual(target_dir, self.dir)
        self.assertEqual(base_name, "report")
        self.assertEqual(ext, "md")

    def test_multi_dot_filename(self) -> None:
        target_dir, base_name, ext = parse_target(self.dir / "report v1.2.md")
        self.assertEqual(base_name, "report v1.2")
        self.assertEqual(ext, "md")

    def test_base_name_with_spaces(self) -> None:
        target = self.dir / "20260807-153000_filename naming rules.md"
        out = save_versioned_result(target, "content")
        self.assertEqual(out.name, "20260807-153000_filename naming rules_v01.md")
        out2 = save_versioned_result(target, "content2")
        self.assertEqual(out2.name, "20260807-153000_filename naming rules_v02.md")

    def test_utf8_content_roundtrip(self) -> None:
        content = "Rechnung über 12,34 € — Größe: klein\n| IF | ... |"
        out = save_versioned_result(self.dir / "report.md", content)
        self.assertEqual(out.read_text(encoding="utf-8"), content)

    def test_target_dir_auto_created(self) -> None:
        target = self.dir / "a" / "b" / "c" / "report.md"
        out = save_versioned_result(target, "content")
        self.assertTrue(out.exists())
        self.assertEqual(out.parent, self.dir / "a" / "b" / "c")


class TestCli(TempDirCase):
    def test_missing_content_file_errors_cleanly(self) -> None:
        target = self.dir / "report.md"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--target",
                str(target),
                "--content-file",
                str(self.dir / "does-not-exist.txt"),
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(target.exists())
        self.assertFalse((self.dir / "report_v01.md").exists())

    def test_stdout_is_exactly_the_written_path(self) -> None:
        content_file = self.dir / "content.md"
        content_file.write_text("hello", encoding="utf-8")
        target = self.dir / "report.md"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--target",
                str(target),
                "--content-file",
                str(content_file),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        expected = self.dir / "report_v01.md"
        self.assertEqual(result.stdout.strip(), str(expected))


if __name__ == "__main__":
    unittest.main()
