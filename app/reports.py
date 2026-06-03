import json
from datetime import datetime, timezone
from pathlib import Path

from app.models import Decision, JobHealthDecision


def build_summary(job_id: str, decision: Decision, total: int, failed: int, warned: int) -> str:
    if decision == Decision.FAIL:
        return f"{failed} of {total} instance(s) failed pre-flight checks for job {job_id}."
    if decision == Decision.WARN:
        return f"{warned} of {total} instance(s) produced warnings for job {job_id}."
    return f"All {total} instance(s) passed pre-flight checks for job {job_id}."


def build_markdown_report(decision: JobHealthDecision) -> str:
    lines = [
        f"# GPU Fleet Health Report: {decision.job_id}",
        "",
        f"Decision: `{decision.decision}`",
        f"Profile: `{decision.profile}`",
        f"Created: `{decision.created_at.isoformat()}`",
        "",
        decision.summary,
        "",
        f"Recommended action: {decision.recommended_action}",
        "",
        "## Instance Results",
    ]

    for instance in decision.instances:
        lines.extend(
            [
                "",
                f"### {instance.instance_id}: `{instance.status}`",
                f"Risk: `{instance.risk_level}`",
                f"Check depth: `{instance.check_depth}`",
            ]
        )
        if instance.recommended_action:
            lines.append(f"Action: {instance.recommended_action}")
        lines.append("")
        for check in instance.checks:
            expected = f" expected `{check.expected}`;" if check.expected is not None else ""
            lines.append(
                f"- `{check.check_name}` {check.status}: observed `{check.observed}`;"
                f"{expected} {check.evidence}"
            )
            if check.remediation:
                lines.append(f"  Remediation: {check.remediation}")

    return "\n".join(lines) + "\n"


def write_local_reports(decision: JobHealthDecision, report_dir: str) -> JobHealthDecision:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    job_dir = Path(report_dir) / decision.job_id / timestamp
    job_dir.mkdir(parents=True, exist_ok=True)

    json_path = job_dir / "decision.json"
    markdown_path = job_dir / "report.md"
    json_path.write_text(decision.model_dump_json(indent=2), encoding="utf-8")
    markdown_path.write_text(decision.report_markdown, encoding="utf-8")

    return decision.model_copy(update={"report_uri": str(markdown_path)})
