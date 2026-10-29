"""Lightweight Vercel build step — import sanity only."""
from pathlib import Path
import importlib.util

root = Path(__file__).resolve().parent.parent
for mod in ("db_adapter", "registry_server", "bridge_v7", "server"):
    path = root / f"{mod}.py"
    spec = importlib.util.spec_from_file_location(mod, path)
    assert spec and spec.loader
    spec.loader.exec_module(importlib.util.module_from_spec(spec))
print("garakland build check ok")
