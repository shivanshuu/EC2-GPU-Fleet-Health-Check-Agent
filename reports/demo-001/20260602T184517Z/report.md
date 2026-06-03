# GPU Fleet Health Report: demo-001

Decision: `FAIL`
Profile: `distributed-gpu`
Created: `2026-06-02T18:45:17.427324+00:00`

1 of 2 instance(s) failed pre-flight checks for job demo-001.

Recommended action: Block job submission, quarantine failed nodes, and select replacement capacity.

## Instance Results

### i-good001: `GO`
Risk: `LOW`
Check depth: `PHASE_1_FAST`

- `ec2_status` PASS: observed `ok`; expected `ok`; Mock EC2 instance and system status checks were evaluated.
- `gpu_count` PASS: observed `8`; expected `8`; nvidia-smi -L returned 8 GPU device(s).
- `efa_available` PASS: observed `present`; expected `present`; fi_info -p efa returned the mock EFA availability result.
- `fsx_mount` PASS: observed `responsive`; expected `responsive`; Mock mount probe checked FSx path responsiveness.
- `recent_xid` PASS: observed `none`; expected `no recent critical XID`; Mock kernel log contains no critical XID events.
- `nvlink_status` PASS: observed `active`; expected `active`; Mock NVLink probe reports active links.

### i-badgpu123: `FAIL`
Risk: `LOW`
Check depth: `PHASE_1_FAST`
Action: Block job submission and quarantine or replace the failed node.

- `ec2_status` PASS: observed `ok`; expected `ok`; Mock EC2 instance and system status checks were evaluated.
- `gpu_count` FAIL: observed `7`; expected `8`; nvidia-smi -L returned 7 GPU device(s).
  Remediation: Quarantine node and request replacement before distributed training.
- `efa_available` PASS: observed `present`; expected `present`; fi_info -p efa returned the mock EFA availability result.
- `fsx_mount` PASS: observed `responsive`; expected `responsive`; Mock mount probe checked FSx path responsiveness.
- `recent_xid` PASS: observed `none`; expected `no recent critical XID`; Mock kernel log contains no critical XID events.
- `nvlink_status` PASS: observed `active`; expected `active`; Mock NVLink probe reports active links.
