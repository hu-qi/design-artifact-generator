#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


def valid_slug(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise argparse.ArgumentTypeError("slug must be lowercase kebab-case")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a design artifact workspace")
    parser.add_argument("--name", required=True)
    parser.add_argument("--slug", required=True, type=valid_slug)
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parent.parent
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()) and not args.force:
        raise SystemExit(f"Output directory is not empty: {out}. Use --force to replace it.")
    if out.exists() and args.force:
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    starter = skill_root / "assets" / "prototype-starter"
    shutil.copytree(starter, out, dirs_exist_ok=True)
    shutil.copy2(skill_root / "assets" / "design-md.template.md", out / "DESIGN.md")
    shutil.copy2(skill_root / "assets" / "artifact-readme.template.md", out / "README.md")
    for directory in ("tokens", "evidence", "reports", "prototype", "screenshots"):
        (out / directory).mkdir(exist_ok=True)
    shutil.copy2(skill_root / "assets" / "sources.template.md", out / "evidence" / "sources.md")
    shutil.copy2(skill_root / "assets" / "decisions.template.md", out / "evidence" / "decisions.md")
    shutil.copy2(skill_root / "assets" / "critique.template.json", out / "reports" / "critique.json")

    replacements = {
        "[REPLACE: Design System Name]": args.name,
        "[REPLACE: Artifact name]": args.name,
        "Version: `1.0.0`": f"Version: `{args.version}`",
        "DESIGN SYSTEM · V1.0.0": f"DESIGN SYSTEM · V{args.version}",
    }
    for rel in ("DESIGN.md", "README.md", "index.html"):
        path = out / rel
        text = path.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")

    project = {"name": args.name, "slug": args.slug, "version": args.version, "directory": str(out)}
    (out / ".artifact-project.json").write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(project, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
