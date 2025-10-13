from src.blueprints import get_all, get


def test_loader_returns_blueprints():
    bps = get_all()
    assert isinstance(bps, list)
    assert any(bp.id == "crashloop_increase_memory" for bp in bps)


def test_get_specific_blueprint():
    bp = get("crashloop_increase_memory")
    assert bp is not None
    assert bp.id == "crashloop_increase_memory"
