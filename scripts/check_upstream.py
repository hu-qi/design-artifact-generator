#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json_url(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "design-artifact-generator-spec-watch"})
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - fixed trusted URL
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect upstream format/tool version drift without modifying the skill")
    parser.add_argument("--lock", type=Path, default=Path(__file__).resolve().parent.parent / "references" / "upstream-lock.json")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    lock = json.loads(args.lock.read_text(encoding="utf-8"))
    findings: list[dict[str, Any]] = []
    checked: dict[str, Any] = {}
    try:
        npm = read_json_url("https://registry.npmjs.org/@google%2Fdesign.md/latest")
        latest = npm.get("version")
        pinned = lock["googleDesignMd"]["packageVersion"]
        checked["googleDesignMd"] = {"pinned": pinned, "latest": latest}
        if latest != pinned:
            findings.append({
                "severity": "warning",
                "code": "google-design-md-version-drift",
                "message": f"@google/design.md changed from pinned {pinned} to latest {latest}",
                "action": "Review the upstream specification and CLI, update references/google-design-md.md, validators, fixtures, and the lock only after regression tests pass.",
            })
    except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as exc:
        findings.append({"severity": "error", "code": "upstream-check-failed", "message": str(exc)})

    summary = {level: sum(1 for item in findings if item["severity"] == level) for level in ("error", "warning", "info")}
    result = {
        "schemaVersion": 1,
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "lock": str(args.lock),
        "checked": checked,
        "findings": findings,
        "summary": summary,
        "drift": summary["warning"] > 0,
        "valid": summary["error"] == 0 and summary["warning"] == 0,
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
