"""Every shipped script answers --help without an error."""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = sorted(
    p for p in (Path(__file__).resolve().parent.parent / "scripts").glob("*.py") if not p.name.startswith("test_")
)


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_script_answers_help(script):
    proc = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
