# GPU Fleet Health Report: ui-smoke

Decision: `FAIL`
Profile: `single-node-gpu`
Created: `2026-06-02T21:38:26.760027+00:00`

1 of 2 instance(s) failed pre-flight checks for job ui-smoke.

Recommended action: Block job submission, quarantine failed nodes, and select replacement capacity.

## Instance Results

### i-good001: `GO`
Risk: `LOW`
Check depth: `PHASE_1_FAST`

- `ec2_status` PASS: observed `ok`; expected `ok`; Mock EC2 instance and system status checks were evaluated.
- `gpu_count` PASS: observed `1`; expected `1`; nvidia-smi -L returned 1 GPU device(s).
- `recent_xid` PASS: observed `none`; expected `no recent critical XID`; Mock kernel log contains no critical XID events.

### i-badgpu123: `FAIL`
Risk: `LOW`
Check depth: `PHASE_1_FAST`
Action: Block job submission and quarantine or replace the failed node.

- `ec2_status` PASS: observed `ok`; expected `ok`; Mock EC2 instance and system status checks were evaluated.
- `gpu_count` FAIL: observed `0`; expected `1`; nvidia-smi -L returned 0 GPU device(s).
  Remediation: Quarantine node and request replacement before distributed training.
- `recent_xid` PASS: observed `none`; expected `no recent critical XID`; Mock kernel log contains no critical XID events.
