from responseiq.services.analyzer import analyze_log


def test_analyzer_detects_oomkilled():
    res = analyze_log("kernel: process killed: oomkilled due to memory")
    assert res is not None
    assert res.title == "Rule: OOMKilled"


def test_analyzer_no_detection():
    res = analyze_log("all good log message")
    assert res is None
