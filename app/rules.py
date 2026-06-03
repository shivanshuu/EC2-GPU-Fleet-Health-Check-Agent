from app.models import (
    AggregateCounts,
    CheckDepth,
    CheckStatus,
    Decision,
    HealthCheckResult,
    InstanceHealthReport,
    RiskLevel,
)


def classify_instance(
    instance_id: str,
    checks: list[HealthCheckResult],
    risk_level: RiskLevel = RiskLevel.LOW,
) -> InstanceHealthReport:
    status = Decision.GO
    if any(check.status == CheckStatus.FAIL for check in checks):
        status = Decision.FAIL
    elif any(check.status == CheckStatus.WARN for check in checks):
        status = Decision.WARN

    return InstanceHealthReport(
        instance_id=instance_id,
        status=status,
        risk_level=risk_level,
        check_depth=check_depth_for_risk(risk_level),
        checks=checks,
        recommended_action=recommended_action(status),
    )


def aggregate(instances: list[InstanceHealthReport]) -> tuple[Decision, AggregateCounts]:
    counts = AggregateCounts(
        passed=sum(1 for instance in instances if instance.status == Decision.GO),
        warned=sum(1 for instance in instances if instance.status == Decision.WARN),
        failed=sum(1 for instance in instances if instance.status == Decision.FAIL),
    )

    if counts.failed:
        return Decision.FAIL, counts
    if counts.warned:
        return Decision.WARN, counts
    return Decision.GO, counts


def check_depth_for_risk(risk_level: RiskLevel) -> CheckDepth:
    if risk_level == RiskLevel.HIGH:
        return CheckDepth.FULL_PHASE_2
    if risk_level == RiskLevel.MEDIUM:
        return CheckDepth.PHASE_2_LIGHT
    return CheckDepth.PHASE_1_FAST


def recommended_action(status: Decision) -> str | None:
    if status == Decision.FAIL:
        return "Block job submission and quarantine or replace the failed node."
    if status == Decision.WARN:
        return "Allow only with operator visibility; consider a standard check first."
    return None


def aggregate_recommendation(decision: Decision) -> str:
    if decision == Decision.FAIL:
        return "Block job submission, quarantine failed nodes, and select replacement capacity."
    if decision == Decision.WARN:
        return "Proceed only if the risk is acceptable; run standard checks for high-value jobs."
    return "Proceed with job submission."
