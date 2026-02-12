import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Add src to sys.path so we can import 'responseiq' directly
sys.path.insert(0, str(ROOT / "src"))

# Use in-memory SQLite for unit tests by default
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
