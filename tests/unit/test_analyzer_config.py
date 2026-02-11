from src.config.settings import settings
from src.parsers.custom_parser import KeywordParser
from src.parsers.registry import registry
from src.services import analyzer


def test_reload_config_and_mapping(tmp_path, monkeypatch):
    cfg = tmp_path / "k.json"
    cfg.write_text('{"simple": ["timeout"], "events": {}, ' '"mapping": {"high": ["timeout"]}}')

    # Patch settings to point to our temp file
    monkeypatch.setattr(settings, "keywords_config_path", cfg)

    # Find the parser and reload
    parser = next(p for p in registry.get_parsers() if isinstance(p, KeywordParser))
    parser.reload_config()

    meta = analyzer.analyze_message("Service timeout occurred")
    assert meta is not None
    assert meta.get("severity") == "high"

    # restore default (optional since tmp_path is ephemeral, but good practice
    # for singleton state)
    monkeypatch.undo()
    parser.reload_config()
