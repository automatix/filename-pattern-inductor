#!/usr/bin/env python3
"""Write one content-read batch result for filename-pattern-inductor.

A subagent that summarized a batch of files pipes its JSONL (one JSON object
per line, one line per file) to this script instead of writing the file
itself. The script resolves the results directory through `paths.py` -- so a
Git Bash (`/c/...`) or WSL (`/mnt/c/...`) spelling lands on the drive it
names -- requires it to be absolute, validates every line and writes
`<results-dir>/r<NNN>.jsonl`. It never overwrites an existing batch file.

Usage:
    python write_batch_result.py --results-dir "C:/.../results" --batch 7 < batch.jsonl

Prints only the written path to stdout; diagnostics go to stderr.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from paths import path_arg


def validate_jsonl(text: str) -> list[str]:
    """Return the non-blank lines of `text`, each checked to be a JSON object with a "path"."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("no JSONL lines on input")
    for number, line in enumerate(lines, start=1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {number} is not valid JSON: {exc}") from exc
        if not isinstance(record, dict) or "path" not in record:
            raise ValueError(f"line {number} is not a JSON object with a 'path' key")
    return lines


def write_batch_result(results_dir: Path, batch: int, text: str) -> Path:
    if not results_dir.is_absolute():
        raise ValueError(f"--results-dir must be absolute, got {str(results_dir)!r}")
    if batch < 1:
        raise ValueError(f"--batch must be 1 or higher, got {batch}")
    lines = validate_jsonl(text)
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / f"r{batch:03d}.jsonl"
    with out_path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results-dir", required=True, type=path_arg)
    parser.add_argument("--batch", required=True, type=int)
    args = parser.parse_args()

    text = sys.stdin.buffer.read().decode("utf-8-sig")
    try:
        out_path = write_batch_result(args.results_dir, args.batch, text)
    except FileExistsError as exc:
        print(f"error: batch file already exists: {exc.filename}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
