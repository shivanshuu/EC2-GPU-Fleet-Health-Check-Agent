# GPU Fleet Health Report: gpu-check-2026-06-02

Decision: `FAIL`
Profile: `distributed-gpu`
Created: `2026-06-02T21:53:24.301019+00:00`

2 of 2 instance(s) failed pre-flight checks for job gpu-check-2026-06-02.

Recommended action: Block job submission, quarantine failed nodes, and select replacement capacity.

## Instance Results

### i-026ef43f062c113ec: `FAIL`
Risk: `LOW`
Check depth: `PHASE_1_FAST`
Action: Block job submission and quarantine or replace the failed node.

- `instance_state` PASS: observed `running`; expected `running`; EC2 DescribeInstances returned the instance lifecycle state.
- `ec2_status` PASS: observed `state=running, system=ok, instance=ok`; expected `state=running, system=ok, instance=ok`; EC2 DescribeInstanceStatus returned AWS system and instance status checks.
- `ssm_managed` PASS: observed `Online`; expected `Online`; SSM DescribeInstanceInformation returned the managed-instance ping status.
- `gpu_count` PASS: observed `4`; expected `4`; SSM probe ran nvidia-smi -L inside the instance.
- `efa_available` FAIL: observed `missing`; expected `EFA NIC attached and fi_info -p efa succeeds`; EC2 network interfaces reported: interface.
  Remediation: Launch with an EFA-enabled network interface for distributed GPU jobs.
- `fsx_mount` WARN: observed `not probed`; expected `responsive`; FSx mount requires an in-instance probe; AWS fast mode only checked EC2 metadata.
  Remediation: Enable SSM or another in-instance execution path for this check.
- `recent_xid` PASS: observed `0 recent XID event(s)`; expected `no recent critical XID`; SSM probe scanned recent kernel logs for NVIDIA XID messages.
- `nvlink_status` WARN: observed `not probed`; expected `active`; NVLink status requires an in-instance GPU probe; AWS fast mode did not run nvidia-smi.
  Remediation: Enable SSM or another in-instance execution path for this check.

### i-0f164d2d2c8552028: `FAIL`
Risk: `LOW`
Check depth: `PHASE_1_FAST`
Action: Block job submission and quarantine or replace the failed node.

- `instance_state` PASS: observed `running`; expected `running`; EC2 DescribeInstances returned the instance lifecycle state.
- `ec2_status` PASS: observed `state=running, system=ok, instance=ok`; expected `state=running, system=ok, instance=ok`; EC2 DescribeInstanceStatus returned AWS system and instance status checks.
- `ssm_managed` PASS: observed `Online`; expected `Online`; SSM DescribeInstanceInformation returned the managed-instance ping status.
- `gpu_count` PASS: observed `4`; expected `4`; SSM probe ran nvidia-smi -L inside the instance.
- `efa_available` FAIL: observed `missing`; expected `EFA NIC attached and fi_info -p efa succeeds`; EC2 network interfaces reported: interface.
  Remediation: Launch with an EFA-enabled network interface for distributed GPU jobs.
- `fsx_mount` WARN: observed `not probed`; expected `responsive`; FSx mount requires an in-instance probe; AWS fast mode only checked EC2 metadata.
  Remediation: Enable SSM or another in-instance execution path for this check.
- `recent_xid` PASS: observed `0 recent XID event(s)`; expected `no recent critical XID`; SSM probe scanned recent kernel logs for NVIDIA XID messages.
- `nvlink_status` WARN: observed `not probed`; expected `active`; NVLink status requires an in-instance GPU probe; AWS fast mode did not run nvidia-smi.
  Remediation: Enable SSM or another in-instance execution path for this check.
