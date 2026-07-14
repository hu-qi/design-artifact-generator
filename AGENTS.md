# AGENTS.md

This file gives guidance to AI coding agents (Claude Code, Cursor, Copilot, AtomCode, etc.) when working with code in this repository.

## Repository Overview

A single Agent Skill — `design-artifact-generator` — that converts brand and product evidence into a Google DESIGN.md-compliant design system and a runnable high-fidelity UI prototype package. Skills follow the [Agent Skills](https://agentskills.io/) format and are installable via `npx skills add hu-qi/design-artifact-generator`.

## Repository Structure

```
design-artifact-generator/
├── skills/                              # Skill payload (what gets distributed)
│   └── design-artifact-generator/       # Skill name must match parent directory
│       ├── SKILL.md                      # Required: skill definition
│       ├── scripts/                      # Required: executable scripts called by the agent
│         ├── inspect_inputs.py
│         ├── validate_design_md.py
│         ├── generate_tokens.py
│         ├── init_artifact.py
│         ├── audit_artifact.py
│         ├── package_artifact.py
│         ├── check_skill.py              # Validates skill structure
│         ├── build_skill_distribution.py # Builds the release ZIP
│         └── common.py
│       ├── references/                   # Optional: supporting docs loaded on demand
│       └ assets/                        # Optional: templates and prototype starter
├── scripts/                             # Repository-level development scripts (NOT distributed)
│   ├── run_ci.py                         # Local CI equivalent
│   ├── bump_version.py                  # Semantic version tooling
│   ├── check_upstream.py                # @google/design.md drift watcher
│   └── manage_evals.py                  # Eval workspace manager
├── tests/                               # Test suite (NOT distributed)
├── evals/                               # Eval cases and baselines (NOT distributed)
├── .github/workflows/                    # CI, release, spec-watch
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── MAINTAINING.md
├── requirements.txt                     # Python deps for dev and runtime
└── AGENTS.md
```

The skill payload lives under `skills/design-artifact-generator/`. Everything outside `skills/` is repository tooling that is not distributed to end users via `npx skills add`.

## SKILL.md Format

```markdown
---
name: design-artifact-generator
description: One sentence describing when to use this skill, including trigger phrases.
license: Apache-2.0
compatibility: Runtime requirements.
metadata:
  author: open-source-workflow
  version: "X.Y.Z"
  specification: "agentskills.io"
---
```

### Required Fields

- `name`: Unique identifier (lowercase, hyphens allowed). Must match the parent directory name.
- `description`: Brief explanation of what the skill does and when to use it.

### Optional Fields

- `license`, `compatibility`, `metadata` (string-to-string map).

## Best Practices for Context Efficiency

Skills are loaded on-demand — only the skill name and description are loaded at startup. The full `SKILL.md` loads into context only when the agent decides the skill is relevant. To minimize context usage:

- **Keep SKILL.md under 500 lines** — put detailed reference material in `references/`.
- **Write specific descriptions** — helps the agent know exactly when to activate the skill.
- **Use progressive disclosure** — reference supporting files that get read only when needed.
- **Prefer scripts over inline code** — script execution doesn't consume context (only output does).
- **File references work one level deep** — link directly from SKILL.md to supporting files.

## Script Requirements

- Python scripts: use `#!/usr/bin/env python3`.
- Reference scripts by relative path, for example `python3 scripts/validate_design_md.py`.
- PyYAML is required for validation scripts; install with `python3 -m pip install -r requirements.txt`.

## Repository-Level Development Scripts

Scripts under the root `scripts/` directory are NOT part of the distributed skill. They operate on the whole repository:

- `run_ci.py` — Runs the deterministic quality gates (calls `check_skill.py`, unit tests, distribution build).
- `bump_version.py` — Updates `SKILL.md` metadata.version and inserts a `CHANGELOG.md` entry.
- `check_upstream.py` — Watches `@google/design.md` for version drift.
- `manage_evals.py` — Manages isolated eval workspaces for self-iteration.

These scripts reference the skill payload at `skills/design-artifact-generator/`.

## CI and Release

Run the deterministic local equivalent of GitHub Actions:

```bash
python3 -m pip install -r requirements.txt
python3 scripts/run_ci.py
```

Before release, include the pinned official Google validator:

```bash
python3 scripts/run_ci.py --official-design-md
```

A git tag `vX.Y.Z` triggers the release workflow. The tag, `SKILL.md` metadata.version, and the top `CHANGELOG.md` heading must all match. The release ZIP is built from `skills/design-artifact-generator/` only; repository-level tooling is not included in the distribution.

## End-User Installation

```bash
npx skills add hu-qi/design-artifact-generator
```

This clones the repository and copies the entire `skills/design-artifact-generator/` directory (including `scripts/`, `references/`, `assets/`) into the agent's skills directory. End users receive the skill payload only — not the repository-level test, eval, or CI tooling.

For manual installs:

```bash
cp -r skills/design-artifact-generator ~/.claude/skills/
```
