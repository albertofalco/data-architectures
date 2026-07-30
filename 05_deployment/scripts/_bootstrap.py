"""Bootstrap helpers for deployment scripts."""

# ==================== IMPORTS ====================

from __future__ import annotations

import sys
from pathlib import Path


# ==================== HELPER FUNCTIONS ====================

def add_project_paths() -> Path:
    """Add repository and ML source paths to sys.path."""
    repo_root = Path(__file__).resolve().parents[2]
    ml_src = repo_root / "04_ml_development" / "src"
    scripts_dir = Path(__file__).resolve().parent
    for path in (repo_root, ml_src, scripts_dir):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    return repo_root
