import sys
from pathlib import Path

# Ensure repository root (one level up from tests) is on sys.path so `src` imports work during tests
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
