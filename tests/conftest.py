import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Add src to sys.path so we can import 'responseiq' directly
sys.path.insert(0, str(ROOT / "src"))

# Use in-memory SQLite for unit tests by default
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

# Ensure tests always use mock LLM, never a real external endpoint.
# This overrides any .env file that may point to Ollama/OpenAI,
# so tests are deterministic and work offline.
# Individual tests that need real LLM behaviour must patch settings explicitly.
os.environ["LLM_BASE_URL"] = ""
os.environ.pop("OPENAI_API_KEY", None)
