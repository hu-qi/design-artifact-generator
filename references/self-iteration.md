# Self-iteration and release discipline

This Skill may help maintainers improve the Skill itself, but it must not silently rewrite its own source during normal design-artifact generation. Self-iteration is an explicit repository-maintenance workflow with reproducible evidence, regression gates, and human approval.

## Two quality tiers

### Tier 1 — deterministic CI

Run for every pull request and release:

```bash
python3 scripts/run_ci.py
```

It validates:

- Agent Skills frontmatter and directory naming;
- version and changelog consistency;
- eval definitions and fixture paths;
- Python syntax and executable contract tests;
- DESIGN.md positive and negative fixtures;
- artifact audit and packaging behavior;
- reproducible Skill ZIP construction.

The network-dependent upstream Google validator is an additional gate:

```bash
python3 scripts/run_ci.py --official-design-md
```

### Tier 2 — Agent behavior evals

Run when changing `SKILL.md`, behavioral references, prompts, templates, validators, audits, or packaging semantics. CI cannot generate or judge high-fidelity designs by itself, so this tier uses isolated Agent runs plus evidence-backed grading.

## Iteration loop

### 1. Reproduce and freeze the failure

Add or update a realistic case in `evals/evals.json`. Keep the prompt general enough to represent a class of tasks. Add concrete assertions after observing the output. For mechanically verifiable failures, also add a deterministic fixture and unit test before changing behavior.

### 2. Create an isolated workspace

```bash
python3 scripts/manage_evals.py init \
  --workspace ../design-artifact-generator-workspace \
  --iteration 1 \
  --skill-version 1.1.0 \
  --baseline-label "design-artifact-generator v1.0.0"
```

Each eval receives clean `candidate/` and `baseline/` directories with prompts, output locations, grading templates, and timing templates. Run the candidate with the current Skill and the baseline with the previous released Skill or, for the first benchmark, without the Skill.

Do not reuse Agent context between cases or configurations.

### 3. Grade with evidence

For each run:

1. copy `grading.template.json` to `grading.json`;
2. mark every assertion `true` or `false`;
3. provide a file path, report finding, visible UI behavior, or quoted output as evidence;
4. optionally assign `human_score` from 0 to 5;
5. copy `timing.template.json` to `timing.json` and record tokens and duration when available.

A PASS without concrete evidence is invalid.

### 4. Aggregate and apply regression gates

```bash
python3 scripts/manage_evals.py aggregate \
  --iteration-root ../design-artifact-generator-workspace/iteration-1 \
  --out ../design-artifact-generator-workspace/iteration-1/benchmark.json

python3 scripts/manage_evals.py compare \
  --benchmark ../design-artifact-generator-workspace/iteration-1/benchmark.json \
  --out ../design-artifact-generator-workspace/iteration-1/comparison.json
```

The default policy requires:

- candidate assertion pass rate of at least 85%;
- no overall score regression;
- no per-case pass-rate regression;
- review of token-cost increases over 30%;
- human approval before baseline promotion.

Tune thresholds only through a reviewed change to `evals/policy.json`. Never lower a threshold merely to release a failing candidate.

### 5. Generate the change plan

```bash
python3 scripts/manage_evals.py plan \
  --benchmark ../design-artifact-generator-workspace/iteration-1/benchmark.json \
  --comparison ../design-artifact-generator-workspace/iteration-1/comparison.json \
  --out ../design-artifact-generator-workspace/iteration-1/ITERATION_PLAN.md
```

Use failed assertions, human feedback, and execution traces together. Prefer the smallest reusable fix in this order:

1. remove ambiguous or wasteful instruction;
2. clarify a step in `SKILL.md`;
3. move detailed guidance into a focused reference;
4. improve a template;
5. bundle a deterministic script for repeated mechanical work.

Do not add prompt-specific patches that only recognize the eval wording.

### 6. Re-run everything

Create a new `iteration-N+1` directory and rerun all cases, not only the failed case. A local fix may regress another mode.

### 7. Human review and baseline promotion

Complete the iteration `review.json`:

```json
{
  "approved": true,
  "reviewer": "maintainer name or handle",
  "notes": "Reviewed all candidate outputs and accepted the quality/cost trade-off."
}
```

Re-aggregate, rerun comparison, then promote:

```bash
python3 scripts/manage_evals.py promote \
  --benchmark ../design-artifact-generator-workspace/iteration-2/benchmark.json \
  --comparison ../design-artifact-generator-workspace/iteration-2/comparison.json
```

Promotion updates `evals/baseline.json`. Commit the baseline change with the behavior change so future releases compare against a real benchmark. The bootstrap baseline intentionally remains `unestablished` until genuine Agent outputs have been reviewed; do not fabricate scores.

## Version and release

Choose semantic versioning based on user-visible behavior:

- patch: validator fix, audit fix, wording clarification without changing output contract;
- minor: new mode, new artifact output, new evaluation capability, backward-compatible behavior improvement;
- major: incompatible artifact contract, removed mode, or changed normative defaults.

After all gates pass:

```bash
python3 scripts/bump_version.py minor \
  --message "Describe the behavior change" \
  --message "Describe the regression coverage"

python3 scripts/run_ci.py --official-design-md
python3 scripts/build_skill_distribution.py . --out dist/design-artifact-generator-vX.Y.Z.zip
```

A Git tag `vX.Y.Z` triggers the release workflow. The tag, `SKILL.md` version, and top changelog version must match.

## Upstream drift

`@google/design.md` is still an alpha format. The scheduled `spec-watch.yml` workflow compares the pinned package version in `references/upstream-lock.json` against the public registry. Drift creates or updates an issue; it does not automatically update validators or the lock.

When drift is detected:

1. read the upstream specification and changelog;
2. add fixtures for changed behavior;
3. update the local reference and validator;
4. run the official old/new CLI diff where useful;
5. rerun Tier 1 and Tier 2 gates;
6. update `references/upstream-lock.json` only after acceptance.

## Non-negotiable safeguards

- Never self-modify during a user artifact generation run.
- Never promote an unreviewed benchmark.
- Never claim improvement from one successful example.
- Never delete an eval because the candidate fails it unless the assertion itself is demonstrably invalid.
- Never place secrets, source customer materials, or private outputs in committed eval fixtures.
- Prefer a reviewable branch and pull request over direct default-branch changes.
