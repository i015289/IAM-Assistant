"""Make scripts/ importable for all tests in tests/scripts/."""
from __future__ import annotations

import sys
from pathlib import Path

# Repo root is two parents above this conftest (tests/scripts/conftest.py)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
