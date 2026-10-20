"""Package the verified ORBITL1-AX25 project into a clean release ZIP archive."""

from __future__ import annotations

import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_ZIP = ROOT / "ORBITL1-AX25_Phases1-4_Release.zip"

EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "ORBITL1-AX25",  # nested duplicate clone
    "ORBITL1-AX25_Phases1-4_Release",
}

EXCLUDE_EXTS = {
    ".pyc",
    ".pyo",
    ".pyd",
}


def package_release():
    print(f"Creating release package: {RELEASE_ZIP}")
    with zipfile.ZipFile(RELEASE_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in sorted(os.walk(ROOT)):
            rel_dir = os.path.relpath(dirpath, ROOT)
            path_parts = set(rel_dir.split(os.sep))

            # Skip excluded directories
            if any(p in EXCLUDE_DIRS for p in path_parts):
                continue

            # In-place remove from dirnames so os.walk doesn't descend into them
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

            for fname in sorted(filenames):
                if fname == RELEASE_ZIP.name:
                    continue
                if any(fname.endswith(ext) for ext in EXCLUDE_EXTS):
                    continue

                full_path = os.path.join(dirpath, fname)
                arc_name = os.path.relpath(full_path, ROOT)
                zf.write(full_path, arc_name)
                print(f"  Added: {arc_name}")

    size_bytes = RELEASE_ZIP.stat().st_size
    print(f"\nRelease package successfully created:")
    print(f"  Path: {RELEASE_ZIP}")
    print(f"  Size: {size_bytes} bytes ({size_bytes / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    package_release()
