import os

# ensure test DB isolation doesn't matter here
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from src.services import analyzer


def test_reload_config_and_mapping(tmp_path):
    cfg = tmp_path / "k.json"
    cfg.write_text('{"simple": ["timeout"], "events": {}, "mapping": {"high": ["timeout"]}}')

    analyzer.reload_config(str(cfg))
    meta = analyzer.analyze_message("Service timeout occurred")
    assert meta is not None
    assert meta.get("severity") == "high"

    # restore default
    analyzer.reload_config(None)
