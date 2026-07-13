# Maintaining Design Artifact Generator

The repository uses a two-tier release gate:

1. deterministic CI for every pull request;
2. isolated Agent evals for behavioral changes.

Start with:

```bash
python3 -m pip install -r requirements.txt
python3 scripts/run_ci.py
```

Read `references/self-iteration.md` before changing instructions, validators, templates, or output contracts. Do not establish or update `evals/baseline.json` without reviewed Agent outputs and a passing comparison report.

## Release checklist

- [ ] The failure or feature is represented by an eval and, where possible, a deterministic test.
- [ ] `python3 scripts/run_ci.py --official-design-md` passes.
- [ ] Behavioral changes have a new isolated benchmark and human approval.
- [ ] `SKILL.md`, `CHANGELOG.md`, and the tag use the same semantic version.
- [ ] `python3 scripts/build_skill_distribution.py` produces a ZIP and SHA-256 sidecar.
- [ ] The ZIP is opened and `SKILL.md` is at `<zip-root>/design-artifact-generator/SKILL.md`.
