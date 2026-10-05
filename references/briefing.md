# briefing

Shown at the start of every run, before the first question and without waiting for a reply.
Translate it; keep it this short and **keep the tables as tables**. Open with one line naming the
version: "Filename Pattern Inductor vX.Y.Z".

**Ceiling: `200` words**, counted from `## What this does` to the end of `## Limits`. Keyword style,
lists and tables over prose.

---

## What this does

Reads an already-organized file collection and derives the rules behind it: which content ends up
under which name and in which folder.

## How it works

| Step | What happens |
|---|---|
| 1. Scan | All files under the given folders, recursively. Over `200` files: confirmation first. |
| 2. Read | Content read in batches; binaries and files over ~`2 MB` by name only. |
| 3. Induce | Name, folder and content correlated into rules. |
| 4. Save | Tables shown and saved as a versioned file. |

## What is asked

| Input | Meaning |
|---|---|
| folders | One folder, several folders one per line, or a `.txt` file listing them. |
| `--output` | Optional. Result file or folder; default: current directory. |

## What comes out

Two tables (`IF` / `THEN target path` / `THEN target filename`): abstract rules and concrete
per-case rules. Saved as `<YYYYMMDD-hhmmss>_filename naming rules_v01.md`; a stable `--output`
path keeps older versions in `archive\`.

## Limits

- **Reads only, never moves or renames** anything in the scanned folders.
- **Large collections are slow and costly.** Start with one or two folders.
- **A concrete rule needs at least `2` matching files.**
