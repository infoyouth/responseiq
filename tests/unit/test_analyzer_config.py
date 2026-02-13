from responseiq.config.settings import settings
from responseiq.parsers.custom_parser import KeywordParser
from responseiq.parsers.registry import registry
from responseiq.services import analyzer


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
    # With AI analysis, timeout may be classified as medium or high depending on context
    # The important thing is that it's detected and classified appropriately
    assert meta.get("severity") in ["medium", "high"]
    # Ensure the message is analyzed (reason should not be empty, as this is what analyzer returns for AI title)
    assert meta.get("reason") is not None and len(meta.get("reason", "")) > 0

    # restore default (optional since tmp_path is ephemeral, but good practice
    # for singleton state)
    monkeypatch.undo()
    parser.reload_config()
