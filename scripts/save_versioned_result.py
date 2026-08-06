#!/usr/bin/env python3
"""Archive-and-version helper for filename-pattern-inductor result files.

Reproduces this user's manual file-versioning convention (see the "File
versioning outside repositories" rule in their global CLAUDE.md, and the
prior art in ~/.claude/skills/healthdb-coverage/scripts/coverage_audit.py):

Given a target path "<dir>/<base_name>.<ext>", find any existing live file(s)
matching "<base_name>(_v<N>)?.<ext>" in <dir> (case-insensitive), move them
into <dir>/archive/ (assigning a fresh "_v<N>" suffix to one that didn't have
one yet), and write the new content to "<dir>/<base_name>_v<N+1>.<ext>",
where N is the highest version number found anywhere for this base name --
across both <dir> and <dir>/archive/. If a live file was deleted by hand
without being archived, its number is naturally reused rather than skipped,
since the next version is always "highest found on disk right now" + 1, not
a persistent counter.

Usage:
    python save_versioned_result.py --target "<dir>\\<base_name>.<ext>" --content-file <path>

Prints only the final written path to stdout; diagnostics go to stderr.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

VERSION_SUFFIX_RE = re.compile(r"_v(\d+)$", re.IGNORECASE)


def parse_target(target: Path) -> tuple[Path, str, str]:
    """Split a target path into (target_dir, base_name, ext).

    `ext` has no leading dot and is "" if `target` has no extension. A
    trailing "_v<digits>" on the stem is stripped defensively, in case the
    caller already included a version suffix.
    """
    target_dir = target.parent
    stem = target.stem
    ext = target.suffix[1:] if target.suffix else ""
    match = VERSION_SUFFIX_RE.search(stem)
    base_name = stem[: match.start()] if match else stem
    return target_dir, base_name, ext


def _versioned_name(base_name: str, ext: str, version: int) -> str:
    if ext:
        return f"{base_name}_v{version:02d}.{ext}"
    return f"{base_name}_v{version:02d}"


def _match_pattern(base_name: str, ext: str) -> re.Pattern[str]:
    escaped_base = re.escape(base_name)
    if ext:
        escaped_ext = re.escape(ext)
        return re.compile(rf"^{escaped_base}(?:_v(\d+))?\.{escaped_ext}$", re.IGNORECASE)
    return re.compile(rf"^{escaped_base}(?:_v(\d+))?$", re.IGNORECASE)


def _scan_dir(directory: Path, pattern: re.Pattern[str]) -> list[tuple[Path, int | None]]:
    if not directory.is_dir():
        return []
    matches = []
    for entry in directory.iterdir():
        if not entry.is_file():
            continue
        m = pattern.match(entry.name)
        if m:
            version = int(m.group(1)) if m.group(1) else None
            matches.append((entry, version))
    return matches


def save_versioned_result(target: Path, content: str) -> Path:
    target_dir, base_name, ext = parse_target(target)
    target_dir.mkdir(parents=True, exist_ok=True)
    archive_dir = target_dir / "archive"

    pattern = _match_pattern(base_name, ext)
    live_matches = _scan_dir(target_dir, pattern)
    archive_matches = _scan_dir(archive_dir, pattern)

    numbered = [v for _, v in live_matches + archive_matches if v is not None]
    highest = max(numbered) if numbered else 0

    live_unsuffixed = [p for p, v in live_matches if v is None]
    live_suffixed = [p for p, v in live_matches if v is not None]

    next_version = highest + 1

    # A previous version that existed but had no suffix yet gets promoted
    # into the archive with one, per the established manual convention.
    for path in live_unsuffixed:
        archive_dir.mkdir(exist_ok=True)
        shutil.move(str(path), str(archive_dir / _versioned_name(base_name, ext, next_version)))
        next_version += 1

    # Any already-suffixed live copies move into the archive unchanged --
    # covers the (rare) case of more than one stray live version at once.
    for path in live_suffixed:
        archive_dir.mkdir(exist_ok=True)
        shutil.move(str(path), str(archive_dir / path.name))

    out_path = target_dir / _versioned_name(base_name, ext, next_version)
    if out_path.exists():
        raise FileExistsError(f"refusing to overwrite unexpected existing file: {out_path}")
    out_path.write_text(content, encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--content-file", required=True, type=Path)
    args = parser.parse_args()

    try:
        content = args.content_file.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: could not read --content-file: {exc}", file=sys.stderr)
        return 1

    out_path = save_versioned_result(args.target, content)
    print(out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
