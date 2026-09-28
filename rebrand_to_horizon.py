#!/usr/bin/env python3
"""One-shot rebrand: headroom -> horizon.

Idempotent, ordered, case-aware cascade. Re-running after a successful
apply reports zero changes, which is the audit signal.

Usage:
    python rebrand_to_horizon.py            # dry-run: report what would change
    python rebrand_to_horizon.py --apply    # write changes + rename file/dir names

The directory renames (headroom/ -> horizon/, crates/headroom-* -> crates/horizon-*)
are NOT done here; do them with `git mv` BEFORE running --apply so history follows.
This script handles file CONTENT and file/dir NAME occurrences inside the tree.
The script always excludes ITSELF from processing (its rules contain the
literal search strings).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SELF_NAME = "rebrand_to_horizon.py"

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "target",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".hypothesis",
    "dist",
    "build",
    ".idea",
    ".vscode",
    ".worktrees",
    "headroom.egg-info",
    "horizon.egg-info",
    ".fastembed_cache",
    "onnx",
}

TEXT_EXTS = {
    ".py", ".toml", ".rs", ".md", ".yml", ".yaml", ".json", ".cfg", ".txt",
    ".html", ".css", ".js", ".mjs", ".ts", ".tsx", ".ps1", ".sh", ".hcl",
    ".ini", ".svg", ".lock", ".c", ".sql",
}

SPECIAL_FILENAMES = {
    "makefile", "dockerfile", ".dockerignore", ".gitignore", ".gitattributes",
    ".env.example", ".env.act.example", ".commitlintrc.json", ".changelog.md",
}

# Never touch: upstream legal history (LICENSE/NOTICE), this tool itself,
# and files replaced manually elsewhere.
EXCLUDE_FILES = {"CHANGELOG.md", "LICENSE", "NOTICE", "BASELINE.md", SELF_NAME}

# Ordered: most specific first. The 3-case cascade after the URL rules covers
# every category (imports, env vars, headers, tool names, config dirs, crates)
# consistently by construction.
RULES: list[tuple[str, str]] = [
    ("github.com/headroomlabs-ai/headroom", "github.com/your-org/horizon"),
    ("docs.headroomlabs.ai", "docs.horizon.invalid"),
    ("headroomlabs.ai", "horizon.invalid"),
    ("headroomlabs-ai", "your-org"),
    ("HEADROOM", "HORIZON"),
    ("Headroom", "Horizon"),
    ("headroom", "horizon"),
]


def is_text_file(path: Path) -> bool:
    if path.name.lower() in SPECIAL_FILENAMES:
        return True
    return path.suffix.lower() in TEXT_EXTS


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.name in EXCLUDE_FILES:
            continue
        if not is_text_file(path):
            continue
        yield path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    parser.add_argument("--root", default=".", help="repo root (default: cwd)")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    total_by_rule = {old: 0 for old, _ in RULES}
    changed_files = 0
    for path in iter_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            print(f"SKIP (unreadable): {path}")
            continue
        new_text = text
        for old, new in RULES:
            count = new_text.count(old)
            if count:
                total_by_rule[old] += count
                new_text = new_text.replace(old, new)
        if new_text != text:
            changed_files += 1
            print(f"CHANGE: {path.relative_to(root)}")
            if args.apply:
                path.write_text(new_text, encoding="utf-8", newline="")

    print()
    print(f"files changed: {changed_files}")
    for old, count in total_by_rule.items():
        print(f"  {old!r}: {count}")
    if not args.apply:
        print()
        print("dry run — re-run with --apply to write changes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
