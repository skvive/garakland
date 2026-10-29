#!/usr/bin/env python3
"""Initialize schema + demo seeds on Neon (requires DATABASE_URL)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

if not (os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")):
    raise SystemExit("Set DATABASE_URL to a Neon connection string first.")

from server import setup

setup()
print("Neon bootstrap complete.")
