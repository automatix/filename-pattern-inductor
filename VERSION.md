# Version

v0.2.0

The same version stands in the heading of `SKILL.md`, at the end of its front-matter
`description`, and under the title of `README.md`. `tests/test_version_consistency.py` fails
unless all four agree.

The running skill reads its version from the heading of `SKILL.md`; this file serves a reader of
the repository and any tool that needs it machine-readable.
