#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
VALID = ROOT / "tests" / "fixtures" / "minimal-artifact"
INVALID_DESIGN = ROOT / "tests" / "fixtures" / "invalid-design" / "DESIGN.md"
BROKEN = ROOT / "tests" / "fixtures" / "broken-artifact"


def run(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run([sys.executable, *args], cwd=cwd, text=True, capture_output=True, env=env)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DesignArtifactScriptTests(unittest.TestCase):
    def test_valid_design_generates_tokens_and_audits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = Path(temp_dir) / "artifact"
            shutil.copytree(VALID, artifact)
            validation = run(str(SCRIPTS / "validate_design_md.py"), str(artifact / "DESIGN.md"), "--strict", "--out", str(artifact / "reports" / "design-md-lint.json"))
            self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)
            tokens = run(str(SCRIPTS / "generate_tokens.py"), str(artifact / "DESIGN.md"), "--json", str(artifact / "tokens" / "tokens.json"), "--css", str(artifact / "tokens" / "tokens.css"))
            self.assertEqual(tokens.returncode, 0, tokens.stdout + tokens.stderr)
            audit = run(str(SCRIPTS / "audit_artifact.py"), str(artifact), "--out", str(artifact / "reports" / "artifact-audit.json"))
            self.assertEqual(audit.returncode, 0, audit.stdout + audit.stderr)
            lint = json.loads((artifact / "reports" / "design-md-lint.json").read_text())
            self.assertEqual(lint["summary"]["error"], 0)
            css = (artifact / "tokens" / "tokens.css").read_text()
            self.assertIn("--color-primary", css)

    def test_invalid_design_is_rejected_with_specific_findings(self) -> None:
        result = run(str(SCRIPTS / "validate_design_md.py"), str(INVALID_DESIGN), "--strict")
        self.assertNotEqual(result.returncode, 0)
        report = json.loads(result.stdout)
        messages = "\n".join(item["message"] for item in report["findings"])
        self.assertIn("Nested color groups", messages)
        self.assertIn("Unsupported typography property", messages)
        self.assertIn("Required full-artifact section is missing", messages)

    def test_broken_artifact_is_rejected(self) -> None:
        result = run(str(SCRIPTS / "audit_artifact.py"), str(BROKEN))
        self.assertNotEqual(result.returncode, 0)
        report = json.loads(result.stdout)
        messages = "\n".join(item["message"] for item in report["findings"])
        self.assertIn("Image is missing alt", messages)
        self.assertIn("Broken local src", messages)

    def test_artifact_packaging_writes_manifest_and_zip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            artifact = temp / "harbor-design-v1.0.0"
            shutil.copytree(VALID, artifact)
            (artifact / ".artifact-project.json").write_text(json.dumps({"name": "Harbor", "slug": "harbor", "version": "1.0.0"}), encoding="utf-8")
            out = temp / "harbor-design-v1.0.0.zip"
            result = run(str(SCRIPTS / "package_artifact.py"), str(artifact), "--out", str(out))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            manifest = json.loads((artifact / "artifact.json").read_text())
            self.assertEqual(manifest["version"], "1.0.0")
            self.assertTrue(out.is_file())
            with zipfile.ZipFile(out) as archive:
                names = archive.namelist()
                self.assertIn("harbor-design-v1.0.0/DESIGN.md", names)
                self.assertFalse(any("__pycache__" in name for name in names))

    def test_skill_source_check_passes(self) -> None:
        result = run(str(SCRIPTS / "check_skill.py"), str(ROOT))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)["valid"])

    def test_skill_distribution_is_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            one = Path(temp_dir) / "one.zip"
            two = Path(temp_dir) / "two.zip"
            first = run(str(SCRIPTS / "build_skill_distribution.py"), str(ROOT), "--out", str(one))
            second = run(str(SCRIPTS / "build_skill_distribution.py"), str(ROOT), "--out", str(two))
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertEqual(digest(one), digest(two))
            with zipfile.ZipFile(one) as archive:
                self.assertIn("design-artifact-generator/SKILL.md", archive.namelist())
                self.assertIn("design-artifact-generator/.github/workflows/ci.yml", archive.namelist())
                self.assertFalse(any("__pycache__" in name for name in archive.namelist()))

    def test_eval_iteration_aggregate_compare_plan_and_promote(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            workspace = temp / "workspace"
            init = run(str(SCRIPTS / "manage_evals.py"), "init", "--skill-root", str(ROOT), "--workspace", str(workspace), "--iteration", "1", "--skill-version", "1.1.0")
            self.assertEqual(init.returncode, 0, init.stdout + init.stderr)
            iteration = workspace / "iteration-1"
            manifest = json.loads((iteration / "run-manifest.json").read_text())
            cases = {case["id"]: case for case in json.loads((ROOT / "evals" / "evals.json").read_text())["evals"]}
            for item in manifest["evals"]:
                case = cases[item["id"]]
                for config in ("candidate", "baseline"):
                    run_root = iteration / item["directory"] / config
                    grading = json.loads((run_root / "grading.template.json").read_text())
                    for index, assertion in enumerate(grading["assertion_results"]):
                        assertion["passed"] = not (config == "baseline" and index == 0)
                        assertion["evidence"] = f"Synthetic evidence for eval {item['id']} assertion {index + 1}"
                    grading["human_score"] = 4.5 if config == "candidate" else 4.0
                    (run_root / "grading.json").write_text(json.dumps(grading, indent=2) + "\n")
                    timing = {"total_tokens": 1000 if config == "candidate" else 950, "duration_ms": 2000 if config == "candidate" else 1900}
                    (run_root / "timing.json").write_text(json.dumps(timing, indent=2) + "\n")
            (iteration / "review.json").write_text(json.dumps({"approved": True, "reviewer": "test", "notes": "Reviewed synthetic test data."}, indent=2) + "\n")

            benchmark = iteration / "benchmark.json"
            aggregate = run(str(SCRIPTS / "manage_evals.py"), "aggregate", "--skill-root", str(ROOT), "--iteration-root", str(iteration), "--out", str(benchmark))
            self.assertEqual(aggregate.returncode, 0, aggregate.stdout + aggregate.stderr)
            comparison = iteration / "comparison.json"
            baseline = temp / "baseline.json"
            baseline.write_text(json.dumps({"schemaVersion": 1, "status": "unestablished", "benchmark": None}) + "\n")
            compare = run(str(SCRIPTS / "manage_evals.py"), "compare", "--benchmark", str(benchmark), "--baseline", str(baseline), "--out", str(comparison))
            self.assertEqual(compare.returncode, 0, compare.stdout + compare.stderr)
            plan = iteration / "ITERATION_PLAN.md"
            planned = run(str(SCRIPTS / "manage_evals.py"), "plan", "--benchmark", str(benchmark), "--comparison", str(comparison), "--out", str(plan))
            self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)
            self.assertIn("Skill Iteration Plan", plan.read_text())
            promoted = run(str(SCRIPTS / "manage_evals.py"), "promote", "--benchmark", str(benchmark), "--comparison", str(comparison), "--baseline", str(baseline))
            self.assertEqual(promoted.returncode, 0, promoted.stdout + promoted.stderr)
            self.assertEqual(json.loads(baseline.read_text())["status"], "established")


if __name__ == "__main__":
    unittest.main()
