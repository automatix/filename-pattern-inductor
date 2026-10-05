"""The front matter must yield the invocation the documentation promises."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMAND = "induct-names"


def _front_matter():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, "SKILL.md has no front matter"
    return match.group(1)


def test_name_is_the_documented_command():
    assert re.search(rf"^name: {COMMAND}$", _front_matter(), re.MULTILINE)
    assert f"/{COMMAND}" in (ROOT / "README.md").read_text(encoding="utf-8")


def test_description_present():
    assert re.search(r"^description: \S", _front_matter(), re.MULTILINE)


def test_no_positional_argument_substitution():
    # `arguments:` would substitute named placeholders with shell-split tokens,
    # breaking paths with spaces and the one-directory-per-line input.
    assert not re.search(r"^arguments:", _front_matter(), re.MULTILINE)
