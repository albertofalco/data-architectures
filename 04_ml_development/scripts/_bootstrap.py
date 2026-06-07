"""Script bootstrap utilities."""

from __future__ import annotations
import sys
from pathlib import Path

def add_src_to_path() -> Path:
    """Add the module src directory to sys.path and return module root."""
    module_dir = Path(__file__).resolve().parents[1]
    src_dir = module_dir / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    return module_dir
