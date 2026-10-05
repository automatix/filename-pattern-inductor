---
name: filename-pattern-inductor
description: Recursively scans one or more directories, correlates each file's name, location, and content, and induces a two-tier filename/placement rule-set (abstract general conventions plus concrete per-recurring-case rules) as two Markdown tables — printed in chat and saved to a versioned result file. Invoke as /filename-pattern-inductor <directory-or-list-file> [--output <path>].
argument-hint: [directory-or-list-file] [--output <path>?]
arguments: [input]
disable-model-invocation: true
allowed-tools: Read, Write, Glob, Bash, PowerShell
---

# Filename Pattern Inductor (`filename-pattern-inductor`)

Reverse-engineers a filename/placement rule-set from an existing, already-organized
collection of files: point it at one or more folders and it infers "content like
*this* tends to end up named/placed like *that*." The output is a two-tier rule-set —
a handful of abstract conventions plus many concrete per-recurring-case rules — meant
to feed a *different* skill that suggests names/locations for *new* files.

## Setup (once per machine)

Requires `python` on `PATH` (stdlib only — nothing to install).

## Arguments

`$ARGUMENTS` holds the raw invocation text. If it contains `--output`, split there:
everything before it is the input spec (`$input`), everything after it is the output
path override (trim surrounding whitespace/quotes; expand a leading `~`). If
`--output` is absent, the entire `$ARGUMENTS` string is `$input`.

## Input: `$input`

Trim `$input` of surrounding quotes/whitespace, then resolve it into a list of
absolute scan-root directories:

- **Names an existing directory** → that is the one scan root.
- **Names an existing file** → read it as UTF-8 text; each non-empty line that
  doesn't start with `#` is one directory path (trim whitespace, expand a leading
  `~`). These are the scan roots. This is the only reliable way to pass *multiple*
  directories — Windows paths routinely contain spaces (this very repo's own path is
  a live example), so they can't be safely space-separated inline.
- **Names neither** (typo, a relative path that doesn't resolve from the session's
  cwd, etc.) → do not guess. State what you tried to resolve and ask the user for the
  correct path(s).

Resolve every scan root to an absolute path. If one scan root is a subdirectory of
another, keep only the outermost and say so.

## Guardrails (before reading any file content)

1. Enumerate every file under each scan root recursively (`Glob` — files only,
   directories excluded from the result). Exclude `.git`, `node_modules`,
   `__pycache__`, `.venv`, `venv`, `dist`, `build`, and other conventionally
   generated/vendored directories — unless a scan root points *directly inside* one
   of these (the user explicitly asked for it).
2. If the total file count exceeds **200**, report the count (overall and per scan
   root) and ask the user whether to proceed, narrow the input, or cap it. Do not
   read content until they answer. There is no upper limit: if the user confirms,
   process the full set, however large it is — never refuse or silently reduce it.
3. For each remaining file, skip content reads — classify by name/extension/location
   only — for common binary/media extensions (images, audio, video, archives,
   executables, fonts) and for anything above roughly 2 MB. Note in the final output
   which files were classified this way, since those rows rest on weaker evidence.

## Procedure

1. Resolve `$input` and the guardrails above.
2. Read content for every remaining file (the `Read` tool's own handling of PDFs,
   notebooks, and large text files is fine — don't fight it). If there are more than
   ~40 such files, batch them (~20–40 per batch) and delegate each batch to a
   parallel subagent (this session's Task/Agent-style subagent-dispatch tool, if
   available — otherwise fall back to reading them yourself in batches), instructing
   each to return a compact structured summary per file: relative path, extension, a
   short one-line content gist, and any recognizable entities (dates, vendor/sender
   name, document type, invoice/reference numbers, category). Never have a subagent
   return full raw file content back to you. **Do not use the `Workflow` tool** for
   this — it requires the end user's own explicit per-session opt-in and must never
   be invoked automatically from inside a skill.
3. Using filename, folder location, and content summary *together* — the correlation
   between them is the actual signal, not any one alone — group files into recurring
   patterns:
   - **Abstract rules**: a small number (aim for 3–8) of overarching conventions most
     or all files share to some degree — e.g. a date-prefix format, a language, a
     casing style, a top-level category-folder scheme.
   - **Concrete/case-based rules**: one row per distinct, recurring content "case" (a
     specific type/category/source of file). Promote a pattern to a concrete rule
     only once you have **at least 2** consistent example files following it — a
     single example is noise, not a rule.
   - Write `THEN target path` and `THEN target filename` as **templates using
     placeholder tokens** (e.g. `<Vendor>`, `<YYYY-MM-DD>`, `<InvoiceNumber>`,
     `<Category>`), not literal paths copied from one scan root — the goal is a
     reusable pattern a downstream skill can apply to *new* files, not a transcript
     of what you found. State this convention once in the output preamble rather
     than repeating it per row.
4. Render exactly two Markdown tables, each with columns `IF`, `THEN target path`,
   `THEN target filename` (no other columns — see "Output format" below). Precede
   them with a short preamble: scan roots used, total files found, how many were read
   for content vs. classified by name/extension only, and a one-line reminder that
   target paths/filenames are templates. Print all of this in the chat response.
5. Resolve the result file target:
   - `--output <path>` given, and `<path>` resolves to an existing directory → target
     is `<path>\<default filename>` (below).
   - `--output <path>` given, and `<path>` does not resolve to an existing directory
     → `<path>` itself is the full target file path (append `.md` if it has none).
   - No `--output` → target is
     `<session-cwd>\<YYYYMMDD-hhmmss>_filename naming rules_v01.md` (capture the
     timestamp once, at the start of this step, in local `YYYYMMDD-hhmmss` format).

   Because the default filename embeds a fresh timestamp every run, its `_vNN` will
   almost always resolve to `_v01` — the archiving/versioning machinery below only
   meaningfully accumulates versions when `--output` names a **stable** path across
   repeated runs (the realistic "keep the rule-set current" workflow). This is
   expected, not a bug — say so if the user seems to expect otherwise.
6. Write the rendered preamble + two tables to a temporary file in the OS temp
   directory (never inside a scanned directory — this skill runs against arbitrary
   folders once installed and cannot assume write access or a scratch convention
   there).
7. Run:
   ```
   python "${CLAUDE_SKILL_DIR}/scripts/save_versioned_result.py" --target "<resolved target path>" --content-file "<temp file path>"
   ```
   This archives any prior version of that exact target and writes the new one; it
   prints the final saved path to stdout — read that back rather than re-deriving it
   yourself.
8. Report back to the user: the final saved path, and the preamble summary (scan
   roots, file counts). The two tables were already shown in step 4 — no need to
   repeat them in full again, just confirm they were saved.

## Output format

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

No `confidence` column and no merged single table — always these two separate
sections, in this order.

## Example rules (illustrates expected granularity — not literal output)

### Abstract rules

| IF | THEN target path | THEN target filename |
|---|---|---|
| Any file whose content names a clear category and date | `<Category>/<YYYY>/` | `<YYYY-MM-DD>_<short-description>.<ext>` |
| Filename already contains a recognizable reference/invoice number | (same target path convention as the matching concrete rule) | append `_<ReferenceNumber>` before the extension |

### Concrete / case-based rules

| IF | THEN target path | THEN target filename |
|---|---|---|
| PDF content mentions a specific recurring vendor plus an invoice number (3 matching files) | `finance/invoices/<Vendor>/<YYYY>/` | `<Vendor>_Invoice_<InvoiceNumber>.pdf` |
| Markdown file is meeting notes (has a date heading and attendee list) (4 matching files) | `notes/meetings/` | `<YYYY-MM-DD>_<topic-slug>.md` |

## Files

- `SKILL.md` — this file.
- `scripts/save_versioned_result.py` — deterministic archive+version+write helper;
  see its own docstring for the algorithm. Do not replicate its logic by hand in
  step 7 above — always call it.
- `scripts/test_save_versioned_result.py` — its test suite.
- `README.md` — human-facing usage guide + installation notes.
