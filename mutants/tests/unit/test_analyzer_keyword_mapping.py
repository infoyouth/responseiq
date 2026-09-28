from responseiq.services.analyzer import analyze_log, analyze_message


def test_simple_keyword_severity_mapping():
    # panic/critical -> high
    for m in (
        "panic: something broke",
        "critical failure occurred",
    ):
        meta = analyze_message(m)
        assert meta is not None
        assert meta.get("severity") == "high"

    # error/failed -> medium
    for m in (
        "An error occurred",
        "operation failed due to X",
    ):
        meta = analyze_message(m)
        assert meta is not None
        assert meta.get("severity") == "medium"


def test_event_keyword_mapping():
    # event-level analyzer should map oomkilled and crashloop to high
    res = analyze_log("kernel: process killed: oomkilled due to memory")
    assert res is not None
    assert res.severity == "high"

    res2 = analyze_log("container is in crashloop: crashloop backoff")
    assert res2 is not None
    assert res2.severity == "high"
