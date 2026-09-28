from responseiq.app import _build_incident_outputs
from responseiq.models import Incident


def _incident(incident_id: int, severity: str, description: str, source: str = "ai") -> Incident:
    return Incident(id=incident_id, log_id=incident_id, severity=severity, description=description, source=source)


def test_incidents_are_sorted_by_impact_descending():
    items = [
        _incident(1, "medium", "single timeout on one service", "rule-engine"),
        _incident(2, "critical", "cluster-wide panic affecting namespace", "ai"),
        _incident(3, "high", "upstream dependency failures across services", "ai"),
    ]

    outputs = _build_incident_outputs(items)

    assert len(outputs) == 3
    assert outputs[0].severity == "critical"
    assert (outputs[0].impact_score or 0) >= (outputs[1].impact_score or 0)
    assert (outputs[1].impact_score or 0) >= (outputs[2].impact_score or 0)
    assert outputs[0].impact_factors is not None
