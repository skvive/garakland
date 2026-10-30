"""Lightweight Vercel build step — import sanity only."""
from pathlib import Path
import importlib
import sys

root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

for mod in ("db_adapter", "registry_server", "bridge_v7", "hub.core", "server"):
    importlib.import_module(mod)
print("garakland build check ok")
