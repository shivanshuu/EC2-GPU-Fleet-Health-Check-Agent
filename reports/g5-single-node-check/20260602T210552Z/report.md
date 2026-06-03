# GPU Fleet Health Report: g5-single-node-check

Decision: `WARN`
Profile: `single-node-gpu`
Created: `2026-06-02T21:05:52.878563+00:00`

2 of 2 instance(s) produced warnings for job g5-single-node-check.

Recommended action: Proceed only if the risk is acceptable; run standard checks for high-value jobs.

## Instance Results

### i-086d21b7ed6e3aaa6: `WARN`
Risk: `HIGH`
Check depth: `FULL_PHASE_2`
Action: Allow only with operator visibility; consider a standard check first.

- `instance_state` PASS: observed `running`; expected `running`; EC2 DescribeInstances returned the instance lifecycle state.
- `ec2_status` PASS: observed `state=running, system=ok, instance=ok`; expected `state=running, system=ok, instance=ok`; EC2 DescribeInstanceStatus returned AWS system and instance status checks.
- `gpu_count` PASS: observed `1`; expected `1`; GPU count was inferred from EC2 instance type g5.xlarge.
- `recent_xid` WARN: observed `not probed`; expected `no recent critical XID`; GPU XID history requires an in-instance log probe; AWS fast mode did not inspect kernel logs.
  Remediation: Enable SSM or another in-instance execution path for this check.

### i-06ac0cdfca64c2d72: `WARN`
Risk: `HIGH`
Check depth: `FULL_PHASE_2`
Action: Allow only with operator visibility; consider a standard check first.

- `instance_state` PASS: observed `running`; expected `running`; EC2 DescribeInstances returned the instance lifecycle state.
- `ec2_status` PASS: observed `state=running, system=ok, instance=ok`; expected `state=running, system=ok, instance=ok`; EC2 DescribeInstanceStatus returned AWS system and instance status checks.
- `gpu_count` PASS: observed `1`; expected `1`; GPU count was inferred from EC2 instance type g5.xlarge.
- `recent_xid` WARN: observed `not probed`; expected `no recent critical XID`; GPU XID history requires an in-instance log probe; AWS fast mode did not inspect kernel logs.
  Remediation: Enable SSM or another in-instance execution path for this check.
