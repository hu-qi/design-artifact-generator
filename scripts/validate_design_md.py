#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

from common import (
    HEX_RE, TOKEN_REF_RE, is_css_color, is_dimension, load_design,
    resolve_path, write_json,
)

ALLOWED_TOP = {"version", "name", "description", "colors", "typography", "rounded", "spacing", "components"}
TYPO_FIELDS = {"fontFamily", "fontSize", "fontWeight", "lineHeight", "letterSpacing", "fontFeature", "fontVariation"}
COMPONENT_FIELDS = {"backgroundColor", "textColor", "typography", "rounded", "padding", "size", "height", "width"}
SECTION_ALIASES = {
    "Overview": "Overview", "Brand & Style": "Overview",
    "Colors": "Colors", "Typography": "Typography",
    "Layout": "Layout", "Layout & Spacing": "Layout",
    "Elevation & Depth": "Elevation & Depth", "Elevation": "Elevation & Depth",
    "Shapes": "Shapes", "Components": "Components",
    "Do's and Don'ts": "Do's and Don'ts", "Dos and Don'ts": "Do's and Don'ts",
}
SECTION_ORDER = ["Overview", "Colors", "Typography", "Layout", "Elevation & Depth", "Shapes", "Components", "Do's and Don'ts"]
REQUIRED_SECTIONS = {"Overview", "Colors", "Typography", "Layout", "Components", "Do's and Don'ts"}


def finding(findings: list[dict[str, Any]], severity: str, path: str, message: str) -> None:
    findings.append({"severity": severity, "path": path, "message": message})


def parse_hex(value: str) -> tuple[int, int, int] | None:
    value = value.strip()
    if not HEX_RE.match(value):
        return None
    h = value[1:]
    if len(h) in (3, 4):
        h = "".join(ch * 2 for ch in h)
    if len(h) == 8:
        h = h[:6]
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def luminance(rgb: tuple[int, int, int]) -> float:
    vals = []
    for channel in rgb:
        c = channel / 255
        vals.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]


def contrast(a: str, b: str) -> float | None:
    ra, rb = parse_hex(a), parse_hex(b)
    if not ra or not rb:
        return None
    la, lb = luminance(ra), luminance(rb)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def scan_references(data: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    refs: dict[str, str] = {}

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, f"{path}.{key}" if path else str(key))
        elif isinstance(value, list):
            for idx, child in enumerate(value):
                walk(child, f"{path}[{idx}]")
        elif isinstance(value, str):
            match = TOKEN_REF_RE.match(value.strip())
            if match:
                refs[path] = match.group(1)
                try:
                    resolve_path(data, match.group(1))
                except KeyError:
                    finding(findings, "error", path, f"Unresolved token reference: {value}")

    walk(data, "")
    for start in refs:
        seen: set[str] = set()
        current = start
        while current in refs:
            if current in seen:
                finding(findings, "error", start, f"Circular token reference detected through {current}")
                break
            seen.add(current)
            target = refs[current]
            current = target


def resolved_scalar(data: dict[str, Any], value: Any) -> Any:
    seen: set[str] = set()
    while isinstance(value, str):
        match = TOKEN_REF_RE.match(value.strip())
        if not match:
            return value
        path = match.group(1)
        if path in seen:
            return value
        seen.add(path)
        try:
            value = resolve_path(data, path)
        except KeyError:
            return value
    return value


def validate(path: Path, strict: bool = False) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    try:
        data, body = load_design(path)
    except Exception as exc:
        finding(findings, "error", "$", str(exc))
        return report(path, findings)

    unknown = sorted(set(data) - ALLOWED_TOP)
    for key in unknown:
        finding(findings, "error" if strict else "warning", key, "Unsupported top-level frontmatter key; move this data to prose or a companion file")

    if data.get("version") != "alpha":
        finding(findings, "warning", "version", "Expected format version 'alpha'")
    if not isinstance(data.get("name"), str) or not data.get("name", "").strip():
        finding(findings, "error", "name", "A non-empty design-system name is required")

    colors = data.get("colors")
    if not isinstance(colors, dict) or not colors:
        finding(findings, "error", "colors", "At least one flat color token is required")
    else:
        for name, value in colors.items():
            if isinstance(value, dict):
                finding(findings, "error", f"colors.{name}", "Nested color groups are invalid; colors must map directly to CSS color strings")
            elif not is_css_color(value):
                finding(findings, "error", f"colors.{name}", f"Invalid CSS color value: {value!r}")

    typography = data.get("typography", {})
    if not isinstance(typography, dict):
        finding(findings, "error", "typography", "Typography must be a token map")
    else:
        for name, token in typography.items():
            p = f"typography.{name}"
            if not isinstance(token, dict):
                finding(findings, "error", p, "Typography tokens must be objects, not font-family strings or aliases")
                continue
            for field in sorted(set(token) - TYPO_FIELDS):
                finding(findings, "error" if strict else "warning", f"{p}.{field}", "Unsupported typography property")
            if not isinstance(token.get("fontFamily"), str) or not token.get("fontFamily", "").strip():
                finding(findings, "error", f"{p}.fontFamily", "fontFamily is required")
            if not is_dimension(token.get("fontSize")):
                finding(findings, "error", f"{p}.fontSize", "fontSize must use px, em, or rem")
            if "fontWeight" in token and not isinstance(token["fontWeight"], (int, float, str)):
                finding(findings, "error", f"{p}.fontWeight", "fontWeight must be numeric")
            if "lineHeight" in token and not (isinstance(token["lineHeight"], (int, float)) or is_dimension(token["lineHeight"])):
                finding(findings, "error", f"{p}.lineHeight", "lineHeight must be unitless or use px, em, or rem")
            if "letterSpacing" in token and not is_dimension(token["letterSpacing"]):
                finding(findings, "error", f"{p}.letterSpacing", "letterSpacing must use px, em, or rem")

    rounded = data.get("rounded", {})
    if not isinstance(rounded, dict):
        finding(findings, "error", "rounded", "Rounded must be a token map")
    else:
        for name, value in rounded.items():
            if not is_dimension(value):
                finding(findings, "error", f"rounded.{name}", "Rounded values must use px, em, or rem")

    spacing = data.get("spacing", {})
    if not isinstance(spacing, dict):
        finding(findings, "error", "spacing", "Spacing must be a token map")
    else:
        for name, value in spacing.items():
            if not (isinstance(value, (int, float)) or is_dimension(value)):
                finding(findings, "error", f"spacing.{name}", "Spacing values must be a number or dimension")

    components = data.get("components", {})
    if not isinstance(components, dict):
        finding(findings, "error", "components", "Components must be a token map")
    else:
        for name, token in components.items():
            p = f"components.{name}"
            if not isinstance(token, dict):
                finding(findings, "error", p, "A component token must be an object")
                continue
            for field, value in token.items():
                if field not in COMPONENT_FIELDS:
                    finding(findings, "warning", f"{p}.{field}", "Unknown component property; consumers should preserve it but portability may vary")
                if isinstance(value, (dict, list)):
                    finding(findings, "error", f"{p}.{field}", "Component properties must be scalar values or token references")
            bg = resolved_scalar(data, token.get("backgroundColor"))
            fg = resolved_scalar(data, token.get("textColor"))
            if isinstance(bg, str) and isinstance(fg, str):
                ratio = contrast(bg, fg)
                if ratio is not None:
                    severity = "info" if ratio >= 4.5 else "error"
                    finding(findings, severity, p, f"Text/background contrast ratio is {ratio:.2f}:1")

    scan_references(data, findings)

    headings = re.findall(r"^##\s+(.+?)\s*$", body, re.MULTILINE)
    canonical_seen: list[str] = []
    for heading in headings:
        canonical = SECTION_ALIASES.get(heading.strip())
        if canonical:
            if canonical in canonical_seen:
                finding(findings, "error", f"section:{heading}", f"Duplicate standard section: {canonical}")
            canonical_seen.append(canonical)
        elif re.match(r"^\d+[.)]?\s+", heading):
            finding(findings, "warning", f"section:{heading}", "Do not number standard headings; parsers may not recognize them")
    missing = REQUIRED_SECTIONS - set(canonical_seen)
    for section in sorted(missing):
        finding(findings, "error", f"section:{section}", "Required full-artifact section is missing")
    indices = [SECTION_ORDER.index(x) for x in canonical_seen]
    if indices != sorted(indices):
        finding(findings, "error", "sections", "Standard sections are not in the required sequence")

    return report(path, findings)


def report(path: Path, findings: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {level: sum(1 for item in findings if item["severity"] == level) for level in ("error", "warning", "info")}
    return {
        "schemaVersion": 1,
        "file": str(path),
        "findings": findings,
        "summary": summary,
        "valid": summary["error"] == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a DESIGN.md against the portable Google DESIGN.md profile")
    parser.add_argument("design_md", type=Path)
    parser.add_argument("--strict", action="store_true", help="Treat unsupported top-level and typography keys as errors")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = validate(args.design_md, args.strict)
    if args.out:
        write_json(args.out, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
