---
name: design-artifact-generator
description: Generate a Google DESIGN.md-compliant design system and a runnable high-fidelity UI prototype package from brand documents, reference websites, screenshots, existing products, source code, or mixed design evidence. Use when the user asks for DESIGN.md, UI design specifications, design-system extraction, brand-to-UI translation, visual refresh, interactive prototype, component catalog, multi-theme prototype, or a distributable design ZIP.
license: Apache-2.0
compatibility: Requires file read/write and Python 3.10+. Web access is needed only when reference URLs must be inspected. Browser screenshot capability is recommended for visual QA but is not mandatory.
metadata:
  author: open-source-workflow
  version: "1.1.0"
  specification: "agentskills.io"
  design-md: "@google/design.md 0.3.0 / format alpha"
---

# Design Artifact Generator

Create an evidence-backed design system and its runnable implementation. The default result is a versioned ZIP containing a strict `DESIGN.md`, design tokens, a component/specification catalog, realistic product screens, source evidence, validation reports, and an artifact manifest.

## Default behavior

- Use **full mode** unless the user explicitly requests only `DESIGN.md`, only a prototype, or only an audit.
- Prefer a **zero-build static artifact** (`HTML + CSS + JavaScript`) so the result opens locally and can be reviewed without installing a framework.
- When the user supplies an existing application repository and asks for implementation in that stack, keep the existing stack and additionally produce a portable static design-review artifact unless they explicitly decline it.
- Do not ask for information already present in files, screenshots, URLs, or the current repository. Record material assumptions in `evidence/decisions.md`.

## Modes

| Mode | Trigger | Required output |
|---|---|---|
| `full` | default | `DESIGN.md` + tokens + catalog + product prototype + reports + ZIP |
| `design-md` | “只生成 DESIGN.md” | `DESIGN.md` + evidence + validation report |
| `prototype` | a valid `DESIGN.md` already exists | prototype + token exports + audit report |
| `audit` | review an existing artifact | reports only; do not silently rewrite files |

## Resource map

Read only what the current task needs:

- Read `references/input-analysis.md` before interpreting mixed source material.
- Read `references/google-design-md.md` before writing or modifying `DESIGN.md`.
- Read `references/prototype-contract.md` before implementing the prototype.
- Read `references/quality-rubric.md` before the final review.
- Read `references/artifact-contract.md` before packaging.
- Read `references/self-iteration.md` only when the task is to maintain, evaluate, or release this Skill itself.
- Use `assets/design-md.template.md` as the structural baseline.
- Use `assets/prototype-starter/` as a starting shell, not as a visual style to preserve.

## Workflow

### 1. Establish the evidence set

1. Inventory all supplied files without modifying them:

   ```bash
   python3 scripts/inspect_inputs.py <input-path> --out evidence/asset-inventory.json
   ```

2. Classify each source as one or more of:
   - brand authority: logo/VI/manual/official brand page;
   - product truth: current application, requirements, domain documents, real data;
   - visual reference: screenshots, competitor/reference sites, design files;
   - implementation constraint: existing framework, component library, accessibility or localization rules.
3. Create `evidence/sources.md` with source, date accessed, role, extraction, and confidence.
4. Create `evidence/decisions.md`. Tag every material decision as:
   - `observed`: directly visible or explicitly specified;
   - `derived`: computed or consistently inferred from multiple observations;
   - `proposed`: a design decision introduced to fill a gap.
5. Never present a proposed value as an official brand value.

### 2. Generate a spec-compliant `DESIGN.md`

1. Start from `assets/design-md.template.md`.
2. Keep the YAML frontmatter strictly compatible with Google DESIGN.md:
   - allowed normative groups: `version`, `name`, `description`, `colors`, `typography`, `rounded`, `spacing`, `components`;
   - `colors` must be a **flat map** from token names to valid CSS color strings;
   - typography entries use `fontFamily`, `fontSize`, `fontWeight`, `lineHeight`, `letterSpacing`, `fontFeature`, and `fontVariation`;
   - cross-token references use `{group.token-name}`;
   - do not put nested brand/theme objects in frontmatter. Put theme mappings in prose and, when needed, `tokens/themes.json`.
3. Use the standard Markdown sections in this exact order, without numeric prefixes:
   - `## Overview`
   - `## Colors`
   - `## Typography`
   - `## Layout`
   - `## Elevation & Depth`
   - `## Shapes`
   - `## Components`
   - `## Do's and Don'ts`
4. A complete UI specification should then add relevant extension sections after the standard sections, such as Iconography, Motion, Accessibility, Content, Data Visualization, Domain Patterns, Responsive Matrix, Localization, Governance, and Agent Implementation Guide.
5. Make tokens normative and prose explanatory. Every prototype style must resolve to a token or an explicitly documented derived value.
6. Validate locally:

   ```bash
   python3 scripts/validate_design_md.py DESIGN.md --strict --out reports/design-md-lint.json
   ```

7. When Node/network/package access is available, also run the official validator and preserve its JSON output:

   ```bash
   npx --yes -p @google/design.md@0.3.0 designmd lint DESIGN.md > reports/google-design-md-lint.json
   ```

8. Fix all errors before prototype work. Do not suppress structural findings merely to pass packaging.

### 3. Export implementation tokens

Generate deterministic token artifacts:

```bash
python3 scripts/generate_tokens.py DESIGN.md \
  --json tokens/tokens.json \
  --css tokens/tokens.css
```

For multiple themes, create `tokens/themes.json` with theme-to-token overrides while keeping the `DESIGN.md` normative token map flat.

### 4. Implement the design specification

1. Initialize a portable workspace when starting from scratch:

   ```bash
   python3 scripts/init_artifact.py \
     --name "<human name>" \
     --slug <kebab-case-slug> \
     --version 1.0.0 \
     --out <artifact-directory>
   ```

2. Build both:
   - a **design catalog** that visually demonstrates colors, typography, spacing, shapes, elevation, icons, controls, states, tables, forms, overlays, navigation, charts, and domain components;
   - at least one **realistic product flow or screen set** proving the design system works in context.
3. Use real domain language and user-provided facts. When real values are unavailable, show `—`, clearly marked sample data, or an empty state; do not invent performance metrics.
4. Implement required states: default, hover, focus-visible, active/selected, disabled, loading, empty, validation error, system error, success, permission-restricted, and destructive confirmation where relevant.
5. Implement responsive behavior at minimum for `1440`, `1024`, `768`, and `390` CSS pixels.
6. Ensure keyboard operation, visible focus, semantic landmarks, form labels, accessible names, non-color status cues, and reduced-motion behavior.
7. Keep all local asset references relative. Do not hotlink third-party assets. Do not include unlicensed fonts or assets.
8. Do not embed credentials, internal API tokens, private URLs, personal data, or source documents that are not intended for distribution.

### 5. Review and iterate

1. Run the artifact audit:

   ```bash
   python3 scripts/audit_artifact.py <artifact-directory> \
     --out <artifact-directory>/reports/artifact-audit.json
   ```

2. Perform visual review at all target widths. When a browser is available, capture screenshots into `screenshots/`.
3. Fill `reports/critique.json` using the axes in `references/quality-rubric.md`. Scores require evidence, not compliments.
4. Resolve all P0 findings and all design lint errors. Resolve P1 findings unless a documented constraint prevents it.
5. Re-open the final files from the packaged directory, not from a temporary draft location.

### 6. Package the result

Package only after validation:

```bash
python3 scripts/package_artifact.py <artifact-directory> \
  --out <slug>-design-v<version>.zip
```

The packager regenerates tokens, runs validation and audit, writes `artifact.json` with checksums, removes OS/editor junk, and refuses to package when required checks fail.


## Maintaining and iterating this Skill

This mode applies only when the user explicitly asks to improve, evaluate, version, or release the Skill source. Do not rewrite the Skill during an ordinary design-artifact generation task.

1. Read `references/self-iteration.md`.
2. Reproduce the issue with a deterministic fixture, an Agent eval assertion, or both before changing behavior.
3. Run the current Skill and the previous release or no-skill baseline in isolated eval workspaces.
4. Aggregate evidence, apply regression gates, and generate an iteration plan with `scripts/manage_evals.py`.
5. Make the smallest reusable change; do not add prompt-specific patches.
6. Run `python3 scripts/run_ci.py`; use `--official-design-md` before release.
7. Require recorded human approval before promoting `evals/baseline.json`.
8. Bump semantic version and changelog only after all gates pass, then build with `scripts/build_skill_distribution.py`.

## Hard requirements

- The deliverable is not complete if it only contains `DESIGN.md` in full mode.
- The prototype must visibly implement the generated rules; it cannot be a generic dashboard with recolored accents.
- `DESIGN.md` must not use nested color groups or nonstandard typography property names in normative frontmatter.
- Brand evidence, product facts, and proposed design decisions must remain distinguishable.
- No unresolved `TODO`, `[REPLACE]`, lorem ipsum, broken local links, missing image alt text, or hidden keyboard traps.
- No `__MACOSX`, `.DS_Store`, `.git`, dependency caches, secrets, or source archives inside the final ZIP.
- Do not claim validation passed unless the report exists and has zero errors.
- Do not silently self-modify, fabricate eval scores, or promote an unreviewed benchmark.

## Completion response

Return:

1. the packaged ZIP;
2. a one-paragraph summary of the design direction and implemented prototype scope;
3. validation status and any deliberate exceptions;
4. the main entry file (`index.html`) and the design source of truth (`DESIGN.md`).
