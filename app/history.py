from app.models import RiskLevel


class InMemoryHistoryStore:
    def __init__(self) -> None:
        self._risk_by_instance: dict[str, RiskLevel] = {}

    async def risk_for(self, instance_id: str) -> RiskLevel:
        if "risk" in instance_id.lower() or "xid" in instance_id.lower():
            return RiskLevel.HIGH
        if "unknown" in instance_id.lower() or "warn" in instance_id.lower():
            return RiskLevel.MEDIUM
        return self._risk_by_instance.get(instance_id, RiskLevel.LOW)

    async def record_instance_risk(self, instance_id: str, risk_level: RiskLevel) -> None:
        self._risk_by_instance[instance_id] = risk_level


history_store = InMemoryHistoryStore()
