#!/usr/bin/env python3
"""Check that every skill in skills/ is well formed. Exit code 1 if anything is wrong.

Rules (from the Agent Skills format):
  * skills/<name>/SKILL.md exists, starts with a YAML frontmatter block
  * frontmatter has `name` (lowercase letters, digits, hyphens; same as the folder) and `description`
  * description is 1..1024 characters and has no angle brackets
  * every relative file mentioned as `scripts/...` or `references/...` in SKILL.md exists
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REF_RE = re.compile(r"(?<![\w/.-])((?:scripts|references|assets)/[\w./-]+\w)")


def parse_frontmatter(text: str):
    m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        return None
    data: dict = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def check(skill_dir: Path) -> list:
    errors = []
    md = skill_dir / "SKILL.md"
    if not md.exists():
        return [f"{skill_dir.name}: SKILL.md is missing"]
    text = md.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    if fm is None:
        return [f"{skill_dir.name}: SKILL.md has no frontmatter"]
    name, desc = fm.get("name", ""), fm.get("description", "")
    if not NAME_RE.match(name) or len(name) > 64:
        errors.append(f"{skill_dir.name}: bad name {name!r}")
    if name != skill_dir.name:
        errors.append(f"{skill_dir.name}: name {name!r} does not match the folder")
    if "claude" in name or "anthropic" in name:
        errors.append(f"{skill_dir.name}: name may not contain 'claude' or 'anthropic'")
    if not desc:
        errors.append(f"{skill_dir.name}: description is empty")
    if len(desc) > 1024:
        errors.append(f"{skill_dir.name}: description is {len(desc)} chars (max 1024)")
    if "<" in desc or ">" in desc:
        errors.append(f"{skill_dir.name}: description must not contain angle brackets")
    body = text.split("---", 2)[2] if text.count("---") >= 2 else text
    for ref in sorted(set(REF_RE.findall(body))):
        if not (skill_dir / ref).exists():
            errors.append(f"{skill_dir.name}: mentions {ref} but the file does not exist")
    return errors


def main() -> int:
    dirs = sorted(p for p in SKILLS.iterdir() if p.is_dir())
    if not dirs:
        print("no skills found", file=sys.stderr)
        return 1
    problems = []
    for d in dirs:
        errs = check(d)
        problems += errs
        print(("FAIL " if errs else "ok   ") + d.name)
    for e in problems:
        print("  - " + e, file=sys.stderr)
    print(f"\n{len(dirs)} skills, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
