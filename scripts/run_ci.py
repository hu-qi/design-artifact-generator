#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def run(name: str, command: list[str], cwd: Path, env: dict[str, str]) -> dict[str, Any]:
    print(f"\n== {name} ==")
    result = subprocess.run(command, cwd=cwd, text=True, env=env)
    return {"name": name, "command": command, "returncode": result.returncode}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the same deterministic quality gates used by GitHub Actions")
    parser.add_argument("--official-design-md", action="store_true", help="Also run the network-dependent official Google validator")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    skill_root = root / "skills" / "design-artifact-generator"
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    checks: list[dict[str, Any]] = []
    checks.append(run("skill structure", [sys.executable, str(skill_root / "scripts" / "check_skill.py"), str(skill_root)], root, env))
    checks.append(run("unit and contract tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"], root, env))

    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "skill.zip"
        checks.append(run("distribution smoke build", [sys.executable, str(skill_root / "scripts" / "build_skill_distribution.py"), str(skill_root), "--out", str(output)], root, env))
        if not output.is_file():
            checks.append({"name": "distribution exists", "command": [], "returncode": 1})

    if args.official_design_md:
        checks.append(run(
            "official Google DESIGN.md validator",
            ["npx", "--yes", "-p", "@google/design.md@0.3.0", "designmd", "lint", "tests/fixtures/minimal-artifact/DESIGN.md"],
            root,
            env,
        ))

    for cache in root.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)

    failed = [item for item in checks if item["returncode"] != 0]
    summary = {"valid": not failed, "checks": checks, "failed": [item["name"] for item in failed]}
    print("\n" + json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
