# GPU Fleet Health Report: g5-ssm-probe-check

Decision: `FAIL`
Profile: `single-node-gpu`
Created: `2026-06-02T21:16:18.976094+00:00`

2 of 2 instance(s) failed pre-flight checks for job g5-ssm-probe-check.

Recommended action: Block job submission, quarantine failed nodes, and select replacement capacity.

## Instance Results

### i-086d21b7ed6e3aaa6: `FAIL`
Risk: `LOW`
Check depth: `PHASE_1_FAST`
Action: Block job submission and quarantine or replace the failed node.

- `instance_state` FAIL: observed `shutting-down`; expected `running`; EC2 DescribeInstances returned the instance lifecycle state.
  Remediation: Start or replace this instance before scheduling the job.
- `ec2_status` FAIL: observed `state=shutting-down, system=not-applicable, instance=not-applicable`; expected `state=running, system=ok, instance=ok`; EC2 DescribeInstanceStatus returned AWS system and instance status checks.
  Remediation: Wait for EC2 status checks to pass or replace this instance.
- `ssm_managed` PASS: observed `Online`; expected `Online`; SSM DescribeInstanceInformation returned the managed-instance ping status.
- `gpu_count` PASS: observed `1`; expected `1`; GPU count was inferred from EC2 instance type g5.xlarge; SSM probe was unavailable.
- `recent_xid` WARN: observed `TimedOut`; expected `no recent critical XID`; SSM probe did not finish within 30 seconds.
  Remediation: Check SSM command execution and retry the in-instance probe.

### i-06ac0cdfca64c2d72: `FAIL`
Risk: `LOW`
Check depth: `PHASE_1_FAST`
Action: Block job submission and quarantine or replace the failed node.

- `instance_state` FAIL: observed `shutting-down`; expected `running`; EC2 DescribeInstances returned the instance lifecycle state.
  Remediation: Start or replace this instance before scheduling the job.
- `ec2_status` FAIL: observed `state=shutting-down, system=not-applicable, instance=not-applicable`; expected `state=running, system=ok, instance=ok`; EC2 DescribeInstanceStatus returned AWS system and instance status checks.
  Remediation: Wait for EC2 status checks to pass or replace this instance.
- `ssm_managed` PASS: observed `Online`; expected `Online`; SSM DescribeInstanceInformation returned the managed-instance ping status.
- `gpu_count` PASS: observed `1`; expected `1`; GPU count was inferred from EC2 instance type g5.xlarge; SSM probe was unavailable.
- `recent_xid` WARN: observed `TimedOut`; expected `no recent critical XID`; SSM probe did not finish within 30 seconds.
  Remediation: Check SSM command execution and retry the in-instance probe.
