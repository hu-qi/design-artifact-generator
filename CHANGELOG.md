# Changelog

## 1.1.0 — 2026-07-13

- Added GitHub Actions CI across Python 3.10–3.14 and pinned official Google DESIGN.md validation.
- Added reproducible Skill distribution builds, SHA-256 sidecars, and tag-driven GitHub releases.
- Added positive and negative contract fixtures for DESIGN.md validation, artifact audit, packaging, and Skill structure.
- Added an eval workspace manager for isolated candidate/baseline runs, evidence grading, benchmark aggregation, regression gating, iteration plans, and human-approved baseline promotion.
- Added explicit self-iteration safeguards, semantic version tooling, maintainer guidance, pull-request checks, and synthetic eval fixtures.
- Added Dependabot and a scheduled upstream `@google/design.md` version-drift watcher that opens or updates a review issue without auto-upgrading the Skill.

## 1.0.0 — 2026-07-13

- Added evidence-driven full/design-md/prototype/audit workflows.
- Added strict Google DESIGN.md compatibility validation.
- Added deterministic token JSON/CSS export.
- Added portable static prototype starter.
- Added input inventory, artifact audit, manifest and ZIP packaging scripts.
- Added quality rubric, eval cases and executable script tests.
