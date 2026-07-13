#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with: python3 -m pip install 'PyYAML>=6.0'") from exc

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
TOKEN_REF_RE = re.compile(r"^\{([A-Za-z0-9_.-]+)\}$")
DIMENSION_RE = re.compile(r"^-?(?:\d+(?:\.\d+)?|\.\d+)(?:px|em|rem)$")
HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
CSS_FUNCTION_RE = re.compile(r"^(?:rgb|rgba|hsl|hsla|hwb|oklch|oklab|lch|lab|color-mix)\(", re.I)
CSS_NAMED = {
    "transparent", "black", "white", "red", "green", "blue", "gray", "grey",
    "yellow", "orange", "purple", "pink", "currentcolor", "inherit"
}


def load_design(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("DESIGN.md must begin with YAML frontmatter delimited by exact --- lines")
    data = yaml.safe_load(match.group(1)) or {}
    if not isinstance(data, dict):
        raise ValueError("YAML frontmatter must be a mapping")
    return data, text[match.end():]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_dimension(value: Any) -> bool:
    return isinstance(value, str) and bool(DIMENSION_RE.match(value.strip()))


def is_css_color(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    v = value.strip().lower()
    return bool(HEX_RE.match(v) or CSS_FUNCTION_RE.match(v) or v in CSS_NAMED)


def resolve_path(data: Any, path: str) -> Any:
    current = data
    for segment in path.split("."):
        if not isinstance(current, dict) or segment not in current:
            raise KeyError(path)
        current = current[segment]
    return current


def css_var_name(group: str, name: str, field: str | None = None) -> str:
    raw = "-".join(part for part in (group, name, field) if part)
    return "--" + re.sub(r"[^a-zA-Z0-9_-]+", "-", raw).strip("-").lower()


def value_to_css(data: dict[str, Any], value: Any) -> str:
    if isinstance(value, str):
        match = TOKEN_REF_RE.match(value.strip())
        if match:
            parts = match.group(1).split(".")
            if len(parts) >= 2:
                group, name = parts[0], parts[1]
                field = parts[2] if len(parts) > 2 else None
                return f"var({css_var_name(group[:-1] if group.endswith('s') else group, name, field)})"
    return str(value)
