#!/usr/bin/env python3
"""Zip every skill into dist/<skill-name>.zip (the skill folder is the zip's top-level folder).

Those zips can be uploaded one by one in Claude's Skills settings.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS, DIST = ROOT / "skills", ROOT / "dist"


def main() -> int:
    DIST.mkdir(exist_ok=True)
    count = 0
    for skill in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        target = DIST / f"{skill.name}.zip"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(skill.rglob("*")):
                if f.is_file() and "__pycache__" not in f.parts and f.suffix != ".pyc":
                    z.write(f, Path(skill.name) / f.relative_to(skill))
        print(f"wrote {target.relative_to(ROOT)}")
        count += 1
    print(f"{count} skill zips in dist/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
