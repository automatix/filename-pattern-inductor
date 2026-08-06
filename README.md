# Filename Pattern Inductor

A Claude Code Skill that reverse-engineers a filename/placement rule-set from an
existing, already-organized collection of files. Point it at one or more folders and
it induces "content like *this* tends to end up named/placed like *that*" — a
two-tier rule-set (a handful of abstract conventions, plus many concrete
per-recurring-case rules) meant to feed a separate skill that suggests names/locations
for *new* files based on their content.

## Usage

```
/filename-pattern-inductor <directory-or-list-file> [--output <path>]
```

| Invocation | Effect |
|---|---|
| `/filename-pattern-inductor D:\Accounting\Invoices` | Scans that one directory recursively. |
| `/filename-pattern-inductor D:\scan-roots.txt` | `scan-roots.txt` lists one directory per line (`#`-comments allowed) — the only reliable way to scan several folders at once, since folder paths can contain spaces. |
| `/filename-pattern-inductor D:\Accounting\Invoices --output D:\rules\invoice-rules.md` | Saves to that path instead of the default. Re-running against the same `--output` path accumulates versions (`_v01`, `_v02`, …) in an `archive\` subfolder next to it. |

If the total file count is large, the skill asks for confirmation (over `200` files)
or declines as out of scope (over `5000` files) before reading any content.

## Output format

Two separate Markdown tables, `IF` / `THEN target path` / `THEN target filename`
(intentionally no `confidence` column) — printed in the chat response and saved to a
result file:

```
## Abstract rules

| IF | THEN target path | THEN target filename |
|---|---|---|
| ... | ... | ... |

## Concrete / case-based rules

| IF | THEN target path | THEN target filename |
|---|---|---|
| ... | ... | ... |
```

`THEN target path` / `THEN target filename` are templates with placeholder tokens
(e.g. `<Vendor>`, `<YYYY-MM-DD>`), not literal paths copied from the scanned folders —
the point is a reusable pattern, not a transcript of what was found.

## Default output path and versioning

With no `--output`, the result is saved to the **session's current working
directory** as `<YYYYMMDD-hhmmss>_filename naming rules_v01.md`. Because that name
embeds a fresh timestamp every run, its version suffix will almost always be `_v01` —
the archive/version machinery (`scripts/save_versioned_result.py`) only meaningfully
accumulates versions when `--output` names a **stable** path across repeated runs,
which is the realistic "keep the rule-set current" workflow. This is expected, not a
bug.

The versioning convention itself (archive the old copy under `archive\`, add a
version suffix if it didn't have one, write the new copy one version higher) mirrors
the one already used by the `healthdb-coverage` skill.

## How it works (briefly)

1. Resolves the input into one or more absolute scan-root directories.
2. Enumerates every file recursively (excluding `.git`, `node_modules`, and similar
   generated/vendored directories) and applies the size guardrails above.
3. Reads content for each remaining file, batching large sets out to parallel
   subagents so only compact per-file summaries come back to the main context.
4. Correlates filename, folder location, and content to induce abstract and
   concrete/case-based rules (a concrete rule needs at least `2` consistent example
   files before it's promoted — a single example is noise, not a rule).
5. Renders the two tables, prints them, and saves them via
   `scripts/save_versioned_result.py`.

See `SKILL.md` for the full procedure.

## Installation

This skill needs local filesystem access (to scan arbitrary folders) and to run a
bundled Python script — it only works where Claude Code has that access.

| Surface | Skill location | Works? |
|---|---|---|
| **Claude Code (CLI)** | `~\.claude\skills\filename-pattern-inductor\` | **Yes** |
| **Desktop app "Code"** | shares `~\.claude\skills\` | **Yes** — it's Claude Code under the hood |
| **Desktop app Chat (GUI)** | Settings → Capabilities → Skills (as a ZIP) | **No** — sandboxed, no access to your local filesystem |
| **Cowork** | same Capabilities/Skills mechanism | **No** — cloud sandbox, can't reach arbitrary local folders |

**To install for Claude Code:** copy or symlink this repository to
`C:\Users\<user>\.claude\skills\filename-pattern-inductor\` (personal/global —
available in every project). A project-local install would instead go to
`<project>\.claude\skills\filename-pattern-inductor\`.

> **Restart note:** if `~\.claude\skills\` didn't exist yet, Claude Code only picks up
> the new skill after a restart (or a new session). Later edits to an already-detected
> `SKILL.md` take effect immediately.

## Requirements

- `python` on `PATH` (stdlib only — `scripts/save_versioned_result.py` has no
  dependencies to install).

## Testing

```
python -m pytest scripts/test_save_versioned_result.py -v
```

## Files

- `SKILL.md` — the agent-facing instructions (input resolution, guardrails,
  procedure, output format, example rules).
- `scripts/save_versioned_result.py` — deterministic archive+version+write helper.
- `scripts/test_save_versioned_result.py` — its test suite.
- `README.md` — this document.
