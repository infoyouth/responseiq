import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Use in-memory SQLite for unit tests by default
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
