#!/usr/bin/env python3
"""Copy the committed broadsheet to the grader's output path.

The image was drawn by compose.py in this repository (Pillow, bundled fonts,
no network). This entrypoint uses only the standard library so the two
required runs write identical bytes without depending on third-party
packages in the sandbox.

Output directory: MAKEFUN_OUTPUT_DIR if set, otherwise /output.
The file name is always entry.png.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path


def main() -> None:
    src = Path(__file__).resolve().parent / "entry.png"
    dest_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest_dir / "entry.png")


if __name__ == "__main__":
    main()
