from typing import List, Optional, TypedDict


class AgentState(TypedDict, total=False):
    attempt_history: List[str]
    retry_count: int
    incident_id: str
    investigation_report: Optional[str]
    current_patch: Optional[str]
    last_verification: Optional[str]
    status: Optional[str]
    trace_id: Optional[str]
    context: Optional[dict]
