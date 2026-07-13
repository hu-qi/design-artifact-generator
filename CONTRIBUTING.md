# Contributing

Use a focused branch and keep changes scoped to a reproducible problem or capability. Add the regression signal before the fix:

- a unit/fixture test for mechanical behavior;
- an Agent eval assertion for judgment-heavy behavior;
- both when applicable.

Run `python3 scripts/run_ci.py` before opening a pull request. Changes to `SKILL.md`, `references/`, `assets/`, validator behavior, audit behavior, or packaging semantics should include an eval benchmark comparison or explain why the change is mechanically covered and does not alter Agent behavior.

Do not commit customer source materials, generated eval outputs, credentials, dependency folders, caches, or distribution ZIPs. Use `evals/files/` only for synthetic or redistributable fixtures.
