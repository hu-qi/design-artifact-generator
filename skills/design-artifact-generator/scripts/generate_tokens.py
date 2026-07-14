#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import css_var_name, load_design, value_to_css, write_json


def generate(design_md: Path) -> tuple[dict[str, Any], str]:
    data, _ = load_design(design_md)
    token_data = {key: data.get(key, {}) for key in ("colors", "typography", "rounded", "spacing", "components")}
    lines = ["/* Generated from DESIGN.md. Do not edit by hand. */", ":root {"]
    for name, value in data.get("colors", {}).items():
        lines.append(f"  {css_var_name('color', name)}: {value};")
    for name, token in data.get("typography", {}).items():
        if not isinstance(token, dict):
            continue
        for field, value in token.items():
            field_name = {
                "fontFamily": "font-family", "fontSize": "font-size", "fontWeight": "font-weight",
                "lineHeight": "line-height", "letterSpacing": "letter-spacing",
                "fontFeature": "font-feature", "fontVariation": "font-variation",
            }.get(field, field)
            lines.append(f"  {css_var_name('type', name, field_name)}: {value_to_css(data, value)};")
    for name, value in data.get("rounded", {}).items():
        lines.append(f"  {css_var_name('rounded', name)}: {value};")
    for name, value in data.get("spacing", {}).items():
        lines.append(f"  {css_var_name('spacing', name)}: {value};")
    for name, token in data.get("components", {}).items():
        if not isinstance(token, dict):
            continue
        for field, value in token.items():
            lines.append(f"  {css_var_name('component', name, field)}: {value_to_css(data, value)};")
    lines.append("}")
    lines.append("")
    for name, token in data.get("typography", {}).items():
        if not isinstance(token, dict):
            continue
        lines.extend([
            f".type-{name} {{",
            f"  font-family: var({css_var_name('type', name, 'font-family')});",
            f"  font-size: var({css_var_name('type', name, 'font-size')});",
        ])
        for prop, field in (("font-weight", "font-weight"), ("line-height", "line-height"), ("letter-spacing", "letter-spacing")):
            if any(k for k, mapped in {"fontWeight":"font-weight","lineHeight":"line-height","letterSpacing":"letter-spacing"}.items() if mapped == field and k in token):
                lines.append(f"  {prop}: var({css_var_name('type', name, field)});")
        lines.append("}")
        lines.append("")
    return token_data, "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Export DESIGN.md tokens to JSON and CSS")
    parser.add_argument("design_md", type=Path)
    parser.add_argument("--json", dest="json_path", type=Path, required=True)
    parser.add_argument("--css", dest="css_path", type=Path, required=True)
    args = parser.parse_args()
    token_data, css = generate(args.design_md)
    write_json(args.json_path, token_data)
    args.css_path.parent.mkdir(parents=True, exist_ok=True)
    args.css_path.write_text(css, encoding="utf-8")
    print(json.dumps({"json": str(args.json_path), "css": str(args.css_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
