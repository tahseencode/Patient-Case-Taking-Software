"""Vercel entrypoint: exposes the FastAPI `app` from the project.

Put this file at  api/index.py  (repo root / api / index.py).
It looks for `app` in the root main.py first, then backend/main.py.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Make both the repo root and backend/ importable (root takes priority).
for p in (ROOT / "backend", ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def _load_module(path: Path):
    """Load a file by path so root main.py and backend/main.py don't clash."""
    spec = importlib.util.spec_from_file_location("_app_entry", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


app = None
_tried = []
for candidate in (ROOT / "main.py", ROOT / "backend" / "main.py"):
    _tried.append(str(candidate))
    if candidate.exists():
        module = _load_module(candidate)
        if hasattr(module, "app"):
            app = module.app
            break

if app is None:
    raise RuntimeError(
        "Could not find a FastAPI `app` object. Looked in: " + ", ".join(_tried)
    )