# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A Claude Code Skill (`filename-pattern-inductor`, invoked as `/induct-names`) that reverse-engineers a filename/
placement rule-set from an existing, already-organized collection of files — it feeds
a *different* skill (developed elsewhere) that suggests names/locations for *new*
files based on their content. The repository root **is** the installable skill
package: `SKILL.md` at the root, helper code under `scripts/`. There is no build step
— installing it means copying or symlinking this whole folder to
`~\.claude\skills\induct-names\`.

See `README.md` for usage and `SKILL.md` for the full agent-facing procedure — this
file only covers what a future Claude instance needs to work on the repo itself.

## Commands

Run the test suite:

```
python -m pytest scripts tests -v
```

Requires `python` on `PATH`. No other dependencies, no lint config, no build step —
mirrors the sibling `Claude Mover` tool project's minimal footprint rather than a full
packaged app.

## Architecture

Two very different kinds of "logic" live here, deliberately kept separate:

- **`SKILL.md`** is the actual deliverable: prose instructions for whichever Claude
  instance runs the skill at invocation time (resolving input directories, applying
  scan-size guardrails, batching content reads out to subagents, inducing the
  two-tier abstract/concrete rule-set, rendering the two output tables). This part is
  inherently LLM judgment — clustering files by name/location/content correlation
  isn't something to script, so don't try to replace it with deterministic code.
- **`scripts/save_versioned_result.py`** is the one piece of genuinely deterministic
  logic: given a target path, it archives any existing live file(s) matching that
  base name under `archive\` (adding a version suffix if one didn't already have
  one) and writes the new content one version higher — the same manual
  archive-and-version convention already established in the user's `healthdb-coverage`
  personal skill. `SKILL.md` always calls this script for the save step rather than
  reimplementing the version arithmetic inline. Its test suite
  (`scripts/test_save_versioned_result.py`) is the thing to run after touching it —
  the versioning edge cases (unsuffixed vs. suffixed live files, a version deleted
  without archiving, values past `99`, case-insensitive matches on Windows) are easy
  to get subtly wrong without them.

## Versioning and releases

The skill version stands in four places that must agree: `VERSION.md`, the `SKILL.md`
heading (`# Filename Pattern Inductor (vX.Y.Z)`), the end of the `SKILL.md` front-matter
`description` (`... Version vX.Y.Z.`) and the line under the `README.md` title.
`tests/test_version_consistency.py` enforces this. Each run names the version twice: in the
briefing (`references/briefing.md`) and in the closing report. Releases are git tags (`vX.Y.Z`)
plus a GitHub Release; no build artifact. Changes land on a feature branch and merge to
`master`; commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`,
`chore:`).
