#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
VERSION_LINE_RE = re.compile(r'(?m)^(\s{2}version:\s*")[^"]+("\s*)$')


def next_version(current: str, target: str) -> str:
    match = SEMVER_RE.fullmatch(current)
    if not match:
        raise ValueError(f"Current version is not stable semver: {current}")
    major, minor, patch = map(int, match.groups())
    if target == "major":
        return f"{major + 1}.0.0"
    if target == "minor":
        return f"{major}.{minor + 1}.0"
    if target == "patch":
        return f"{major}.{minor}.{patch + 1}"
    if not SEMVER_RE.fullmatch(target):
        raise ValueError("Target must be patch, minor, major, or X.Y.Z")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Update SKILL.md and CHANGELOG.md for a reviewed release")
    parser.add_argument("target", help="patch, minor, major, or an explicit X.Y.Z")
    parser.add_argument("--message", action="append", required=True, help="Changelog bullet; repeat for multiple bullets")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    skill = root / "skills" / "design-artifact-generator" / "SKILL.md"
    changelog = root / "CHANGELOG.md"
    text = skill.read_text(encoding="utf-8")
    match = VERSION_LINE_RE.search(text)
    if not match:
        raise SystemExit("Could not find metadata.version in SKILL.md")
    current = text[match.start(0):match.end(0)].split('"')[1]
    target = next_version(current, args.target)
    updated_skill = VERSION_LINE_RE.sub(rf'\g<1>{target}\g<2>', text, count=1)

    change_text = changelog.read_text(encoding="utf-8")
    bullets = "\n".join(f"- {message.strip()}" for message in args.message if message.strip())
    entry = f"## {target} — {date.today().isoformat()}\n\n{bullets}\n\n"
    if change_text.startswith("# Changelog\n"):
        updated_changelog = "# Changelog\n\n" + entry + change_text[len("# Changelog\n"):].lstrip("\n")
    else:
        updated_changelog = "# Changelog\n\n" + entry + change_text

    result = {"current": current, "target": target, "messages": args.message, "dryRun": args.dry_run}
    if not args.dry_run:
        skill.write_text(updated_skill, encoding="utf-8")
        changelog.write_text(updated_changelog, encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
