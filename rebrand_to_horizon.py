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
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

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
    ".ruff",
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
    ".ini", ".svg", ".lock",
}

SPECIAL_FILENAMES = {
    "Makefile", "Dockerfile", ".dockerignore", ".gitignore", ".gitattributes",
    ".env.example", ".env.act.example", ".commitlintrc.json", ".changelog.md",
}

# Never touch (history stays upstream's; replaced separately).
EXCLUDE_FILES = {"CHANGELOG.md"}

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

NAME_MARKERS = ("headroom", "HEADROOM", "Headroom")


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


def rename_paths(root: Path) -> list[tuple[Path, str]]:
    """Rename files/dirs whose names contain a headroom marker (dirs last)."""
    renames: list[tuple[Path, str]] = []
    for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts[:-1] if path.is_dir() else rel.parts[:-1]):
            continue
        name = path.name
        new_name = name
        for marker, repl in (("headroom", "horizon"), ("HEADROOM", "HORIZON"), ("Headroom", "Horizon")):
            new_name = new_name.replace(marker, repl)
        if new_name != name:
            renames.append((path, new_name))
    return renames


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
            print(f"CHANGE ({sum(text.count(o) for o, _ in RULES)}): {path.relative_to(root)}")
            if args.apply:
                path.write_text(new_text, encoding="utf-8", newline="")

    if args.apply:
        for path, new_name in rename_paths(root):
            target = path.with_name(new_name)
            print(f"RENAME: {path.relative_to(root)} -> {new_name}")
            path.rename(target)

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
