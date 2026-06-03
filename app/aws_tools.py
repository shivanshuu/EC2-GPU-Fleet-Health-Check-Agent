import asyncio
import json
import os
from typing import Any

from app.models import CheckStatus, HealthCheckResult, JobProfile, Severity


class AwsToolsUnavailable(RuntimeError):
    pass


async def collect_aws_checks(
    instance_id: str,
    profile: JobProfile,
    aws_profile: str | None = None,
    aws_region: str | None = None,
) -> list[HealthCheckResult]:
    instance = await _describe_instance(instance_id, aws_profile, aws_region)
    status = await _describe_instance_status(instance_id, aws_profile, aws_region)
    ssm_instance = await _describe_ssm_instance(instance_id, aws_profile, aws_region)
    should_probe_instance = (
        instance.get("State", {}).get("Name") == "running"
        and _ssm_is_online(ssm_instance)
    )
    ssm_probe = await _run_ssm_probe(
        instance_id,
        aws_profile,
        aws_region,
        timeout_seconds=profile.fast_check_timeout_seconds,
    ) if should_probe_instance else None

    checks = [
        _instance_state_check(instance_id, instance),
        _ec2_status_check(instance_id, instance, status),
        _ssm_status_check(instance_id, ssm_instance),
        _gpu_count_check(instance_id, instance, profile, ssm_probe),
    ]

    if profile.requires_efa:
        checks.append(_efa_check(instance_id, instance, ssm_probe))
    if profile.requires_fsx:
        checks.append(
            _unprobed_warning(
                instance_id,
                "fsx_mount",
                "responsive",
                "FSx mount requires an in-instance probe; AWS fast mode only checked EC2 metadata.",
            )
        )
    if profile.block_on_recent_critical_xid:
        checks.append(_recent_xid_check(instance_id, ssm_probe))
    if profile.requires_nvlink:
        checks.append(
            _unprobed_warning(
                instance_id,
                "nvlink_status",
                "active",
                "NVLink status requires an in-instance GPU probe; AWS fast mode did not run nvidia-smi.",
            )
        )

    return checks


async def _describe_instance(
    instance_id: str,
    aws_profile: str | None,
    aws_region: str | None,
) -> dict[str, Any]:
    payload = await _aws_json(
        [
            "ec2",
            "describe-instances",
            "--instance-ids",
            instance_id,
        ],
        aws_profile,
        aws_region,
    )
    instances = [
        instance
        for reservation in payload.get("Reservations", [])
        for instance in reservation.get("Instances", [])
    ]
    if not instances:
        raise AwsToolsUnavailable(f"EC2 instance {instance_id} was not found.")
    return instances[0]


async def _describe_instance_status(
    instance_id: str,
    aws_profile: str | None,
    aws_region: str | None,
) -> dict[str, Any] | None:
    payload = await _aws_json(
        [
            "ec2",
            "describe-instance-status",
            "--instance-ids",
            instance_id,
            "--include-all-instances",
        ],
        aws_profile,
        aws_region,
    )
    statuses = payload.get("InstanceStatuses", [])
    return statuses[0] if statuses else None


async def _describe_ssm_instance(
    instance_id: str,
    aws_profile: str | None,
    aws_region: str | None,
) -> dict[str, Any] | None:
    payload = await _aws_json(
        [
            "ssm",
            "describe-instance-information",
            "--filters",
            f"Key=InstanceIds,Values={instance_id}",
        ],
        aws_profile,
        aws_region,
    )
    instances = payload.get("InstanceInformationList", [])
    return instances[0] if instances else None


async def _run_ssm_probe(
    instance_id: str,
    aws_profile: str | None,
    aws_region: str | None,
    timeout_seconds: int,
) -> dict[str, str] | None:
    command = "\n".join(
        [
            "set +e",
            "if command -v nvidia-smi >/dev/null 2>&1; then",
            "  echo NVIDIA_SMI=present",
            "  echo GPU_COUNT=$(nvidia-smi -L 2>/dev/null | grep -c '^GPU ')",
            "  if nvidia-smi nvlink -s >/tmp/ec2check-nvlink.out 2>&1; then",
            "    echo NVLINK_STATUS=active",
            "  else",
            "    echo NVLINK_STATUS=unavailable",
            "  fi",
            "else",
            "  echo NVIDIA_SMI=missing",
            "  echo GPU_COUNT=unknown",
            "  echo NVLINK_STATUS=unavailable",
            "fi",
            "if command -v fi_info >/dev/null 2>&1; then",
            "  if timeout 8s fi_info -p efa >/tmp/ec2check-efa.out 2>&1; then",
            "    echo EFA_STATUS=available",
            "  else",
            "    echo EFA_STATUS=unavailable",
            "    echo EFA_DETAIL=$(tail -1 /tmp/ec2check-efa.out 2>/dev/null | tr '=' ':')",
            "  fi",
            "else",
            "  echo EFA_STATUS=fi_info_missing",
            "fi",
            "xid_log=$( (timeout 8s dmesg -T 2>/dev/null; timeout 8s journalctl -k --since '-24 hours' --no-pager 2>/dev/null) | grep -Ei 'NVRM:.*Xid|Xid' | tail -20 )",
            "if [ -n \"$xid_log\" ]; then",
            "  echo RECENT_XID_COUNT=$(printf '%s\\n' \"$xid_log\" | grep -c .)",
            "else",
            "  echo RECENT_XID_COUNT=0",
            "fi",
        ]
    )
    payload = await _aws_json(
        [
            "ssm",
            "send-command",
            "--instance-ids",
            instance_id,
            "--document-name",
            "AWS-RunShellScript",
            "--comment",
            "EC2Check GPU health probe",
            "--parameters",
            json.dumps({"commands": [command]}),
        ],
        aws_profile,
        aws_region,
    )
    command_id = payload.get("Command", {}).get("CommandId")
    if not command_id:
        raise AwsToolsUnavailable("SSM SendCommand did not return a CommandId.")

    deadline = asyncio.get_running_loop().time() + timeout_seconds
    last_payload: dict[str, Any] | None = None
    while asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(2)
        try:
            last_payload = await _aws_json(
                [
                    "ssm",
                    "get-command-invocation",
                    "--command-id",
                    command_id,
                    "--instance-id",
                    instance_id,
                ],
                aws_profile,
                aws_region,
            )
        except AwsToolsUnavailable as exc:
            if "timed out" in str(exc):
                return {
                    "SSM_PROBE_STATUS": "TimedOut",
                    "SSM_PROBE_ERROR": str(exc),
                }
            continue

        invocation_status = last_payload.get("Status")
        if invocation_status == "Success":
            return _parse_probe_output(last_payload.get("StandardOutputContent", ""))
        if invocation_status in {"Cancelled", "Failed", "TimedOut", "Cancelling"}:
            return {
                "SSM_PROBE_STATUS": invocation_status,
                "SSM_PROBE_ERROR": last_payload.get("StandardErrorContent", "").strip(),
            }

    return {
        "SSM_PROBE_STATUS": "TimedOut",
        "SSM_PROBE_ERROR": f"SSM probe did not finish within {timeout_seconds} seconds.",
    }


async def _aws_json(
    args: list[str],
    aws_profile: str | None,
    aws_region: str | None,
) -> dict[str, Any]:
    command = ["aws", *args, "--output", "json"]
    if aws_profile:
        command.extend(["--profile", aws_profile])
    if aws_region and aws_region != "local":
        command.extend(["--region", aws_region])
    command.extend(["--cli-connect-timeout", "10", "--cli-read-timeout", "20"])

    env = os.environ.copy()
    env.pop("AWS_REGION", None)
    env.pop("AWS_DEFAULT_REGION", None)

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
    except FileNotFoundError as exc:
        raise AwsToolsUnavailable("AWS CLI is required for AWS mode.") from exc

    operation = " ".join(args[:2])
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
    except TimeoutError as exc:
        process.kill()
        raise AwsToolsUnavailable(f"AWS CLI command timed out while running: {operation}.") from exc
    if process.returncode != 0:
        message = stderr.decode("utf-8", errors="replace").strip()
        raise AwsToolsUnavailable(message or "AWS CLI command failed.")

    try:
        return json.loads(stdout.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise AwsToolsUnavailable("AWS CLI returned invalid JSON.") from exc


def _instance_state_check(instance_id: str, instance: dict[str, Any]) -> HealthCheckResult:
    state = instance.get("State", {}).get("Name", "unknown")
    is_running = state == "running"
    return HealthCheckResult(
        instance_id=instance_id,
        check_name="instance_state",
        status=CheckStatus.PASS if is_running else CheckStatus.FAIL,
        severity=Severity.INFO if is_running else Severity.CRITICAL,
        observed=state,
        expected="running",
        evidence="EC2 DescribeInstances returned the instance lifecycle state.",
        remediation="Start or replace this instance before scheduling the job."
        if not is_running
        else None,
    )


def _ec2_status_check(
    instance_id: str,
    instance: dict[str, Any],
    status: dict[str, Any] | None,
) -> HealthCheckResult:
    state = instance.get("State", {}).get("Name", "unknown")
    system_status = _status_value(status, "SystemStatus")
    instance_status = _status_value(status, "InstanceStatus")
    observed = f"state={state}, system={system_status}, instance={instance_status}"

    passed = state == "running" and system_status == "ok" and instance_status == "ok"
    severity = Severity.INFO if passed else Severity.CRITICAL
    return HealthCheckResult(
        instance_id=instance_id,
        check_name="ec2_status",
        status=CheckStatus.PASS if passed else CheckStatus.FAIL,
        severity=severity,
        observed=observed,
        expected="state=running, system=ok, instance=ok",
        evidence="EC2 DescribeInstanceStatus returned AWS system and instance status checks.",
        remediation="Wait for EC2 status checks to pass or replace this instance."
        if not passed
        else None,
    )


def _ssm_status_check(
    instance_id: str,
    ssm_instance: dict[str, Any] | None,
) -> HealthCheckResult:
    if not ssm_instance:
        return HealthCheckResult(
            instance_id=instance_id,
            check_name="ssm_managed",
            status=CheckStatus.WARN,
            severity=Severity.WARNING,
            observed="not managed",
            expected="online",
            evidence="SSM DescribeInstanceInformation did not return this instance.",
            remediation="Attach an SSM-capable instance profile and ensure the SSM agent can reach SSM endpoints.",
        )

    ping_status = ssm_instance.get("PingStatus", "unknown")
    is_online = ping_status == "Online"
    return HealthCheckResult(
        instance_id=instance_id,
        check_name="ssm_managed",
        status=CheckStatus.PASS if is_online else CheckStatus.WARN,
        severity=Severity.INFO if is_online else Severity.WARNING,
        observed=ping_status,
        expected="Online",
        evidence="SSM DescribeInstanceInformation returned the managed-instance ping status.",
        remediation="Restore SSM agent connectivity before running in-instance probes."
        if not is_online
        else None,
    )


def _gpu_count_check(
    instance_id: str,
    instance: dict[str, Any],
    profile: JobProfile,
    ssm_probe: dict[str, str] | None,
) -> HealthCheckResult:
    instance_type = instance.get("InstanceType", "unknown")
    if ssm_probe and ssm_probe.get("GPU_COUNT") not in {None, "unknown"}:
        observed = ssm_probe["GPU_COUNT"]
        matches = observed == str(profile.expected_gpu_count)
        return HealthCheckResult(
            instance_id=instance_id,
            check_name="gpu_count",
            status=CheckStatus.PASS if matches else CheckStatus.FAIL,
            severity=Severity.INFO if matches else Severity.CRITICAL,
            observed=observed,
            expected=str(profile.expected_gpu_count),
            evidence="SSM probe ran nvidia-smi -L inside the instance.",
            remediation="Quarantine node and inspect nvidia-smi output before scheduling."
            if not matches
            else None,
        )

    gpu_count = infer_gpu_count(instance_type)
    if gpu_count is None:
        return HealthCheckResult(
            instance_id=instance_id,
            check_name="gpu_count",
            status=CheckStatus.WARN,
            severity=Severity.WARNING,
            observed=f"unknown for {instance_type}",
            expected=str(profile.expected_gpu_count),
            evidence="GPU count could not be probed through SSM and could not be inferred from the EC2 instance type.",
            remediation="Run an in-instance GPU probe with nvidia-smi before scheduling.",
        )

    matches = gpu_count == profile.expected_gpu_count
    return HealthCheckResult(
        instance_id=instance_id,
        check_name="gpu_count",
        status=CheckStatus.PASS if matches else CheckStatus.FAIL,
        severity=Severity.INFO if matches else Severity.CRITICAL,
        observed=str(gpu_count),
        expected=str(profile.expected_gpu_count),
        evidence=f"GPU count was inferred from EC2 instance type {instance_type}; SSM probe was unavailable.",
        remediation="Choose an instance type with the expected GPU count or update the job profile."
        if not matches
        else None,
    )


def _efa_check(
    instance_id: str,
    instance: dict[str, Any],
    ssm_probe: dict[str, str] | None,
) -> HealthCheckResult:
    interface_types = [
        interface.get("InterfaceType", "interface")
        for interface in instance.get("NetworkInterfaces", [])
    ]
    has_efa = "efa" in interface_types
    interface_evidence = f"EC2 network interfaces reported: {', '.join(interface_types) or 'none'}."
    if not has_efa:
        return HealthCheckResult(
            instance_id=instance_id,
            check_name="efa_available",
            status=CheckStatus.FAIL,
            severity=Severity.CRITICAL,
            observed="missing",
            expected="EFA NIC attached and fi_info -p efa succeeds",
            evidence=interface_evidence,
            remediation="Launch with an EFA-enabled network interface for distributed GPU jobs.",
        )

    if not ssm_probe:
        return HealthCheckResult(
            instance_id=instance_id,
            check_name="efa_available",
            status=CheckStatus.WARN,
            severity=Severity.WARNING,
            observed="attached; not functionally probed",
            expected="EFA NIC attached and fi_info -p efa succeeds",
            evidence=f"{interface_evidence} SSM probe was unavailable, so fi_info -p efa was not run.",
            remediation="Enable SSM in-instance probing to validate EFA functionality.",
        )

    if ssm_probe.get("SSM_PROBE_STATUS"):
        return HealthCheckResult(
            instance_id=instance_id,
            check_name="efa_available",
            status=CheckStatus.WARN,
            severity=Severity.WARNING,
            observed=ssm_probe["SSM_PROBE_STATUS"],
            expected="EFA NIC attached and fi_info -p efa succeeds",
            evidence=ssm_probe.get("SSM_PROBE_ERROR") or "SSM probe did not complete successfully.",
            remediation="Check SSM command execution and retry the EFA in-instance probe.",
        )

    efa_status = ssm_probe.get("EFA_STATUS", "unknown")
    if efa_status == "available":
        return HealthCheckResult(
            instance_id=instance_id,
            check_name="efa_available",
            status=CheckStatus.PASS,
            severity=Severity.INFO,
            observed="available",
            expected="EFA NIC attached and fi_info -p efa succeeds",
            evidence=f"{interface_evidence} SSM probe ran fi_info -p efa successfully.",
        )

    detail = ssm_probe.get("EFA_DETAIL")
    return HealthCheckResult(
        instance_id=instance_id,
        check_name="efa_available",
        status=CheckStatus.FAIL,
        severity=Severity.CRITICAL,
        observed=efa_status,
        expected="EFA NIC attached and fi_info -p efa succeeds",
        evidence=(
            f"{interface_evidence} SSM probe ran fi_info -p efa and it did not succeed."
            + (f" Last output: {detail}" if detail else "")
        ),
        remediation="Repair EFA/libfabric configuration or replace the node before distributed training.",
    )


def _unprobed_warning(
    instance_id: str,
    check_name: str,
    expected: str,
    evidence: str,
) -> HealthCheckResult:
    return HealthCheckResult(
        instance_id=instance_id,
        check_name=check_name,
        status=CheckStatus.WARN,
        severity=Severity.WARNING,
        observed="not probed",
        expected=expected,
        evidence=evidence,
        remediation="Enable SSM or another in-instance execution path for this check.",
    )


def _recent_xid_check(
    instance_id: str,
    ssm_probe: dict[str, str] | None,
) -> HealthCheckResult:
    if not ssm_probe:
        return _unprobed_warning(
            instance_id,
            "recent_xid",
            "no recent critical XID",
            "GPU XID history requires an SSM in-instance log probe, but this instance is not online in SSM.",
        )

    if ssm_probe.get("SSM_PROBE_STATUS"):
        return HealthCheckResult(
            instance_id=instance_id,
            check_name="recent_xid",
            status=CheckStatus.WARN,
            severity=Severity.WARNING,
            observed=ssm_probe["SSM_PROBE_STATUS"],
            expected="no recent critical XID",
            evidence=ssm_probe.get("SSM_PROBE_ERROR") or "SSM probe did not complete successfully.",
            remediation="Check SSM command execution and retry the in-instance probe.",
        )

    try:
        xid_count = int(ssm_probe.get("RECENT_XID_COUNT", "0") or "0")
    except ValueError:
        xid_count = 0
    has_xids = xid_count > 0
    return HealthCheckResult(
        instance_id=instance_id,
        check_name="recent_xid",
        status=CheckStatus.FAIL if has_xids else CheckStatus.PASS,
        severity=Severity.CRITICAL if has_xids else Severity.INFO,
        observed=f"{xid_count} recent XID event(s)",
        expected="no recent critical XID",
        evidence="SSM probe scanned recent kernel logs for NVIDIA XID messages.",
        remediation="Quarantine node and inspect GPU/PCIe health."
        if has_xids
        else None,
    )


def _status_value(status: dict[str, Any] | None, key: str) -> str:
    if status is None:
        return "not available"
    return status.get(key, {}).get("Status", "unknown")


def _ssm_is_online(ssm_instance: dict[str, Any] | None) -> bool:
    return bool(ssm_instance and ssm_instance.get("PingStatus") == "Online")


def _parse_probe_output(output: str) -> dict[str, str]:
    parsed = {}
    for line in output.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def infer_gpu_count(instance_type: str) -> int | None:
    g5_counts = {
        "g5.xlarge": 1,
        "g5.2xlarge": 1,
        "g5.4xlarge": 1,
        "g5.8xlarge": 1,
        "g5.12xlarge": 4,
        "g5.16xlarge": 1,
        "g5.24xlarge": 4,
        "g5.48xlarge": 8,
    }
    return g5_counts.get(instance_type)
