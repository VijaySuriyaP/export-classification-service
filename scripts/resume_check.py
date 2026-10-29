#!/usr/bin/env python3
"""Print the first unchecked project step for a clean continuation."""
from __future__ import annotations

import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
progress = root / "PROGRESS.md"
state = root / "STATE.md"
if state.exists():
    print("State checkpoint:")
    for line in state.read_text(encoding="utf-8").splitlines():
        if line.startswith(("- **Current step:**", "- **Exact next command:**", "- **Environment limitation:**")):
            print(line)
if not progress.exists():
    raise SystemExit("PROGRESS.md missing; begin at Step 1.")
for line in progress.read_text(encoding="utf-8").splitlines():
    match = re.match(r"- \[ \] Step (\d+): (.*)", line)
    if match:
        print(f"First unchecked step: {match.group(1)} — {match.group(2)}")
        raise SystemExit(0)
print("No unchecked numbered steps found in PROGRESS.md.")
