#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with: python3 -m pip install 'PyYAML>=6.0'") from exc

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
EXCLUDED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build", "__MACOSX"}
EXCLUDED_FILES = {".DS_Store", "Thumbs.db"}
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def version_from_skill(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("SKILL.md has no valid YAML frontmatter")
    data = yaml.safe_load(match.group(1)) or {}
    version = (data.get("metadata") or {}).get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("SKILL.md metadata.version is missing")
    return version


def included_files(root: Path, output: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in EXCLUDED_DIRS for part in rel.parts) or path.name in EXCLUDED_FILES:
            continue
        if path.resolve() == output.resolve():
            continue
        if rel.parts[:2] == ("evals", "runs") and path.name != ".gitkeep":
            continue
        files.append(path)
    return files


def write_entry(archive: zipfile.ZipFile, source: Path, arcname: str) -> None:
    info = zipfile.ZipInfo(arcname, date_time=FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    mode = 0o755 if os.access(source, os.X_OK) else 0o644
    info.external_attr = mode << 16
    info.flag_bits |= 0x800  # UTF-8 filenames
    archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a reproducible Agent Skill ZIP and SHA-256 sidecar")
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--skip-check", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    version = version_from_skill(root / "SKILL.md")
    output = (args.out or root.parent / f"{root.name}-v{version}.zip").resolve()

    if not args.skip_check:
        check = subprocess.run([sys.executable, str(root / "scripts" / "check_skill.py"), str(root)], text=True)
        if check.returncode:
            return check.returncode

    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    files = included_files(root, output)
    with zipfile.ZipFile(output, "w") as archive:
        for path in files:
            rel = path.relative_to(root).as_posix()
            write_entry(archive, path, f"{root.name}/{rel}")

    digest = sha256(output)
    sidecar = output.with_suffix(output.suffix + ".sha256")
    sidecar.write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    result = {
        "schemaVersion": 1,
        "name": root.name,
        "version": version,
        "builtAt": datetime.now(timezone.utc).isoformat(),
        "reproduciblePayload": True,
        "output": str(output),
        "sha256": digest,
        "sha256File": str(sidecar),
        "files": len(files),
        "bytes": output.stat().st_size,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
