#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONFIGS = ("candidate", "baseline")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slugify(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value[:48] or "case"


def load_cases(skill_root: Path) -> list[dict[str, Any]]:
    data = read_json(skill_root / "evals" / "evals.json")
    cases = data.get("evals")
    if not isinstance(cases, list) or not cases:
        raise ValueError("evals/evals.json has no eval cases")
    return cases


def case_directory(case: dict[str, Any]) -> str:
    label = case.get("name") or str(case.get("prompt", ""))[:60]
    return f"eval-{int(case['id']):03d}-{slugify(str(label))}"


def command_init(args: argparse.Namespace) -> int:
    skill_root = args.skill_root.resolve()
    cases = load_cases(skill_root)
    iteration_root = args.workspace.resolve() / f"iteration-{args.iteration}"
    if iteration_root.exists() and any(iteration_root.iterdir()) and not args.force:
        raise SystemExit(f"Workspace is not empty: {iteration_root}. Use --force to replace it.")
    if iteration_root.exists() and args.force:
        import shutil
        shutil.rmtree(iteration_root)
    iteration_root.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schemaVersion": 1,
        "iteration": args.iteration,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "skillRoot": str(skill_root),
        "skillVersion": args.skill_version,
        "baselineLabel": args.baseline_label,
        "configs": list(CONFIGS),
        "evals": [],
    }
    for case in cases:
        directory = case_directory(case)
        manifest["evals"].append({"id": case["id"], "directory": directory})
        for config in CONFIGS:
            run_root = iteration_root / directory / config
            (run_root / "outputs").mkdir(parents=True, exist_ok=True)
            inputs = "\n".join(f"- {item}" for item in case.get("files", [])) or "- none"
            prompt = (
                f"# Eval {case['id']} — {config}\n\n"
                f"Skill configuration: `{config}`. For `candidate`, use the current skill. "
                f"For `baseline`, use {args.baseline_label}.\n\n"
                f"## Task\n\n{case['prompt']}\n\n"
                f"## Input files\n\n{inputs}\n\n"
                f"## Output directory\n\n`{(run_root / 'outputs').as_posix()}`\n"
            )
            (run_root / "prompt.md").write_text(prompt, encoding="utf-8")
            grading = {
                "assertion_results": [
                    {"text": assertion, "passed": None, "evidence": ""}
                    for assertion in case.get("assertions", [])
                ],
                "human_score": None,
                "notes": "",
            }
            write_json(run_root / "grading.template.json", grading)
            write_json(run_root / "timing.template.json", {"total_tokens": None, "duration_ms": None})
    write_json(iteration_root / "run-manifest.json", manifest)
    write_json(iteration_root / "feedback.json", {})
    write_json(iteration_root / "review.json", {"approved": False, "reviewer": "", "notes": ""})
    print(json.dumps({"workspace": str(iteration_root), "evals": len(cases), "configs": list(CONFIGS)}, ensure_ascii=False, indent=2))
    return 0


def validate_grading(path: Path, assertions: list[str]) -> tuple[list[dict[str, Any]], float | None, str]:
    if not path.is_file():
        raise ValueError(f"Missing grading file: {path}")
    data = read_json(path)
    results = data.get("assertion_results")
    if not isinstance(results, list) or len(results) != len(assertions):
        raise ValueError(f"{path}: assertion_results must contain exactly {len(assertions)} entries")
    normalized: list[dict[str, Any]] = []
    for index, (result, expected) in enumerate(zip(results, assertions, strict=True)):
        if not isinstance(result, dict) or result.get("text") != expected:
            raise ValueError(f"{path}: assertion {index + 1} text does not match evals/evals.json")
        passed = result.get("passed")
        evidence = str(result.get("evidence", "")).strip()
        if not isinstance(passed, bool):
            raise ValueError(f"{path}: assertion {index + 1} passed must be true or false")
        if not evidence:
            raise ValueError(f"{path}: assertion {index + 1} requires concrete evidence")
        normalized.append({"text": expected, "passed": passed, "evidence": evidence})
    human_score = data.get("human_score")
    if human_score is not None:
        if not isinstance(human_score, (int, float)) or not 0 <= float(human_score) <= 5:
            raise ValueError(f"{path}: human_score must be between 0 and 5")
        human_score = float(human_score)
    return normalized, human_score, str(data.get("notes", ""))


def load_timing(path: Path) -> dict[str, float | None]:
    if not path.is_file():
        return {"total_tokens": None, "duration_ms": None}
    data = read_json(path)
    result: dict[str, float | None] = {}
    for key in ("total_tokens", "duration_ms"):
        value = data.get(key)
        result[key] = float(value) if isinstance(value, (int, float)) and value >= 0 else None
    return result


def summarize_config(eval_rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = sum(row["assertions"]["total"] for row in eval_rows)
    passed = sum(row["assertions"]["passed"] for row in eval_rows)
    pass_rate = passed / total if total else 0.0
    human_scores = [row["human_score"] / 5 for row in eval_rows if row.get("human_score") is not None]
    human_mean = statistics.fmean(human_scores) if human_scores else None
    score = pass_rate if human_mean is None else (0.8 * pass_rate + 0.2 * human_mean)
    tokens = [row["timing"]["total_tokens"] for row in eval_rows if row["timing"]["total_tokens"] is not None]
    durations = [row["timing"]["duration_ms"] for row in eval_rows if row["timing"]["duration_ms"] is not None]
    return {
        "score": round(score, 6),
        "pass_rate": round(pass_rate, 6),
        "assertions": {"passed": passed, "failed": total - passed, "total": total},
        "human_score_mean": round(human_mean * 5, 4) if human_mean is not None else None,
        "tokens_mean": round(statistics.fmean(tokens), 2) if tokens else None,
        "duration_ms_mean": round(statistics.fmean(durations), 2) if durations else None,
        "per_eval": {str(row["id"]): row for row in eval_rows},
    }


def command_aggregate(args: argparse.Namespace) -> int:
    skill_root = args.skill_root.resolve()
    iteration_root = args.iteration_root.resolve()
    cases = load_cases(skill_root)
    configurations: dict[str, Any] = {}
    for config in CONFIGS:
        rows: list[dict[str, Any]] = []
        for case in cases:
            run_root = iteration_root / case_directory(case) / config
            assertions, human_score, notes = validate_grading(run_root / "grading.json", case.get("assertions", []))
            timing = load_timing(run_root / "timing.json")
            passed = sum(1 for item in assertions if item["passed"])
            failures = [item for item in assertions if not item["passed"]]
            rows.append({
                "id": case["id"],
                "name": case.get("name", ""),
                "assertions": {"passed": passed, "failed": len(assertions) - passed, "total": len(assertions)},
                "pass_rate": round(passed / len(assertions), 6) if assertions else 0.0,
                "human_score": human_score,
                "failures": failures,
                "notes": notes,
                "timing": timing,
            })
        configurations[config] = summarize_config(rows)

    manifest = read_json(iteration_root / "run-manifest.json") if (iteration_root / "run-manifest.json").is_file() else {}
    review = read_json(iteration_root / "review.json") if (iteration_root / "review.json").is_file() else {"approved": False}
    feedback = read_json(iteration_root / "feedback.json") if (iteration_root / "feedback.json").is_file() else {}
    result = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "iteration": manifest.get("iteration"),
        "skillVersion": args.skill_version or manifest.get("skillVersion"),
        "configurations": configurations,
        "delta": {
            "score": round(configurations["candidate"]["score"] - configurations["baseline"]["score"], 6),
            "pass_rate": round(configurations["candidate"]["pass_rate"] - configurations["baseline"]["pass_rate"], 6),
            "tokens_mean": delta_optional(configurations["candidate"].get("tokens_mean"), configurations["baseline"].get("tokens_mean")),
            "duration_ms_mean": delta_optional(configurations["candidate"].get("duration_ms_mean"), configurations["baseline"].get("duration_ms_mean")),
        },
        "humanReview": review,
        "feedback": feedback,
    }
    out = args.out or iteration_root / "benchmark.json"
    write_json(out, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def delta_optional(candidate: float | None, baseline: float | None) -> float | None:
    if candidate is None or baseline is None:
        return None
    return round(candidate - baseline, 2)


def load_policy(path: Path) -> dict[str, Any]:
    data = read_json(path)
    return {
        "minimum_candidate_pass_rate": float(data.get("minimum_candidate_pass_rate", 0.85)),
        "max_overall_score_regression": float(data.get("max_overall_score_regression", 0.0)),
        "max_case_pass_rate_regression": float(data.get("max_case_pass_rate_regression", 0.0)),
        "max_token_increase_ratio": float(data.get("max_token_increase_ratio", 0.30)),
        "minimum_score_gain_for_large_token_increase": float(data.get("minimum_score_gain_for_large_token_increase", 0.03)),
        "require_human_approval_for_promotion": bool(data.get("require_human_approval_for_promotion", True)),
    }


def established_summary(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    data = read_json(path)
    if data.get("status") != "established":
        return None
    benchmark = data.get("benchmark")
    return benchmark if isinstance(benchmark, dict) else None


def command_compare(args: argparse.Namespace) -> int:
    benchmark = read_json(args.benchmark.resolve())
    policy = load_policy(args.policy.resolve())
    candidate = benchmark["configurations"]["candidate"]
    internal_baseline = benchmark["configurations"].get("baseline")
    promoted_baseline = established_summary(args.baseline.resolve())
    baseline = internal_baseline or promoted_baseline
    findings: list[dict[str, Any]] = []

    def add(severity: str, code: str, message: str, **details: Any) -> None:
        findings.append({"severity": severity, "code": code, "message": message, **details})

    if candidate["pass_rate"] < policy["minimum_candidate_pass_rate"]:
        add("error", "minimum-pass-rate", "Candidate pass rate is below the release threshold", candidate=candidate["pass_rate"], minimum=policy["minimum_candidate_pass_rate"])

    if baseline:
        score_delta = candidate["score"] - baseline["score"]
        if score_delta < -policy["max_overall_score_regression"]:
            add("error", "overall-regression", "Candidate score regressed against baseline", delta=round(score_delta, 6))
        for case_id, candidate_case in candidate.get("per_eval", {}).items():
            base_case = baseline.get("per_eval", {}).get(case_id)
            if not base_case:
                continue
            delta = candidate_case["pass_rate"] - base_case["pass_rate"]
            if delta < -policy["max_case_pass_rate_regression"]:
                add("error", "case-regression", f"Eval {case_id} regressed", eval_id=case_id, delta=round(delta, 6))
        ct, bt = candidate.get("tokens_mean"), baseline.get("tokens_mean")
        if ct is not None and bt not in (None, 0):
            ratio = (ct - bt) / bt
            gain = candidate["score"] - baseline["score"]
            if ratio > policy["max_token_increase_ratio"] and gain < policy["minimum_score_gain_for_large_token_increase"]:
                add("warning", "token-cost", "Token usage increased without enough quality gain", token_increase_ratio=round(ratio, 4), score_gain=round(gain, 6))
    else:
        add("info", "baseline-unestablished", "No established baseline exists; only absolute thresholds were applied")

    summary = {level: sum(1 for item in findings if item["severity"] == level) for level in ("error", "warning", "info")}
    result = {
        "schemaVersion": 1,
        "benchmark": str(args.benchmark.resolve()),
        "baseline": str(args.baseline.resolve()),
        "policy": policy,
        "findings": findings,
        "summary": summary,
        "valid": summary["error"] == 0,
    }
    if args.out:
        write_json(args.out.resolve(), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


def hint_for(text: str) -> str:
    lowered = text.lower()
    mappings = [
        (("design.md", "token", "typography", "color"), "SKILL.md §2, references/google-design-md.md, scripts/validate_design_md.py"),
        (("evidence", "observed", "proposed", "source"), "SKILL.md §1 and references/input-analysis.md"),
        (("prototype", "responsive", "screen", "component", "state"), "SKILL.md §4 and references/prototype-contract.md"),
        (("accessib", "keyboard", "focus", "alt"), "references/prototype-contract.md and scripts/audit_artifact.py"),
        (("zip", "package", "manifest", "checksum"), "SKILL.md §6, references/artifact-contract.md, scripts/package_artifact.py"),
        (("audit", "validation", "report"), "SKILL.md §5 and scripts/audit_artifact.py"),
    ]
    for words, target in mappings:
        if any(word in lowered for word in words):
            return target
    return "Review SKILL.md wording first; add or change a script only when the failure is mechanical and repeated"


def command_plan(args: argparse.Namespace) -> int:
    benchmark = read_json(args.benchmark.resolve())
    comparison = read_json(args.comparison.resolve()) if args.comparison and args.comparison.is_file() else None
    candidate = benchmark["configurations"]["candidate"]
    failures: list[tuple[str, dict[str, Any]]] = []
    for case_id, case in candidate.get("per_eval", {}).items():
        for failure in case.get("failures", []):
            failures.append((case_id, failure))
    lines = [
        "# Skill Iteration Plan",
        "",
        f"Generated from `{args.benchmark}`.",
        "",
        "## Release gate",
        "",
    ]
    if comparison:
        lines.append(f"- Gate status: **{'PASS' if comparison.get('valid') else 'FAIL'}**")
        for finding in comparison.get("findings", []):
            lines.append(f"- `{finding['severity']}` `{finding['code']}` — {finding['message']}")
    else:
        lines.append("- Comparison report was not supplied.")
    lines.extend(["", "## Failed assertions", ""])
    if not failures:
        lines.append("- None. Focus on human feedback, transcript efficiency, and unnecessary instruction weight.")
    else:
        for case_id, failure in failures:
            lines.append(f"### Eval {case_id}")
            lines.append(f"- Failure: {failure['text']}")
            lines.append(f"- Evidence: {failure['evidence']}")
            lines.append(f"- Likely change surface: {hint_for(failure['text'])}")
            lines.append("- Required regression test: preserve this assertion and add a deterministic fixture when the behavior is mechanically verifiable.")
            lines.append("")
    feedback = benchmark.get("feedback", {})
    lines.extend(["## Human feedback", ""])
    if isinstance(feedback, dict) and any(str(v).strip() for v in feedback.values()):
        for key, value in feedback.items():
            if str(value).strip():
                lines.append(f"- **{key}:** {value}")
    else:
        lines.append("- No actionable human feedback recorded.")
    lines.extend([
        "",
        "## Change discipline",
        "",
        "1. Reproduce before editing and keep the failing eval unchanged.",
        "2. Fix the smallest reusable layer: instruction, reference, template, then deterministic script.",
        "3. Do not add case-specific wording that only matches the current prompt.",
        "4. Run `python3 scripts/run_ci.py` and rerun every agent eval in a fresh iteration directory.",
        "5. Require human approval before promoting the benchmark baseline.",
    ])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"written": str(args.out), "failed_assertions": len(failures)}, ensure_ascii=False, indent=2))
    return 0


def command_promote(args: argparse.Namespace) -> int:
    benchmark = read_json(args.benchmark.resolve())
    comparison = read_json(args.comparison.resolve())
    policy = load_policy(args.policy.resolve())
    if not comparison.get("valid"):
        raise SystemExit("Cannot promote a benchmark that failed the comparison gate")
    review = benchmark.get("humanReview", {})
    if policy["require_human_approval_for_promotion"] and not review.get("approved"):
        raise SystemExit("Human review approval is required before baseline promotion")
    candidate = benchmark["configurations"]["candidate"]
    result = {
        "schemaVersion": 1,
        "status": "established",
        "skillVersion": benchmark.get("skillVersion"),
        "promotedAt": datetime.now(timezone.utc).isoformat(),
        "review": review,
        "sourceBenchmark": args.benchmark.name,
        "sourceIteration": benchmark.get("iteration"),
        "benchmark": candidate,
    }
    write_json(args.baseline.resolve(), result)
    print(json.dumps({"promoted": True, "baseline": str(args.baseline.resolve()), "score": candidate.get("score")}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create, aggregate, compare, plan, and promote Agent Skill eval iterations")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="Create an isolated eval workspace")
    p.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parent.parent)
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--iteration", type=int, required=True)
    p.add_argument("--skill-version", required=True)
    p.add_argument("--baseline-label", default="the previous released skill version or a no-skill run")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=command_init)

    p = sub.add_parser("aggregate", help="Aggregate completed grading and timing files")
    p.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parent.parent)
    p.add_argument("--iteration-root", type=Path, required=True)
    p.add_argument("--skill-version")
    p.add_argument("--out", type=Path)
    p.set_defaults(func=command_aggregate)

    p = sub.add_parser("compare", help="Apply regression and efficiency gates")
    p.add_argument("--benchmark", type=Path, required=True)
    p.add_argument("--baseline", type=Path, default=Path(__file__).resolve().parent.parent / "evals" / "baseline.json")
    p.add_argument("--policy", type=Path, default=Path(__file__).resolve().parent.parent / "evals" / "policy.json")
    p.add_argument("--out", type=Path)
    p.set_defaults(func=command_compare)

    p = sub.add_parser("plan", help="Generate a reviewable iteration plan from failures")
    p.add_argument("--benchmark", type=Path, required=True)
    p.add_argument("--comparison", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.set_defaults(func=command_plan)

    p = sub.add_parser("promote", help="Promote an approved passing candidate to baseline")
    p.add_argument("--benchmark", type=Path, required=True)
    p.add_argument("--comparison", type=Path, required=True)
    p.add_argument("--baseline", type=Path, default=Path(__file__).resolve().parent.parent / "evals" / "baseline.json")
    p.add_argument("--policy", type=Path, default=Path(__file__).resolve().parent.parent / "evals" / "policy.json")
    p.set_defaults(func=command_promote)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
