from app.aws_tools import collect_aws_checks
from app.history import InMemoryHistoryStore, history_store
from app.mock_collectors import collect_mock_checks
from app.models import Decision, JobHealthDecision, PreflightRequest, RiskLevel
from app.profiles import load_profile
from app.reports import build_markdown_report, build_summary, write_local_reports
from app.rules import aggregate, aggregate_recommendation, classify_instance


async def run_preflight(
    request: PreflightRequest,
    report_dir: str = "reports",
    store: InMemoryHistoryStore = history_store,
    aws_profile: str | None = None,
    aws_region: str | None = None,
) -> JobHealthDecision:
    profile = load_profile(request.profile)
    instance_reports = []

    for instance_id in request.instance_ids:
        risk_level = await store.risk_for(instance_id)
        if request.mode == "aws":
            checks = await collect_aws_checks(
                instance_id,
                profile,
                aws_profile=aws_profile,
                aws_region=aws_region,
            )
        else:
            checks = collect_mock_checks(instance_id, profile)
        instance_report = classify_instance(instance_id, checks, risk_level)
        await store.record_instance_risk(instance_id, _risk_after_decision(instance_report.status, risk_level))
        instance_reports.append(instance_report)

    decision, counts = aggregate(instance_reports)
    summary = build_summary(
        request.job_id,
        decision,
        total=len(instance_reports),
        failed=counts.failed,
        warned=counts.warned,
    )

    job_decision = JobHealthDecision(
        job_id=request.job_id,
        profile=profile.name,
        decision=decision,
        summary=summary,
        aggregate_counts=counts,
        instances=instance_reports,
        recommended_action=aggregate_recommendation(decision),
        report_markdown="",
    )
    job_decision = job_decision.model_copy(
        update={"report_markdown": build_markdown_report(job_decision)}
    )
    return write_local_reports(job_decision, report_dir)


def _risk_after_decision(decision: Decision, current: RiskLevel) -> RiskLevel:
    if decision == Decision.FAIL:
        return RiskLevel.HIGH
    if decision == Decision.WARN and current == RiskLevel.LOW:
        return RiskLevel.MEDIUM
    return current
