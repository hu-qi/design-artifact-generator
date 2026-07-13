#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import zipfile
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Any

from common import write_json

ROLE_BY_EXT = {
    ".png": "visual-reference", ".jpg": "visual-reference", ".jpeg": "visual-reference", ".webp": "visual-reference", ".gif": "visual-reference", ".svg": "brand-or-visual",
    ".pdf": "document", ".doc": "document", ".docx": "document", ".ppt": "document", ".pptx": "document", ".xls": "document", ".xlsx": "document",
    ".md": "requirements-or-guidance", ".txt": "requirements-or-guidance", ".html": "existing-product", ".css": "existing-product", ".js": "existing-product", ".ts": "existing-product", ".tsx": "existing-product", ".vue": "existing-product",
    ".ai": "brand-or-design-source", ".sketch": "design-source", ".fig": "design-source", ".zip": "archive",
}


def image_dimensions(stream: BinaryIO, suffix: str) -> tuple[int, int] | None:
    try:
        start = stream.read(32)
        if suffix == ".png" and start.startswith(b"\x89PNG"):
            return struct.unpack(">II", start[16:24])
        if suffix == ".gif" and start[:6] in (b"GIF87a", b"GIF89a"):
            return struct.unpack("<HH", start[6:10])
        if suffix in (".jpg", ".jpeg"):
            stream.seek(0)
            if stream.read(2) != b"\xff\xd8":
                return None
            while True:
                byte = stream.read(1)
                if not byte:
                    break
                if byte != b"\xff":
                    continue
                marker = stream.read(1)
                while marker == b"\xff":
                    marker = stream.read(1)
                if marker in (b"\xd8", b"\xd9"):
                    continue
                length_raw = stream.read(2)
                if len(length_raw) != 2:
                    break
                length = struct.unpack(">H", length_raw)[0]
                if marker and marker[0] in {0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF}:
                    data = stream.read(5)
                    if len(data) == 5:
                        height, width = struct.unpack(">HH", data[1:5])
                        return width, height
                    break
                stream.seek(length - 2, 1)
        if suffix == ".webp" and start[:4] == b"RIFF" and start[8:12] == b"WEBP":
            chunk = start[12:16]
            if chunk == b"VP8X" and len(start) >= 30:
                width = 1 + int.from_bytes(start[24:27], "little")
                height = 1 + int.from_bytes(start[27:30], "little")
                return width, height
    except Exception:
        return None
    return None


def safe_zip_name(name: str) -> bool:
    p = PurePosixPath(name)
    return not p.is_absolute() and ".." not in p.parts


def file_record(name: str, size: int, data: bytes | None = None, path: Path | None = None) -> dict[str, Any]:
    suffix = Path(name).suffix.lower()
    record: dict[str, Any] = {"path": name, "size": size, "extension": suffix, "roleHint": ROLE_BY_EXT.get(suffix, "other")}
    if data is not None:
        record["sha256"] = hashlib.sha256(data).hexdigest()
        from io import BytesIO
        dims = image_dimensions(BytesIO(data), suffix)
    elif path is not None:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        record["sha256"] = h.hexdigest()
        with path.open("rb") as f:
            dims = image_dimensions(f, suffix)
    else:
        dims = None
    if dims:
        record["width"], record["height"] = dims
    return record


def inspect(path: Path) -> dict[str, Any]:
    files = []
    warnings = []
    kind = "directory" if path.is_dir() else "file"
    if path.is_dir():
        for item in sorted(path.rglob("*")):
            if item.is_file():
                rel = item.relative_to(path).as_posix()
                files.append(file_record(rel, item.stat().st_size, path=item))
    elif zipfile.is_zipfile(path):
        kind = "zip"
        with zipfile.ZipFile(path) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                if not safe_zip_name(info.filename):
                    warnings.append({"path": info.filename, "message": "Unsafe archive path"})
                    continue
                if info.file_size > 100 * 1024 * 1024:
                    warnings.append({"path": info.filename, "message": "File exceeds 100 MiB inspection limit"})
                    files.append({"path": info.filename, "size": info.file_size, "roleHint": "large-file"})
                    continue
                data = zf.read(info)
                files.append(file_record(info.filename, info.file_size, data=data))
    elif path.is_file():
        files.append(file_record(path.name, path.stat().st_size, path=path))
    else:
        raise FileNotFoundError(path)
    role_counts: dict[str, int] = {}
    for item in files:
        role_counts[item["roleHint"]] = role_counts.get(item["roleHint"], 0) + 1
    return {
        "schemaVersion": 1,
        "input": str(path),
        "kind": kind,
        "fileCount": len(files),
        "totalBytes": sum(item.get("size", 0) for item in files),
        "roleHints": role_counts,
        "warnings": warnings,
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely inventory design input files or ZIP archives")
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = inspect(args.input)
    if args.out:
        write_json(args.out, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not result["warnings"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
