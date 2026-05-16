#!/usr/bin/env python3
"""Run ReferenceFootnote local gates."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from reflib import ROOT, VERSION, print_json, result, run_command


def check_scripts() -> list[str]:
    errors = []
    for script in sorted((ROOT / "scripts").glob("*.py")):
        if script.name == "reflib.py":
            continue
        code, _out, err = run_command(["python3", str(script), "--help"], ROOT)
        if code != 0:
            errors.append(f"{script.name} --help failed: {err.strip()}")
    return errors


def check_forbidden_tokens() -> list[str]:
    errors = []
    forbidden = ["cu" + "rl ", "wg" + "et ", "ss" + "h ", "sc" + "p ", "rs" + "ync ", "localhost" + ":22", "openclaw" + "-cnki-takeover"]
    for base in ["scripts", "agents"]:
        for path in (ROOT / base).glob("**/*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                for token in forbidden:
                    if token in text:
                        errors.append(f"forbidden token {token!r} in {path.relative_to(ROOT)}")
    return errors


def check_claude_review(required: bool) -> list[str]:
    review = Path(os.environ.get("REFERENCEFOOTNOTE_REVIEW_PATH", ROOT / ".handoff" / "claude" / f"{VERSION}-review.md"))
    if not review.exists():
        return ["Claude review missing"] if required else []
    text = review.read_text(encoding="utf-8")
    if "APPROVED_WITH_NOTES" in text or "APPROVED" in text:
        return []
    return ["Claude review exists but is not approved"]


def check_git_release() -> list[str]:
    errors = []
    code, out, _err = run_command(["git", "status", "--porcelain"], ROOT)
    if code != 0 or out.strip():
        errors.append("git working tree is not clean")
    code, out, _err = run_command(["git", "tag", "--list", VERSION], ROOT)
    if code != 0 or out.strip() != VERSION:
        errors.append(f"git tag missing: {VERSION}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--pre-review", action="store_true")
    mode.add_argument("--release", action="store_true")
    args = parser.parse_args()
    if not args.pre_review and not args.release:
        args.pre_review = True
    errors = []
    for cmd in [
        ["python3", "scripts/verify-structure.py", "--target", "reference-footnote"],
        ["python3", "scripts/startup.py"],
        ["python3", "tests/run-fixtures.py", "--all"],
    ]:
        code, out, err = run_command(cmd, ROOT)
        if code != 0:
            errors.append(f"{' '.join(cmd)} failed: {err.strip() or out.strip()}")
    errors.extend(check_scripts())
    errors.extend(check_forbidden_tokens())
    if args.release:
        errors.extend(check_claude_review(required=True))
        errors.extend(check_git_release())
    else:
        if not check_claude_review(required=True):
            errors.append("pre-review mode expected Claude review to be absent or unpublished")
    print_json(result("failed" if errors else "passed", mode="release" if args.release else "pre-review", errors=errors))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
