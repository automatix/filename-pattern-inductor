"""Tests for write_batch_result.py. All paths and records are synthetic."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path, PureWindowsPath
from tempfile import TemporaryDirectory

from write_batch_result import validate_jsonl, write_batch_result

SCRIPT_PATH = Path(__file__).resolve().parent / "write_batch_result.py"
RECORD = {"path": "Example/2025/Invoice 0001.pdf", "ext": "pdf", "gist": "synthetic invoice",
          "doctype": "invoice", "entities": {"vendor": "Example GmbH"}}
JSONL = json.dumps(RECORD) + "\n" + json.dumps({**RECORD, "path": "Example/2025/Invoice 0002.pdf"}) + "\n"


def _run(results_dir: str, batch: str, stdin: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--results-dir", results_dir, "--batch", batch],
        input=stdin.encode("utf-8"), capture_output=True, check=False,
    )


class TestWriteBatchResult(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name).resolve()

    def test_writes_numbered_file(self) -> None:
        out = write_batch_result(self.dir / "results", 4, JSONL)
        self.assertEqual(out, self.dir / "results" / "r004.jsonl")
        self.assertEqual(out.read_text(encoding="utf-8"), JSONL)

    def test_refuses_to_overwrite(self) -> None:
        write_batch_result(self.dir, 1, JSONL)
        with self.assertRaises(FileExistsError):
            write_batch_result(self.dir, 1, JSONL)

    def test_rejects_relative_results_dir(self) -> None:
        with self.assertRaises(ValueError):
            write_batch_result(Path("results"), 1, JSONL)

    def test_rejects_invalid_lines(self) -> None:
        for text in ("", "not json\n", "[1, 2]\n", '{"gist": "no path"}\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate_jsonl(text)

    def test_cli_writes_and_prints_path(self) -> None:
        proc = _run(str(self.dir / "results"), "12", JSONL)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(Path(proc.stdout.decode().strip()), self.dir / "results" / "r012.jsonl")

    def test_cli_rejects_relative_results_dir(self) -> None:
        proc = _run("results", "1", JSONL)
        self.assertNotEqual(proc.returncode, 0)

    @unittest.skipUnless(os.name == "nt", "drive notations only matter on Windows")
    def test_cli_git_bash_results_dir_lands_on_named_drive(self) -> None:
        win = PureWindowsPath(self.dir / "results")
        posix = "/" + win.drive[0].lower() + "/" + "/".join(win.parts[1:])
        stray = Path(Path.cwd().drive + "\\") / "c"
        stray_existed = stray.exists()
        proc = _run(posix, "1", JSONL)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((self.dir / "results" / "r001.jsonl").is_file())
        self.assertEqual(stray.exists(), stray_existed)

    @unittest.skipUnless(os.name == "nt", "drive-relative resolution only exists on Windows")
    def test_cli_rejects_drive_relative_results_dir(self) -> None:
        proc = _run(r"\mnt\c\synthetic-fpi-test\results", "1", JSONL)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn(b"no drive letter", proc.stderr)


if __name__ == "__main__":
    unittest.main()
