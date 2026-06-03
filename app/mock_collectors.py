from app.models import CheckStatus, HealthCheckResult, JobProfile, Severity


def collect_mock_checks(instance_id: str, profile: JobProfile) -> list[HealthCheckResult]:
    scenario = _scenario_for(instance_id)

    if scenario == "missing_gpu":
        visible_gpus = max(profile.expected_gpu_count - 1, 0)
    else:
        visible_gpus = profile.expected_gpu_count

    checks = [
        HealthCheckResult(
            instance_id=instance_id,
            check_name="ec2_status",
            status=CheckStatus.FAIL if scenario == "ec2_status_failed" else CheckStatus.PASS,
            severity=Severity.CRITICAL if scenario == "ec2_status_failed" else Severity.INFO,
            observed="failed" if scenario == "ec2_status_failed" else "ok",
            expected="ok",
            evidence="Mock EC2 instance and system status checks were evaluated.",
            remediation="Replace or stop scheduling this instance until EC2 status recovers."
            if scenario == "ec2_status_failed"
            else None,
        ),
        HealthCheckResult(
            instance_id=instance_id,
            check_name="gpu_count",
            status=CheckStatus.FAIL if visible_gpus != profile.expected_gpu_count else CheckStatus.PASS,
            severity=Severity.CRITICAL if visible_gpus != profile.expected_gpu_count else Severity.INFO,
            observed=str(visible_gpus),
            expected=str(profile.expected_gpu_count),
            evidence=f"nvidia-smi -L returned {visible_gpus} GPU device(s).",
            remediation="Quarantine node and request replacement before distributed training."
            if visible_gpus != profile.expected_gpu_count
            else None,
        ),
    ]

    if profile.requires_efa:
        checks.append(
            HealthCheckResult(
                instance_id=instance_id,
                check_name="efa_available",
                status=CheckStatus.FAIL if scenario == "efa_failed" else CheckStatus.PASS,
                severity=Severity.CRITICAL if scenario == "efa_failed" else Severity.INFO,
                observed="missing" if scenario == "efa_failed" else "present",
                expected="present",
                evidence="fi_info -p efa returned the mock EFA availability result.",
                remediation="Repair EFA driver/configuration or replace node."
                if scenario == "efa_failed"
                else None,
            )
        )

    if profile.requires_fsx:
        checks.append(
            HealthCheckResult(
                instance_id=instance_id,
                check_name="fsx_mount",
                status=CheckStatus.FAIL if scenario == "fsx_failed" else CheckStatus.PASS,
                severity=Severity.CRITICAL if scenario == "fsx_failed" else Severity.INFO,
                observed="unavailable" if scenario == "fsx_failed" else "responsive",
                expected="responsive",
                evidence="Mock mount probe checked FSx path responsiveness.",
                remediation="Restore FSx mount before scheduling this job."
                if scenario == "fsx_failed"
                else None,
            )
        )

    if profile.block_on_recent_critical_xid:
        checks.append(
            HealthCheckResult(
                instance_id=instance_id,
                check_name="recent_xid",
                status=_xid_status(scenario),
                severity=_xid_severity(scenario),
                observed=_xid_observed(scenario),
                expected="no recent critical XID",
                evidence=_xid_evidence(scenario),
                remediation="Quarantine node and inspect GPU/PCIe health."
                if scenario == "recent_xid"
                else None,
            )
        )

    if profile.requires_nvlink:
        checks.append(
            HealthCheckResult(
                instance_id=instance_id,
                check_name="nvlink_status",
                status=CheckStatus.PASS,
                severity=Severity.INFO,
                observed="active",
                expected="active",
                evidence="Mock NVLink probe reports active links.",
            )
        )

    return checks


def _scenario_for(instance_id: str) -> str:
    lowered = instance_id.lower()
    if "badgpu" in lowered or "missing-gpu" in lowered or lowered.endswith("123"):
        return "missing_gpu"
    if "efa" in lowered:
        return "efa_failed"
    if "fsx" in lowered:
        return "fsx_failed"
    if "xid" in lowered:
        return "recent_xid"
    if "warn" in lowered:
        return "old_xid_warning"
    if "ec2fail" in lowered:
        return "ec2_status_failed"
    return "healthy"


def _xid_status(scenario: str) -> CheckStatus:
    if scenario == "recent_xid":
        return CheckStatus.FAIL
    if scenario == "old_xid_warning":
        return CheckStatus.WARN
    return CheckStatus.PASS


def _xid_severity(scenario: str) -> Severity:
    if scenario == "recent_xid":
        return Severity.CRITICAL
    if scenario == "old_xid_warning":
        return Severity.WARNING
    return Severity.INFO


def _xid_observed(scenario: str) -> str:
    if scenario == "recent_xid":
        return "recent XID 79"
    if scenario == "old_xid_warning":
        return "old noncritical XID"
    return "none"


def _xid_evidence(scenario: str) -> str:
    if scenario == "recent_xid":
        return "Mock kernel log contains recent NVRM Xid 79 GPU fell off bus event."
    if scenario == "old_xid_warning":
        return "Mock kernel log contains an old noncritical XID outside the block window."
    return "Mock kernel log contains no critical XID events."
