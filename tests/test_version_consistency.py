"""Every place that declares the skill version must carry the same one."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_RE = r"v\d+\.\d+\.\d+"


def _read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def _version_file():
    match = re.search(rf"^({VERSION_RE})$", _read("VERSION.md"), re.MULTILINE)
    assert match, "VERSION.md has no line holding just vX.Y.Z"
    return match.group(1)


def test_skill_heading_matches_version_file():
    match = re.search(rf"^# Filename Pattern Inductor \(({VERSION_RE})\)$", _read("SKILL.md"), re.MULTILINE)
    assert match, "SKILL.md heading lacks '(vX.Y.Z)'"
    assert match.group(1) == _version_file()


def test_skill_description_ends_with_version():
    match = re.search(r"^description: (.*)$", _read("SKILL.md"), re.MULTILINE)
    assert match, "SKILL.md front matter has no description"
    assert match.group(1).rstrip().endswith(f"Version {_version_file()}.")


def test_readme_names_version_under_title():
    lines = [line for line in _read("README.md").splitlines() if line.strip()]
    assert lines[0] == "# Filename Pattern Inductor"
    assert lines[1].startswith(f"Version {_version_file()}.")


def test_briefing_exists_and_skill_references_it():
    assert (ROOT / "references" / "briefing.md").is_file()
    assert "references/briefing.md" in _read("SKILL.md")
