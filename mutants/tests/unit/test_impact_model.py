from responseiq.services.impact import assess_impact, infer_affected_surface


def test_infer_affected_surface_env_wide():
    assert infer_affected_surface("critical outage across cluster namespace") == "env_wide"


def test_impact_score_critical_higher_than_medium():
    critical = assess_impact(severity="critical", title="panic", description="service panic")
    medium = assess_impact(severity="medium", title="timeout", description="single timeout")

    assert critical.score > medium.score


def test_impact_score_increases_with_recurrence():
    first = assess_impact(severity="high", title="error", description="upstream 502", recurrence=1)
    repeated = assess_impact(severity="high", title="error", description="upstream 502", recurrence=4)

    assert repeated.score > first.score


def test_impact_factors_are_present():
    assessed = assess_impact(severity="high", source="ai", recurrence=2)

    assert assessed.factors["severity"] == "high"
    assert assessed.factors["recurrence"] == 2
    assert assessed.factors["source"] == "ai"
