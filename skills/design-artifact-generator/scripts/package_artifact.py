#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import sha256_file, write_json

EXCLUDE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "__MACOSX"}
EXCLUDE_FILES = {".DS_Store", "Thumbs.db", ".artifact-project.json"}


def run(command: list[str]) -> int:
    result = subprocess.run(command, text=True)
    return result.returncode


def included_files(root: Path, output_zip: Path | None = None) -> list[Path]:
    items = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in EXCLUDE_DIRS for part in rel.parts) or path.name in EXCLUDE_FILES:
            continue
        if path.suffix.lower() == ".zip":
            continue
        if output_zip and path.resolve() == output_zip.resolve():
            continue
        items.append(path)
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate, manifest, and ZIP a design artifact")
    parser.add_argument("root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--allow-errors", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    out = args.out.resolve()
    scripts = Path(__file__).resolve().parent
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (root / "tokens").mkdir(parents=True, exist_ok=True)

    validate_code = run([sys.executable, str(scripts / "validate_design_md.py"), str(root / "DESIGN.md"), "--strict", "--out", str(reports / "design-md-lint.json")])
    tokens_code = run([sys.executable, str(scripts / "generate_tokens.py"), str(root / "DESIGN.md"), "--json", str(root / "tokens" / "tokens.json"), "--css", str(root / "tokens" / "tokens.css")])

    project = {}
    project_file = root / ".artifact-project.json"
    if project_file.exists():
        project = json.loads(project_file.read_text(encoding="utf-8"))
    name = project.get("name") or root.name
    slug = project.get("slug") or root.name
    version = project.get("version") or "1.0.0"

    preliminary = {
        "schemaVersion": 1,
        "kind": "design-artifact",
        "name": name,
        "slug": slug,
        "version": version,
        "entry": "index.html",
        "designSystem": "DESIGN.md",
        "htmlEntries": [p.relative_to(root).as_posix() for p in root.rglob("*.html")],
        "packagedAt": datetime.now(timezone.utc).isoformat(),
        "validation": {"designMdExitCode": validate_code, "tokenExportExitCode": tokens_code},
        "files": [],
    }
    write_json(root / "artifact.json", preliminary)

    audit_code = run([sys.executable, str(scripts / "audit_artifact.py"), str(root), "--out", str(reports / "artifact-audit.json")])

    files = included_files(root, out)
    manifest_files = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        if rel == "artifact.json":
            continue
        manifest_files.append({"path": rel, "size": path.stat().st_size, "sha256": sha256_file(path)})
    preliminary["validation"]["artifactAuditExitCode"] = audit_code
    preliminary["files"] = manifest_files
    write_json(root / "artifact.json", preliminary)

    if (validate_code or tokens_code or audit_code) and not args.allow_errors:
        print(json.dumps({"packaged": False, "reason": "validation failed", "codes": preliminary["validation"]}, ensure_ascii=False, indent=2))
        return 1

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in included_files(root, out):
            zf.write(path, arcname=f"{root.name}/{path.relative_to(root).as_posix()}")
    print(json.dumps({"packaged": True, "output": str(out), "files": len(included_files(root, out)), "bytes": out.stat().st_size}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
