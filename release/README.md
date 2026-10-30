# Release artifacts

`GARAKLAND_PLATFORM_v1.zip` is built by:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build-platform-zip.ps1
```

The ZIP includes static UI review PNGs (`v4_*.png`, `v5_*.png`) when present at repo root.
Regenerate PNGs (optional):

```powershell
pip install playwright
playwright install chromium
python scripts/capture_review_screens.py
```

Large ZIP files are gitignored; keep them in this folder for handoff only.
