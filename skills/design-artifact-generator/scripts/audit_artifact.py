#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any

from common import write_json

PLACEHOLDER_RE = re.compile(r"\[REPLACE(?::[^\]]*)?\]|(?:^|\s)TODO\s*[:：-]|(?i:lorem ipsum dolor|feature one)", re.MULTILINE)
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "__MACOSX"}


class AuditHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[tuple[str, str]] = []
        self.images: list[dict[str, str]] = []
        self.inputs: list[dict[str, str]] = []
        self.labels_for: set[str] = set()
        self.lang = ""
        self.has_title = False
        self.has_viewport = False
        self.has_main = False
        self.buttons = 0
        self.empty_buttons = 0
        self._button_stack: list[dict[str, Any]] = []
        self._label_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {k: (v or "") for k, v in attrs}
        if tag == "html": self.lang = attr.get("lang", "")
        if tag == "title": self.has_title = True
        if tag == "meta" and attr.get("name", "").lower() == "viewport": self.has_viewport = True
        if tag == "main": self.has_main = True
        if tag in ("a", "link") and attr.get("href"): self.refs.append(("href", attr["href"]))
        if tag in ("img", "script", "iframe", "source") and attr.get("src"): self.refs.append(("src", attr["src"]))
        if tag == "img": self.images.append(attr)
        if tag in ("input", "select", "textarea"):
            self.inputs.append(attr)
        if tag == "label":
            self._label_depth += 1
            if attr.get("for"):
                self.labels_for.add(attr["for"])
        if tag in ("input", "select", "textarea") and self._label_depth:
            self.inputs[-1]["_wrapped_label"] = "true"
        if tag == "button":
            self.buttons += 1
            self._button_stack.append({
                "text": "",
                "named": bool(attr.get("aria-label") or attr.get("aria-labelledby") or attr.get("title")),
            })

    def handle_data(self, data: str) -> None:
        if self._button_stack:
            self._button_stack[-1]["text"] += data.strip()

    def handle_endtag(self, tag: str) -> None:
        if tag == "button" and self._button_stack:
            button = self._button_stack.pop()
            if not button["text"] and not button["named"]:
                self.empty_buttons += 1
        if tag == "label" and self._label_depth:
            self._label_depth -= 1


def is_external(ref: str) -> bool:
    if ref.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
        return True
    parts = urlsplit(ref)
    return bool(parts.scheme or parts.netloc)


def audit(root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []

    def add(severity: str, path: str, message: str) -> None:
        findings.append({"severity": severity, "path": path, "message": message})

    for required in ("DESIGN.md", "README.md", "index.html", "reports/critique.json"):
        if not (root / required).is_file():
            add("error", required, "Required artifact file is missing")

    junk_patterns = {".DS_Store", "Thumbs.db"}
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts) or path.name in junk_patterns:
            add("error", rel.as_posix(), "OS, editor, dependency, or cache junk must not be packaged")
        if path.is_file() and path.name.startswith(".env"):
            add("error", rel.as_posix(), "Environment files may contain secrets and must not be packaged")

    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        rel = path.relative_to(root).as_posix()
        if path.suffix.lower() in {".html", ".md", ".css", ".js", ".json", ".txt"}:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if PLACEHOLDER_RE.search(text):
                add("error", rel, "Unresolved placeholder, TODO, or filler text found")
        if path.suffix.lower() == ".html":
            parser = AuditHTMLParser()
            parser.feed(path.read_text(encoding="utf-8"))
            if not parser.lang: add("error", rel, "html[lang] is required")
            if not parser.has_title: add("error", rel, "A document title is required")
            if not parser.has_viewport: add("error", rel, "A responsive viewport meta tag is required")
            if not parser.has_main: add("warning", rel, "Use a semantic main landmark")
            for image in parser.images:
                if "alt" not in image:
                    add("error", rel, f"Image is missing alt: {image.get('src', '')}")
            for control in parser.inputs:
                ctype = control.get("type", "text").lower()
                if ctype in {"hidden", "submit", "button", "reset"}:
                    continue
                cid = control.get("id")
                if not (control.get("_wrapped_label") or control.get("aria-label") or control.get("aria-labelledby") or (cid and cid in parser.labels_for)):
                    add("warning", rel, f"Form control may lack an accessible name: {control.get('name') or cid or ctype}")
            if parser.empty_buttons:
                add("error", rel, f"{parser.empty_buttons} button(s) have no text or accessible-name evidence")
            for attr, ref in parser.refs:
                if is_external(ref):
                    continue
                target_ref = ref.split("#", 1)[0].split("?", 1)[0]
                if not target_ref:
                    continue
                target = (path.parent / target_ref).resolve()
                try:
                    target.relative_to(root.resolve())
                except ValueError:
                    add("error", rel, f"Local reference escapes artifact root: {ref}")
                    continue
                if not target.exists():
                    add("error", rel, f"Broken local {attr}: {ref}")

    critique = root / "reports" / "critique.json"
    if critique.exists():
        try:
            data = json.loads(critique.read_text(encoding="utf-8"))
            if data.get("score") is None:
                add("error", "reports/critique.json", "Critique score has not been completed")
            axes = data.get("axes")
            if not isinstance(axes, dict) or len(axes) < 8:
                add("error", "reports/critique.json", "Critique must contain the full quality-axis set")
            else:
                for name, axis in axes.items():
                    if not isinstance(axis, dict) or axis.get("score") is None or not str(axis.get("notes", "")).strip() or "[REPLACE" in str(axis.get("notes")):
                        add("error", f"reports/critique.json:{name}", "Critique axis is incomplete")
        except Exception as exc:
            add("error", "reports/critique.json", f"Invalid critique JSON: {exc}")

    summary = {level: sum(1 for x in findings if x["severity"] == level) for level in ("error", "warning", "info")}
    return {"schemaVersion": 1, "root": str(root), "findings": findings, "summary": summary, "valid": summary["error"] == 0}


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a distributable design artifact")
    parser.add_argument("root", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = audit(args.root.resolve())
    if args.out:
        write_json(args.out, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
