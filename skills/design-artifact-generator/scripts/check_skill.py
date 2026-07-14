#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with: python3 -m pip install 'PyYAML>=6.0'") from exc

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
CHANGELOG_VERSION_RE = re.compile(r"^##\s+([0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?)\b", re.MULTILINE)
JUNK_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "venv", "node_modules", "__MACOSX"}
JUNK_FILES = {".DS_Store", "Thumbs.db"}
REQUIRED_FILES = {
    "SKILL.md",
    "references/self-iteration.md",
    "scripts/build_skill_distribution.py",
}


def load_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("SKILL.md must begin with YAML frontmatter delimited by exact --- lines")
    data = yaml.safe_load(match.group(1)) or {}
    if not isinstance(data, dict):
        raise ValueError("SKILL.md frontmatter must be a mapping")
    return data, text[match.end():]


def check(root: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []

    def add(severity: str, path: str, message: str) -> None:
        findings.append({"severity": severity, "path": path, "message": message})

    skill_path = root / "SKILL.md"
    if not skill_path.is_file():
        add("error", "SKILL.md", "Required file is missing")
        return report(root, findings)

    try:
        frontmatter, _body = load_frontmatter(skill_path)
    except Exception as exc:
        add("error", "SKILL.md", str(exc))
        return report(root, findings)

    name = frontmatter.get("name")
    description = frontmatter.get("description")
    compatibility = frontmatter.get("compatibility")
    metadata = frontmatter.get("metadata", {})

    if not isinstance(name, str) or not NAME_RE.fullmatch(name) or "--" in name or len(name) > 64:
        add("error", "SKILL.md:name", "name must be lowercase kebab-case, 1-64 characters, with no consecutive hyphens")
    elif root.name != name:
        add("error", "SKILL.md:name", f"name {name!r} must match parent directory {root.name!r}")
    if not isinstance(description, str) or not description.strip() or len(description) > 1024:
        add("error", "SKILL.md:description", "description must be non-empty and at most 1024 characters")
    if compatibility is not None and (not isinstance(compatibility, str) or not compatibility.strip() or len(compatibility) > 500):
        add("error", "SKILL.md:compatibility", "compatibility must be a non-empty string at most 500 characters")
    if not isinstance(metadata, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in metadata.items()):
        add("error", "SKILL.md:metadata", "metadata must map strings to strings")
        version = None
    else:
        version = metadata.get("version")
        if not isinstance(version, str) or not SEMVER_RE.fullmatch(version):
            add("error", "SKILL.md:metadata.version", "metadata.version must be semantic versioning")

    line_count = len(skill_path.read_text(encoding="utf-8").splitlines())
    if line_count > 500:
        add("error", "SKILL.md", f"SKILL.md has {line_count} lines; keep it under 500 and move detail to references/")

    for rel in sorted(REQUIRED_FILES):
        if not (root / rel).is_file():
            add("error", rel, "Required maintenance or runtime file is missing")

    changelog = root / "CHANGELOG.md"
    if changelog.is_file() and version:
        match = CHANGELOG_VERSION_RE.search(changelog.read_text(encoding="utf-8"))
        if not match:
            add("error", "CHANGELOG.md", "No release heading was found")
        elif match.group(1) != version:
            add("error", "CHANGELOG.md", f"Top changelog version {match.group(1)} does not match SKILL.md version {version}")

    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if any(part in JUNK_PARTS for part in rel.parts) or path.name in JUNK_FILES:
            add("error", rel.as_posix(), "Generated cache, dependency, or OS junk must not be committed or distributed")
        if path.is_file() and path.suffix == ".py":
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (SyntaxError, UnicodeDecodeError) as exc:
                add("error", rel.as_posix(), f"Python source cannot be parsed: {exc}")

    return report(root, findings)


def report(root: Path, findings: list[dict[str, str]]) -> dict[str, Any]:
    summary = {level: sum(1 for item in findings if item["severity"] == level) for level in ("error", "warning", "info")}
    return {"schemaVersion": 1, "root": str(root), "findings": findings, "summary": summary, "valid": summary["error"] == 0}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Agent Skill source tree and release metadata")
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = check(args.root.resolve())
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
