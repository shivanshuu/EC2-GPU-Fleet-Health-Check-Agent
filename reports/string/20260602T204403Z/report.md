# GPU Fleet Health Report: string

Decision: `GO`
Profile: `distributed-gpu`
Created: `2026-06-02T20:44:03.338927+00:00`

All 1 instance(s) passed pre-flight checks for job string.

Recommended action: Proceed with job submission.

## Instance Results

### xx: `GO`
Risk: `LOW`
Check depth: `PHASE_1_FAST`

- `ec2_status` PASS: observed `ok`; expected `ok`; Mock EC2 instance and system status checks were evaluated.
- `gpu_count` PASS: observed `8`; expected `8`; nvidia-smi -L returned 8 GPU device(s).
- `efa_available` PASS: observed `present`; expected `present`; fi_info -p efa returned the mock EFA availability result.
- `fsx_mount` PASS: observed `responsive`; expected `responsive`; Mock mount probe checked FSx path responsiveness.
- `recent_xid` PASS: observed `none`; expected `no recent critical XID`; Mock kernel log contains no critical XID events.
- `nvlink_status` PASS: observed `active`; expected `active`; Mock NVLink probe reports active links.
