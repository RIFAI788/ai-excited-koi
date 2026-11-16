"""Koi Leap — ai-excited-01 entrypoint.

Copies the pre-rendered entry image (entry.png, drawn by render.py) to
the output directory. Pure copy, so both runs write identical bytes.
Standard library only.
"""

import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
DST = os.path.join(OUT_DIR, "entry.png")

os.makedirs(OUT_DIR, exist_ok=True)
shutil.copyfile(SRC, DST)

# The gate requires a whole, non-empty image file.
if os.path.getsize(DST) == 0:
    raise SystemExit("entry.png copied empty")
