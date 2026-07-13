# Design Artifact Generator Skill

A lightweight Agent Skill that converts brand and product evidence into two coupled outputs:

1. a strict, machine-readable and human-readable `DESIGN.md` based on Google’s format;
2. a runnable UI artifact that proves the specification through a component catalog and realistic product screens.

It intentionally avoids the desktop daemon, web application, plugin registry, model routing, and persistent runtime used by full design platforms. The Agent is the design engine; bundled scripts provide deterministic validation, quality gates, evaluation lifecycle management, and reproducible packaging.

## Install

Copy the `design-artifact-generator` directory into the skills directory supported by your Agent client. The folder name must remain `design-artifact-generator` because the Agent Skills specification requires it to match the `name` field.

## Typical prompts

```text
根据这些品牌资料、参考网站、现有系统截图和需求文档，生成完整 DESIGN.md，落地为可运行演示原型，并输出 versioned ZIP。
```

```text
审计这个现有 DESIGN.md 是否符合 google-labs-code/design.md，并修复后生成组件规范页。
```

```text
读取当前 Vue 项目和品牌资料，保留业务信息架构，重做视觉系统；同时提供独立静态评审包。
```

## Artifact commands

```bash
python3 scripts/inspect_inputs.py input.zip --out input-inventory.json
python3 scripts/validate_design_md.py DESIGN.md --strict
python3 scripts/generate_tokens.py DESIGN.md --json tokens/tokens.json --css tokens/tokens.css
python3 scripts/audit_artifact.py ./my-product-design-v1.0
python3 scripts/package_artifact.py ./my-product-design-v1.0 --out my-product-design-v1.0.zip
```

PyYAML is required:

```bash
python3 -m pip install -r requirements.txt
```

## CI and release

Run the deterministic local equivalent of GitHub Actions:

```bash
python3 scripts/run_ci.py
```

Before release, include the pinned official Google validator:

```bash
python3 scripts/run_ci.py --official-design-md
```

The repository includes:

- a Python 3.10–3.14 CI matrix;
- positive and negative DESIGN.md contract tests;
- artifact audit and packaging tests;
- reproducible Skill ZIP construction;
- tag-driven GitHub releases with SHA-256 sidecars;
- Dependabot for Actions and Python dependencies;
- a monthly upstream `@google/design.md` drift watcher.

## Eval-driven self-iteration

Self-iteration is explicit and human-governed. The Skill never silently rewrites itself during normal artifact generation.

```bash
python3 scripts/manage_evals.py init \
  --workspace ../design-artifact-generator-workspace \
  --iteration 1 \
  --skill-version 1.1.0 \
  --baseline-label "design-artifact-generator v1.0.0"
```

After isolated candidate and baseline runs are graded with concrete evidence:

```bash
python3 scripts/manage_evals.py aggregate \
  --iteration-root ../design-artifact-generator-workspace/iteration-1

python3 scripts/manage_evals.py compare \
  --benchmark ../design-artifact-generator-workspace/iteration-1/benchmark.json \
  --out ../design-artifact-generator-workspace/iteration-1/comparison.json

python3 scripts/manage_evals.py plan \
  --benchmark ../design-artifact-generator-workspace/iteration-1/benchmark.json \
  --comparison ../design-artifact-generator-workspace/iteration-1/comparison.json \
  --out ../design-artifact-generator-workspace/iteration-1/ITERATION_PLAN.md
```

A passing candidate can update `evals/baseline.json` only after `review.json` records human approval. Full process and safeguards are documented in `references/self-iteration.md` and `MAINTAINING.md`.

## Build the Skill distribution

```bash
python3 scripts/build_skill_distribution.py . \
  --out dist/design-artifact-generator-v1.1.0.zip
```

The builder validates the source, creates a deterministic ZIP payload, and writes a `.sha256` sidecar.

## Output philosophy

- Evidence before taste.
- Normative tokens before styling.
- Product context before component decoration.
- Runnable artifacts before screenshots.
- Automated checks before packaging.
- Eval evidence before Skill changes.
- Human approval before baseline promotion.
