# GPU Fleet Health Report: gpu-check-2026-06-02

Decision: `FAIL`
Profile: `distributed-gpu`
Created: `2026-06-02T21:30:42.331249+00:00`

2 of 2 instance(s) failed pre-flight checks for job gpu-check-2026-06-02.

Recommended action: Block job submission, quarantine failed nodes, and select replacement capacity.

## Instance Results

### i-086d21b7ed6e3aaa6: `FAIL`
Risk: `LOW`
Check depth: `PHASE_1_FAST`
Action: Block job submission and quarantine or replace the failed node.

- `instance_state` FAIL: observed `terminated`; expected `running`; EC2 DescribeInstances returned the instance lifecycle state.
  Remediation: Start or replace this instance before scheduling the job.
- `ec2_status` FAIL: observed `state=terminated, system=not-applicable, instance=not-applicable`; expected `state=running, system=ok, instance=ok`; EC2 DescribeInstanceStatus returned AWS system and instance status checks.
  Remediation: Wait for EC2 status checks to pass or replace this instance.
- `ssm_managed` WARN: observed `not managed`; expected `online`; SSM DescribeInstanceInformation did not return this instance.
  Remediation: Attach an SSM-capable instance profile and ensure the SSM agent can reach SSM endpoints.
- `gpu_count` FAIL: observed `1`; expected `8`; GPU count was inferred from EC2 instance type g5.xlarge; SSM probe was unavailable.
  Remediation: Choose an instance type with the expected GPU count or update the job profile.
- `efa_available` FAIL: observed `missing`; expected `present`; EC2 network interfaces reported: none.
  Remediation: Launch with an EFA-enabled network interface for distributed GPU jobs.
- `fsx_mount` WARN: observed `not probed`; expected `responsive`; FSx mount requires an in-instance probe; AWS fast mode only checked EC2 metadata.
  Remediation: Enable SSM or another in-instance execution path for this check.
- `recent_xid` WARN: observed `not probed`; expected `no recent critical XID`; GPU XID history requires an SSM in-instance log probe, but this instance is not online in SSM.
  Remediation: Enable SSM or another in-instance execution path for this check.
- `nvlink_status` WARN: observed `not probed`; expected `active`; NVLink status requires an in-instance GPU probe; AWS fast mode did not run nvidia-smi.
  Remediation: Enable SSM or another in-instance execution path for this check.

### i-06ac0cdfca64c2d72: `FAIL`
Risk: `LOW`
Check depth: `PHASE_1_FAST`
Action: Block job submission and quarantine or replace the failed node.

- `instance_state` FAIL: observed `terminated`; expected `running`; EC2 DescribeInstances returned the instance lifecycle state.
  Remediation: Start or replace this instance before scheduling the job.
- `ec2_status` FAIL: observed `state=terminated, system=not-applicable, instance=not-applicable`; expected `state=running, system=ok, instance=ok`; EC2 DescribeInstanceStatus returned AWS system and instance status checks.
  Remediation: Wait for EC2 status checks to pass or replace this instance.
- `ssm_managed` WARN: observed `not managed`; expected `online`; SSM DescribeInstanceInformation did not return this instance.
  Remediation: Attach an SSM-capable instance profile and ensure the SSM agent can reach SSM endpoints.
- `gpu_count` FAIL: observed `1`; expected `8`; GPU count was inferred from EC2 instance type g5.xlarge; SSM probe was unavailable.
  Remediation: Choose an instance type with the expected GPU count or update the job profile.
- `efa_available` FAIL: observed `missing`; expected `present`; EC2 network interfaces reported: none.
  Remediation: Launch with an EFA-enabled network interface for distributed GPU jobs.
- `fsx_mount` WARN: observed `not probed`; expected `responsive`; FSx mount requires an in-instance probe; AWS fast mode only checked EC2 metadata.
  Remediation: Enable SSM or another in-instance execution path for this check.
- `recent_xid` WARN: observed `not probed`; expected `no recent critical XID`; GPU XID history requires an SSM in-instance log probe, but this instance is not online in SSM.
  Remediation: Enable SSM or another in-instance execution path for this check.
- `nvlink_status` WARN: observed `not probed`; expected `active`; NVLink status requires an in-instance GPU probe; AWS fast mode did not run nvidia-smi.
  Remediation: Enable SSM or another in-instance execution path for this check.
