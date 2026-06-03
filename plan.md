# GPU Fleet Health Agent Plan

## Executive Summary

Enterprises running large-scale AI training on AWS can lose substantial GPU-hours when jobs land on EC2 instances that are technically running but functionally degraded. Basic EC2 status checks can confirm that an instance is reachable and that AWS has not detected certain system or instance failures, but they do not answer the job-specific question that matters before a high-cost training run:

> Is this exact node, right now, healthy enough for this exact job?

The proposed solution is a GPU Fleet Health Agent: a pre-job readiness gate for EC2 GPU fleets that checks instance, GPU, network, storage, and system health before a job is submitted. The first version should be deterministic, evidence-based, and explainable. The "agent" layer should orchestrate checks, synthesize results, explain decisions, compare against history, and eventually recommend or perform bounded remediation.

The strongest initial positioning is:

> HyperPod-style pre-flight health discipline for customers running custom EC2, EKS, Slurm, Ray, or internal schedulers.

The hackathon MVP should focus on Phase 1 fast pre-flight checks and a small slice of Phase 2 standard checks. It should prove that the agent can prevent a job from landing on a bad EC2 GPU node, explain why, and recommend or trigger quarantine.

## Business Proposition

### Problem

Large distributed training jobs are expensive and fragile. A single bad GPU, degraded NVLink path, EFA issue, FSx mount problem, driver mismatch, or stale XID event can cause job failure, severe slowdown, NCCL timeout, or checkpoint rollback.

Schedulers often trust stale node labels or simple readiness signals. A node can appear schedulable while still being a poor choice for a specific job. This creates the "bad node lottery": teams restart failed jobs and hope the next placement avoids the same hardware.

### Customer Pain

Customers running large GPU fleets face several recurring problems:

- Jobs fail hours after launch due to pre-existing hardware or interconnect issues.
- Silent degradation causes jobs to run slower without immediately failing.
- Observability gaps can hide GPU-level issues for long periods.
- Engineers manually SSH into nodes and run diagnostics after failures.
- Restarting jobs can waste checkpoint progress, reserved capacity, and scarce GPU time.
- Self-managed EC2, EKS, Slurm, Ray, or internal schedulers often lack a unified pre-job health gate.

### Value Proposition

The agent reduces wasted GPU-hours by checking node readiness before jobs start. It provides:

- A single `GO`, `WARN`, or `FAIL` decision before job submission.
- Evidence-backed explanations for every decision.
- Fast detection of unhealthy or suspicious GPU nodes.
- Optional quarantine or scheduler cordon action.
- Historical learning over time to improve thresholds and placement.
- A portable reliability layer for customers who do not use HyperPod.

### Strategic Value

For AWS, this improves the reliability story for GPU training across EC2, EKS, and potentially HyperPod. Customers who trust their GPU fleet are more likely to scale usage. Customers who repeatedly lose expensive jobs may reduce cluster size, delay projects, or evaluate other cloud providers.

The agent can be positioned as an AWS-native reliability layer that uses existing building blocks: EC2 APIs, CloudWatch, SSM Run Command, DCGM, `nvidia-smi`, EFA tools, NCCL tests, and scheduler integrations.

## Why Customers May Not Use HyperPod

HyperPod has valuable built-in health and resiliency features, including deep health checks for GPU, Trainium, EFA, NCCL, DCGM, and related infrastructure. However, many customers still choose bare EC2 or self-managed orchestration.

Common reasons include:

- Cost sensitivity: customers may want raw EC2 economics, existing ODCRs, Spot usage, Savings Plans, or their own capacity accounting.
- Control: large training labs often use custom schedulers, AMIs, health checks, drivers, NCCL tuners, observability stacks, and remediation workflows.
- Multi-cloud strategy: customers may want one Kubernetes or scheduler abstraction across AWS, GCP, Azure, and on-prem environments.
- Multi-account isolation: customers may buy reserved capacity in one account and run isolated workloads across different accounts.
- Migration friction: existing Slurm, Ray, Kueue, Airflow, or internal schedulers may already be embedded.
- Performance experimentation: advanced users may want direct control over topology, placement, checkpointing, collectives, and failure handling.
- Operational preference: some teams prefer self-managed EC2 even if it means they need to assemble reliability tooling themselves.

This creates an opportunity for a lightweight health gate that works with the infrastructure customers already run.

## Challenges

### 1. Trust And False Positives

If the agent blocks healthy nodes too often, teams will bypass it. The MVP should only block on high-confidence failures and emit warnings for ambiguous signals.

Initial hard-block examples:

- EC2 system or instance status check failed.
- Expected GPU count does not match visible GPU count.
- Required EFA device is unavailable.
- Required FSx mount is unavailable or unresponsive.
- Recent critical XID event indicates GPU fell off the bus.
- Required NVIDIA or EFA kernel modules are missing.

### 2. Check Runtime

Not every check can run before every job. A 30-second pre-flight cannot fully validate NCCL bandwidth across a large cluster. The system needs tiers:

- Fast pre-flight: under 30 seconds, every job.
- Standard check: under 5 minutes, first job of day, high-value jobs, or suspicious nodes.
- Deep check: 15+ minutes, after maintenance, after failures, or before major runs.

### 3. Deterministic Health Engine vs Agent Reasoning

The health checks should be deterministic, auditable, and reproducible. The agent should not invent health status. It should orchestrate checks, explain results, compare against history, and recommend actions.

### 4. Execution Environment

SSM Run Command is a convenient MVP execution layer, but not all customers will have SSM enabled. Production should support multiple execution modes:

- SSM Run Command.
- Kubernetes DaemonSet.
- Slurm prolog script.
- Node-local daemon.
- SSH only for internal demos or controlled environments.

### 5. Historical Data Quality

Historical learning depends on consistent metadata:

- Job type.
- Instance type.
- Instance IDs.
- AMI ID.
- Driver, CUDA, NCCL, and DCGM versions.
- Pre-flight result.
- Warnings.
- Outcome.
- Failure reason.
- Duration.
- Checkpoint loss.
- Estimated wasted cost.

Without consistent job taxonomy and outcome labeling, the agent cannot reliably learn which signals predict failure.

### 6. Remediation Safety

Automatic quarantine and replacement are valuable but risky. Production rollout should use policy stages:

- Observe only.
- Warn only.
- Block with human approval.
- Auto-quarantine on high-confidence failures.
- Auto-replace only within approved policy boundaries.

## Opportunities

### 1. Pre-Job Health Gate

The largest immediate opportunity is pre-flight gating. Current tooling is often reactive: it tells teams something failed after the job is already running. A pre-job gate prevents bad placement before expensive compute begins.

### 2. Silent Degradation Detection

The agent can detect conditions that are not visible in basic EC2 health:

- NVLink degradation.
- NCCL bandwidth degradation.
- EFA underperformance.
- GPU XID history.
- Thermal throttling.
- GPU count mismatch.
- Fabric Manager issues.
- DCGM service failures.
- FSx or storage responsiveness problems.

### 3. Historical Learning

Over time, the agent can learn which warnings actually predict job failure or slowdown. This can evolve the system from a checker into a reliability advisor.

Examples:

- "Recent XID 79 should be a hard fail for distributed GPU jobs."
- "This AMI version correlates with NCCL timeout failures."
- "This instance group shows 30% lower NCCL bandwidth than baseline."
- "This job type usually needs more memory than the selected instance provides."

### 4. Scheduler-Aware Placement

The agent can eventually recommend which nodes are safest for a given job, not just whether a proposed node set is acceptable.

### 5. Cross-Environment Portability

The same readiness model can be adapted to:

- Bare EC2.
- EKS and Kueue.
- Slurm.
- Ray.
- HyperPod-adjacent workflows.
- Internal training platforms.

## Objectives

### Hackathon MVP Objectives

The MVP should prove:

1. The agent can run fast pre-flight checks against one or more EC2 GPU instances.
2. The agent can classify each node as healthy, warning, or failed.
3. The agent can produce an overall job-level `GO`, `WARN`, or `FAIL` decision.
4. The agent can explain the decision with evidence.
5. The agent can recommend or simulate quarantine for failed nodes.
6. The output is machine-readable enough to integrate with a scheduler later.

### Non-Goals For MVP

Do not build these first:

- Full autonomous remediation.
- Full in-flight monitoring.
- Full post-job root cause analysis.
- Complex machine learning prediction.
- Multi-cloud support.
- Deep checks before every job.
- A large dashboard.
- Complete HyperPod integration.

### Production Objectives

Longer term, the system should:

- Integrate with job submission flows.
- Store historical job and node health data.
- Learn risk patterns from outcomes.
- Recommend placement based on prior performance.
- Quarantine and replace nodes within policy.
- Support multiple execution backends.
- Provide auditable decisions for platform and ML teams.

## Agent Maturity Model

### Level 0: Scripted Checker

A CLI runs predefined checks on a list of instances and emits JSON.

Example:

```bash
gpu-health-agent check --instances i-123 i-456 --profile distributed-gpu
```

### Level 1: Pre-Flight Gate

The checker sits in front of a scheduler or job submission path. It blocks high-confidence failures and warns on ambiguous signals.

### Level 2: Explainable Agent

The agent summarizes evidence and remediation steps in human-readable form.

Example:

```text
FAIL: Instance i-123 has 7 visible GPUs; expected 8.
Evidence: nvidia-smi -L returned 7 devices; dmesg contains recent Xid 79.
Recommendation: quarantine i-123 and select a replacement node.
```

### Level 3: Job-Aware Health

The agent chooses checks and thresholds based on job profile:

- Single-node GPU fine-tune.
- Multi-node distributed training.
- CPU batch job.
- Inference batch job.
- Data preprocessing job.

### Level 4: Historical Baselines

The agent compares new submissions against historical runs and node behavior.

Examples:

- Prior jobs on this node failed after similar XID warnings.
- This job type normally completes in 9 hours; recent runs on this instance group are 30% slower.
- This AMI and driver combination correlates with EFA errors.

### Level 5: Advisor

The agent recommends safer placement, stronger thresholds, and specific remediation.

### Level 6: Bounded Autopilot

The agent performs policy-approved remediation:

- Cordon node.
- Tag node as quarantined.
- Trigger replacement.
- Open ticket.
- Notify owner.
- Require human approval for high-impact actions.

## Technical Plan

### How The New Orchestration Insight Helps

The new orchestration detail makes the plan more actionable. Earlier sections describe what the agent should check and why it matters. This section clarifies how the agent actually receives instance IDs, where AWS API calls happen, what credentials are required, how multi-node jobs are handled, and how decisions are enforced.

This does not replace the core GPU Health Agent idea. It sharpens it:

- The hackathon demo can use a manual or conversational entry point.
- Production can use EventBridge or a Kubernetes admission webhook.
- The agent can run from a laptop, Lambda, ECS, or another control-plane environment.
- The target GPU instances do not need SSH access if SSM is available.
- Multi-node checks can run in parallel and return both per-node and aggregate decisions.
- Historical node risk can determine how deep the check should be.

### AWS Deployment Architecture

The agent should be deployable as an AWS-native control-plane service. The first AWS deployment should use serverless components where possible so the team can move quickly during the hackathon, then evolve to ECS or EKS for longer-running checks and admission-webhook integration.

Recommended AWS MVP:

```text
Engineer / Job Submitter / Demo Script
        |
        v
API Gateway HTTP API
        |
        v
Lambda: preflight-agent
        |
        +-- EC2 APIs
        |     - DescribeInstances
        |     - DescribeInstanceStatus
        |
        +-- CloudWatch APIs
        |     - GetMetricData
        |
        +-- SSM APIs
        |     - DescribeInstanceInformation
        |     - SendCommand
        |     - GetCommandInvocation
        |
        +-- DynamoDB
        |     - node risk history
        |     - job decision summaries
        |
        +-- S3
        |     - raw command output
        |     - JSON reports
        |     - markdown reports
        |
        +-- CloudWatch Logs / Metrics
              - agent logs
              - decision metrics
              - failed-node counts
```

Recommended production architecture:

```text
Job Submission Source
  - Manual API call
  - EventBridge event
  - Kueue / Kubernetes admission webhook
  - Slurm prolog wrapper
  - Ray job wrapper
        |
        v
Agent Entry Layer
  - API Gateway + Lambda for fast checks
  - EventBridge + Lambda for asynchronous checks
  - ECS Fargate service for longer checks or webhook serving
  - EKS service for in-cluster admission webhook integration
        |
        v
Agent Orchestrator
  - choose check depth
  - fan out per-node checks
  - collect SSM results
  - evaluate deterministic rules
  - write reports and history
        |
        v
Target GPU EC2 Instances
  - managed by SSM
  - no SSH required
  - run nvidia-smi, EFA, DCGM, NCCL, and storage probes
        |
        v
Decision Enforcement
  - return GO/WARN/FAIL
  - reject admission request
  - tag or cordon failed node
  - trigger approved replacement workflow
```

### AWS Deployment Mode Recommendations

Use two deployment modes:

1. **AWS Hackathon MVP Mode**
   - API Gateway + Lambda for manual pre-flight requests.
   - DynamoDB for node risk and job history.
   - S3 for reports and raw probe output.
   - CloudWatch Logs for agent logs.
   - SSM Run Command for node probes.
   - Optional EventBridge rule for demo event triggering.

2. **AWS Production Mode**
   - ECS Fargate or EKS service for longer checks, webhook hosting, and more control over timeouts.
   - API Gateway or internal ALB/NLB depending on who calls the agent.
   - EventBridge for queue/job-submission events.
   - DynamoDB or Aurora/Postgres for history.
   - S3 for durable raw artifacts.
   - CloudWatch metrics and alarms for agent health.
   - KMS encryption for S3, DynamoDB, and environment secrets.

Lambda is a good first deployment target for the 30-second Phase 1 checks. ECS Fargate or an EKS service is better for Phase 2 and deep checks because they can exceed Lambda-friendly runtimes, need more controlled concurrency, or serve an admission webhook with predictable networking.

### MVP Runtime Architecture

```text
Job Submitter / Demo CLI
        |
        v
API Gateway / Lambda Pre-Flight Agent
        |
        +-- AWS Collector
        |     - EC2 DescribeInstanceStatus
        |     - EC2 DescribeInstances
        |     - CloudWatch GetMetricData
        |     - SSM DescribeInstanceInformation
        |
        +-- Node Probe Runner
        |     - SSM Run Command for MVP
        |     - nvidia-smi
        |     - fi_info
        |     - mount checks
        |     - dmesg/journal scan
        |
        +-- Rule Engine
        |     - deterministic PASS/WARN/FAIL rules
        |     - profile-specific thresholds
        |
        +-- Agent Explanation Layer
        |     - summarize evidence
        |     - recommend remediation
        |     - format operator report
        |
        +-- Report Store
              - DynamoDB decision summary
              - S3 raw output and reports
              - CloudWatch Logs and metrics
```

### End-To-End Orchestration

The agent has three possible entry points.

Hackathon entry point:

- Manual or conversational.
- Engineer provides the instance ID or node list directly.
- Example: `pre-flight node i-abc123 for 128-GPU training job`.
- Agent extracts or receives the instance IDs and runs checks.

Production entry point A:

- EventBridge trigger.
- Job is submitted to Kubernetes, Kueue, Slurm, Ray, or an internal queue.
- The scheduler or queue emits an event with the candidate node list.
- Lambda, ECS, or another control-plane service invokes the agent with instance IDs.

Production entry point B:

- Kubernetes admission webhook.
- Pod creation is intercepted.
- The webhook calls the agent before admitting the workload.
- The agent checks target nodes and returns admit, warn, or reject.

Production may also support a Slurm prolog or Ray job-submission wrapper. For the hackathon, manual input plus mock or real SSM is enough. EventBridge and webhook integration can remain presentation material unless time allows a small stub.

### Tool And API Call Layer

The agent should be implemented as a Python control-plane process that runs in AWS for the hackathon MVP. The same core logic can also run locally in mock mode for development and testing.

```text
Codex Agent / GPU Health Agent (Python)
Running on laptop, Lambda, ECS, or control-plane host
        |
        v
Tool Layer: boto3 functions in tools.py
        |
        +-- SSM RunCommand -> target GPU instance
        |     - nvidia-smi -q
        |     - nvidia-smi -L
        |     - nvidia-smi nvlink -s
        |     - fi_info -p efa
        |     - dmesg or journal scan for XID/MCE/EFA/PCIe errors
        |     - dcgmi diag -r 2
        |     - nccl-tests all_reduce_perf
        |     - systemctl is-active nvidia-fabricmanager
        |     - systemctl is-active dcgm
        |
        +-- CloudWatch GetMetricData
        |     - StatusCheckFailed_Instance
        |     - StatusCheckFailed_System
        |     - StatusCheckFailed_AttachedEBS where applicable
        |
        +-- EC2 DescribeInstances / DescribeInstanceStatus
        |     - instance type
        |     - instance state
        |     - status checks
        |     - placement and metadata
        |
        +-- DynamoDB / S3 memory and report store
              - past decisions
              - node risk score
              - job outcome history
              - raw probe output and reports
```

### Required Access

For the MVP with SSM, the agent machine or runtime needs an IAM role or credentials with:

- `ssm:SendCommand`
- `ssm:GetCommandInvocation`
- `ssm:ListCommandInvocations`
- `cloudwatch:GetMetricData`
- `ec2:DescribeInstances`
- `ec2:DescribeInstanceStatus`
- `ssm:DescribeInstanceInformation`
- `dynamodb:GetItem`
- `dynamodb:PutItem`
- `dynamodb:UpdateItem`
- `dynamodb:Query`
- `s3:GetObject`
- `s3:PutObject`
- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`

If quarantine tagging is enabled, add:

- `ec2:CreateTags`

If production remediation is enabled, additional permissions may be needed depending on the action:

- Kubernetes API access to cordon nodes.
- SageMaker or HyperPod replacement permissions if using cluster node replacement APIs.
- Ticketing, notification, or incident-management permissions.

The target GPU instance needs:

- SSM Agent running.
- IAM instance profile allowing SSM management.
- Network path to SSM endpoints.
- NVIDIA, EFA, DCGM, NCCL, and storage utilities installed for the checks being run.

No SSH, direct instance login, or manual `kubectl` access is required for the basic SSM execution path.

### AWS Networking Requirements

The agent can run outside a VPC for the simplest hackathon deployment if it only calls public AWS service endpoints. The target instances still need to be managed by SSM.

For production or private environments, deploy the agent in a VPC and configure VPC endpoints for:

- Systems Manager: `ssm`
- SSM Messages: `ssmmessages`
- EC2 Messages: `ec2messages`
- EC2 API: `ec2`
- CloudWatch Logs: `logs`
- CloudWatch Monitoring: `monitoring`
- S3 gateway endpoint
- DynamoDB gateway endpoint
- KMS if using customer-managed keys

Target instances need outbound access to SSM endpoints through public internet, NAT, or private VPC endpoints.

### AWS Resource Inventory

Hackathon MVP resources:

- `AWS::Lambda::Function` for the pre-flight agent.
- `AWS::ApiGatewayV2::Api` HTTP API for manual requests.
- `AWS::DynamoDB::Table` for job and node history.
- `AWS::S3::Bucket` for reports and raw probe output.
- `AWS::IAM::Role` for Lambda execution.
- `AWS::Logs::LogGroup` for agent logs.
- Optional `AWS::Events::Rule` for EventBridge-triggered demo runs.
- Optional `AWS::Lambda::FunctionUrl` if API Gateway is too much for the hackathon.

Production resources:

- ECS Fargate service or EKS deployment for long-running checks.
- Internal ALB/NLB if used by private scheduler services.
- EventBridge bus/rules for job-submission events.
- KMS keys for encrypted S3 and DynamoDB data.
- CloudWatch dashboards and alarms.
- Secrets Manager or SSM Parameter Store for configuration.
- WAF or private API access if exposed beyond internal users.

### Multi-Node Job Handling

For a multi-node job, such as a 128-GPU job on 16 nodes, the agent receives a list of instance IDs.

The agent should:

1. Run Phase 1 fast checks on all nodes in parallel.
2. Query historical node risk before deciding whether to run deeper checks.
3. Run Phase 2 checks only on flagged, suspicious, medium-risk, high-risk, or explicitly requested nodes.
4. Return per-node decisions and an aggregate job decision.
5. Block the job if any required node receives `FAIL`.
6. Allow the job if all nodes pass.
7. Allow with advisory if there are warnings but no failures.

Example aggregate result:

```text
15/16 PASS, 1 FAIL
Aggregate decision: FAIL
Failed node: i-abc123
Reason: expected 8 GPUs, found 7; recent XID 79 in kernel logs.
```

### Risk-Based Check Depth

Historical data should influence the check depth. This makes the agent faster for clean nodes and more careful with suspicious nodes.

```text
Job Submitted
     |
     v
Agent receives node list
     |
     v
EC2 DescribeInstances -> get instance type -> infer expected GPU/EFA counts
     |
     v
For each node: check_history() -> determine risk level -> set check depth
     |
     +-- LOW risk -> Phase 1 only, under 30s
     +-- MEDIUM risk -> Phase 1 + lightweight Phase 2, under 1 min
     +-- HIGH risk -> Phase 1 + full Phase 2, under 5 min
     |
     v
Agent synthesizes outputs -> decision per node
     |
     v
Store decision in memory and update risk score
     |
     v
Return per-node decisions, aggregate decision, reasoning, suggested actions
```

Initial risk scoring can be simple and rule-based:

- Low risk: recent clean checks, successful recent jobs, no warnings.
- Medium risk: old warnings, stale health data, unknown history, or recent replacement.
- High risk: repeated warnings, recent failed job, recent XID, prior NCCL timeout, or prior quarantine.

This gives historical data a practical role in the MVP roadmap without requiring complex prediction.

### Recommended MVP Components

Use Python for speed of implementation.

Suggested structure:

```text
gpu-health-agent/
  README.md
  pyproject.toml
  template.yaml or cdk/
  src/
    gpu_health_agent/
      __init__.py
      cli.py
      app.py
      lambda_handler.py
      config.py
      models.py
      tools.py
      aws_collectors.py
      node_probe.py
      rules.py
      explain.py
      reports.py
      history.py
      demo_data.py
  infra/
    README.md
    template.yaml
    parameters-dev.json
    parameters-prod.json
  scripts/
    deploy.sh
    invoke-demo.sh
    package-lambda.sh
  profiles/
    distributed-gpu.json
    single-node-gpu.json
    cpu-batch.json
  examples/
    sample-request.json
    sample-report-pass.json
    sample-report-fail.json
  tests/
    test_rules.py
    test_explain.py
```

### Job Profile Schema

Example:

```json
{
  "name": "distributed-gpu",
  "expected_gpu_count": 8,
  "requires_efa": true,
  "requires_fsx": true,
  "requires_nvlink": true,
  "fast_check_timeout_seconds": 30,
  "standard_check_timeout_seconds": 300,
  "block_on_recent_critical_xid": true,
  "warn_on_ecc_errors": true,
  "minimum_free_disk_gb": 100
}
```

### Check Result Schema

Example:

```json
{
  "instance_id": "i-123",
  "check_name": "gpu_count",
  "status": "FAIL",
  "severity": "CRITICAL",
  "observed": "7",
  "expected": "8",
  "evidence": "nvidia-smi -L returned 7 GPU devices",
  "remediation": "Quarantine node and replace before distributed training"
}
```

### Job Decision Schema

Example:

```json
{
  "job_id": "train-001",
  "profile": "distributed-gpu",
  "decision": "FAIL",
  "summary": "1 of 8 instances failed pre-flight checks",
  "aggregate_counts": {
    "pass": 7,
    "warn": 0,
    "fail": 1
  },
  "instances": [
    {
      "instance_id": "i-123",
      "status": "FAIL",
      "risk_level": "HIGH",
      "check_depth": "FULL_PHASE_2",
      "failed_checks": ["gpu_count", "recent_xid"]
    }
  ],
  "recommended_action": "Block job submission, quarantine failed node, and request replacement",
  "report_uri": "reports/train-001.json"
}
```

### Fast Pre-Flight Checks

Run before every job.

AWS-side checks:

- EC2 instance state is `running`.
- EC2 system status is OK.
- EC2 instance status is OK.
- Attached EBS status is OK where relevant.
- SSM managed instance is online.

Node-side checks:

- GPU count matches expected count.
- `nvidia-smi -q` does not show critical errors.
- Recent XID scan does not show critical events.
- NVLink status reports active links when required.
- EFA device exists when required.
- FSx mount exists and responds when required.
- Required services are running: NVIDIA driver, Fabric Manager, DCGM, EFA components.
- Kernel modules are present: NVIDIA, EFA, GDR-related modules where applicable.

### Standard Checks

Run for high-value jobs, first job of day, suspicious nodes, or manually requested checks.

- DCGM diagnostics level 2.
- Short NCCL allreduce test.
- EFA latency and bandwidth smoke test.
- NVLink/NVBandwidth sample.
- PCIe link width and speed validation.
- FSx or local disk I/O sanity test.

### Deep Checks

Run after failures, after maintenance, after node replacement, or before very large runs.

- DCGM diagnostics level 4.
- Multi-node NCCL allreduce across candidate nodes.
- GPU memory test.
- HPL or workload-specific benchmark.
- Extended EFA bandwidth and latency benchmark.
- NVSwitch SXid scan.
- Topology verification.

## Historical Data Plan

### What To Store

For every pre-flight decision and job outcome:

```json
{
  "job_id": "train-2026-06-02-001",
  "job_type": "distributed-gpu-training",
  "submitted_at": "2026-06-02T12:00:00Z",
  "instance_ids": ["i-123", "i-456"],
  "instance_type": "p5.48xlarge",
  "ami_id": "ami-abc",
  "driver_version": "535.183.01",
  "cuda_version": "12.2",
  "nccl_version": "2.x",
  "dcgm_version": "3.x",
  "preflight_decision": "WARN",
  "warnings": ["old XID event on i-123"],
  "outcome": "FAILED",
  "failure_reason": "NCCL timeout",
  "duration_minutes": 47,
  "checkpoint_loss_minutes": 120,
  "estimated_wasted_cost_usd": 100000
}
```

### MVP Storage

- DynamoDB table for job decisions and node risk summaries.
- S3 bucket for raw SSM output, JSON reports, and markdown reports.
- CloudWatch Logs for Lambda logs and command orchestration details.
- Optional local JSON mode only for developer testing.

Suggested DynamoDB single-table design:

```text
Table: gpu-health-agent-history

PK                         SK                         Purpose
JOB#<job_id>               DECISION                   job-level decision
JOB#<job_id>               NODE#<instance_id>         per-node result for job
NODE#<instance_id>         RISK                       latest node risk summary
NODE#<instance_id>         CHECK#<timestamp>          historical node check
PROFILE#<profile_name>     BASELINE                   optional profile baseline
```

Suggested S3 layout:

```text
s3://<bucket>/reports/<yyyy>/<mm>/<dd>/<job_id>/decision.json
s3://<bucket>/reports/<yyyy>/<mm>/<dd>/<job_id>/report.md
s3://<bucket>/raw-ssm/<yyyy>/<mm>/<dd>/<job_id>/<instance_id>/<command_id>.txt
```

### Production Storage

- S3 for raw check output and reports.
- DynamoDB or Aurora/Postgres for job and node summaries.
- CloudWatch Logs for raw command output.
- CloudWatch metrics for fleet-level health status.
- OpenSearch only if interactive log search is required.

### Historical Insights

The agent should eventually answer:

- Which nodes repeatedly fail health checks?
- Which warnings predict failures?
- Which instance groups are slower than baseline?
- Which AMIs or driver versions correlate with NCCL failures?
- Which job types require stricter checks?
- Which failures are due to infrastructure vs workload behavior?

## Decision Policy

### Status Definitions

`GO`:

- All required checks pass.
- No critical warnings.

`WARN`:

- Job may proceed, but there are risk indicators.
- Examples: old noncritical XID, mild ECC warning, low but acceptable disk space, stale metrics, nonrequired service degraded.

`FAIL`:

- Job should not be submitted to the selected node set.
- Examples: missing GPU, failed EC2 status, required EFA unavailable, FSx unavailable, critical XID, required service missing.

### Rollout Policy

1. Observe only: collect reports without influencing scheduling.
2. Warn only: show recommendations but never block.
3. Soft block: require human confirmation to proceed on `FAIL`.
4. Hard block: automatically reject high-confidence failures.
5. Auto-quarantine: cordon or tag failed nodes.
6. Auto-replace: trigger replacement within explicit policy.

### Decision Enforcement Options

Hackathon enforcement:

- The agent returns the decision.
- A human acts on it.
- The demo shows the quarantine or replacement command as a recommendation.

Production option A: admission control.

- Agent response flows back to a Kueue or Kubernetes admission webhook.
- If the aggregate decision is `FAIL`, the webhook rejects the pod or holds the job.
- If the aggregate decision is `WARN`, the webhook admits the job and annotates the warning.

Production option B: scheduler avoidance.

- The agent cordons the failed Kubernetes node or marks it unschedulable.
- Future jobs avoid the node until it is cleared.

Production option C: managed replacement.

- The agent calls an approved replacement path for blocked nodes.
- For HyperPod-adjacent workflows, this could be a SageMaker or HyperPod node replacement action where available and approved.
- This should require explicit policy approval in production.

## Implementation Steps For Codex

### Step 1: Scaffold The Project

Create a Python package called `gpu-health-agent` with the directory structure shown above. Add a CLI entry point.

Expected command:

```bash
gpu-health-agent check --job-id demo-001 --profile profiles/distributed-gpu.json --instances i-123 i-456 --mode mock
```

### Step 2: Define Data Models

Implement typed models for:

- `JobProfile`
- `HealthCheckResult`
- `InstanceHealthReport`
- `JobHealthDecision`
- `RemediationAction`
- `NodeRiskProfile`
- `CheckDepth`

Use dataclasses or Pydantic depending on project constraints. For a hackathon, dataclasses are enough.

### Step 3: Implement Mock Mode First

Before calling AWS, create mock collectors that simulate:

- Healthy node.
- Missing GPU node.
- EFA failure.
- FSx failure.
- Recent XID failure.
- EC2 status check failure.

This makes the demo reliable without requiring real GPU instances.

### Step 4: Implement Rule Engine

Create deterministic rules that map check results to `GO`, `WARN`, or `FAIL`.

Rules should be profile-aware:

- Missing EFA is `FAIL` only when `requires_efa` is true.
- Missing FSx is `FAIL` only when `requires_fsx` is true.
- GPU count mismatch is `FAIL` for GPU profiles.
- Old noncritical XID is `WARN`; recent critical XID is `FAIL`.

The aggregate job decision should be:

- `FAIL` if any required node fails.
- `WARN` if no nodes fail but one or more nodes warn.
- `GO` only if all required nodes pass.

### Step 5: Implement Explanation Layer

Generate:

- One-line summary.
- Evidence list.
- Per-instance status.
- Recommended action.
- Operator-friendly markdown report.
- Machine-readable JSON report.

The explanation must never claim more than the checks prove.

### Step 6: Add History And Risk Scoring

Implement a simple history layer backed by DynamoDB, with local JSON only as an optional developer fallback.

For MVP:

- Store job decision records and node risk records in DynamoDB.
- Store raw command output and reports in S3.
- Track prior decisions, warnings, failures, and last check timestamp.
- Compute `LOW`, `MEDIUM`, or `HIGH` risk.
- Use risk level to select check depth.

Simple policy:

- `LOW`: clean recent check and no prior failures.
- `MEDIUM`: unknown history, stale check, old warning, or recently replaced node.
- `HIGH`: recent `FAIL`, recent critical XID, prior NCCL timeout, repeated warnings, or prior quarantine.

### Step 7: Add AWS Tool Layer

Create `tools.py` as the boundary for AWS API calls and node command execution. Keep it thin and testable.

Implement tool functions for:

- `describe_instances(instance_ids)`
- `describe_instance_status(instance_ids)`
- `get_cloudwatch_status_metrics(instance_ids)`
- `describe_ssm_instance_information(instance_ids)`
- `send_ssm_probe(instance_id, commands)`
- `get_ssm_command_result(command_id, instance_id)`

Keep AWS access optional so the demo can run in mock mode.

### Step 8: Add AWS Collectors

Implement collectors for real mode:

- `ec2.describe_instance_status`
- `ec2.describe_instances`
- `ssm.describe_instance_information`
- `cloudwatch.get_metric_data`
- optional `ssm.send_command` for node probes

Keep AWS access optional so the demo can run in mock mode.

### Step 9: Add Node Probe Commands

Implement a command bundle for SSM or local execution:

```bash
nvidia-smi -L
nvidia-smi -q
nvidia-smi nvlink -s
fi_info -p efa
mount | grep fsx
dmesg | grep -E 'Xid|NVRM|MCE|EFA|PCIe'
systemctl is-active nvidia-fabricmanager
systemctl is-active dcgm
lsmod | grep -E 'nvidia|efa|gdrdrv|nv_peer_mem'
```

Make each probe tolerant of missing binaries so CPU-only profiles can still run.

### Step 10: Generate Reports

Write outputs to:

```text
s3://<bucket>/reports/<yyyy>/<mm>/<dd>/<job-id>/decision.json
s3://<bucket>/reports/<yyyy>/<mm>/<dd>/<job-id>/report.md
```

The markdown report should be suitable for a Slack paste or incident ticket.

### Step 11: Add Quarantine Stub

For the MVP, do not actually terminate or replace instances. Implement safe actions:

- Print `kubectl cordon <node>` command if Kubernetes node name is known.
- Print AWS tag action: `HealthAgent=Quarantine`.
- Optionally call `ec2.create_tags` only when `--apply-actions` is set.

### Step 12: Add Tests

Add unit tests for:

- Rule aggregation.
- Profile-specific failures.
- Explanation text.
- Mock scenarios.
- JSON report shape.
- Risk scoring.
- Check-depth selection.

### Step 13: Prepare Demo Script

Create a demo with three runs:

1. All nodes healthy: decision `GO`.
2. One node has only 7 of 8 GPUs: decision `FAIL`.
3. One node has old noncritical XID: decision `WARN`.
4. One node has prior failure history: decision path escalates from Phase 1 to deeper checks.

Show:

- CLI command.
- JSON output.
- Markdown report.
- Per-node and aggregate decision.
- Quarantine recommendation.

### Step 14: Optional Scheduler Integration

If time permits, add one integration path:

- Kueue admission webhook stub.
- Slurm prolog script wrapper.
- Simple REST API endpoint.

For hackathon, an API Gateway-backed REST-style endpoint is likely easiest:

```http
POST /v1/preflight-check
```

Request:

```json
{
  "job_id": "demo-001",
  "profile": "distributed-gpu",
  "instance_ids": ["i-123", "i-456"]
}
```

Response:

```json
{
  "decision": "FAIL",
  "summary": "1 instance failed pre-flight checks"
}
```

### Step 15: Add Lambda Handler

Create `lambda_handler.py` that accepts API Gateway or EventBridge input and calls the same core agent logic as the CLI.

Supported API Gateway request:

```json
{
  "job_id": "demo-001",
  "profile": "distributed-gpu",
  "instance_ids": ["i-123", "i-456"],
  "mode": "mock",
  "apply_actions": false
}
```

Supported EventBridge shape:

```json
{
  "source": "gpu-health-agent.demo",
  "detail-type": "JobSubmitted",
  "detail": {
    "job_id": "demo-001",
    "profile": "distributed-gpu",
    "instance_ids": ["i-123", "i-456"]
  }
}
```

The handler should return:

```json
{
  "statusCode": 200,
  "body": {
    "decision": "FAIL",
    "summary": "1 instance failed pre-flight checks",
    "report_uri": "s3://..."
  }
}
```

### Step 16: Add Infrastructure-As-Code

Create either AWS SAM or AWS CDK infrastructure. For a hackathon, SAM is the fastest path.

Minimum resources:

- Lambda function.
- HTTP API route: `POST /v1/preflight-check`.
- DynamoDB history table.
- S3 report bucket.
- CloudWatch log group.
- IAM role and policy for the Lambda function.
- Optional EventBridge rule for demo events.

Recommended Lambda environment variables:

```text
HISTORY_TABLE_NAME=<dynamodb-table>
REPORT_BUCKET_NAME=<s3-bucket>
DEFAULT_PROFILE=distributed-gpu
DEFAULT_MODE=mock
LOG_LEVEL=INFO
APPLY_ACTIONS_DEFAULT=false
```

### Step 17: Add Deployment Scripts

Create scripts:

```text
scripts/package-lambda.sh
scripts/deploy.sh
scripts/invoke-demo.sh
```

`deploy.sh` should deploy the SAM/CDK stack to a named AWS region and output:

- API endpoint URL.
- DynamoDB table name.
- S3 bucket name.
- Lambda function name.

`invoke-demo.sh` should call the API endpoint with a mock failing node and print the response.

### Step 18: Run AWS Smoke Test

Smoke test sequence:

1. Deploy stack.
2. Invoke `POST /v1/preflight-check` in mock mode.
3. Confirm API response contains aggregate decision.
4. Confirm DynamoDB has job and node records.
5. Confirm S3 has `decision.json` and `report.md`.
6. Confirm CloudWatch Logs contain the request ID and decision.
7. If real EC2 instances are available, invoke real mode against one SSM-managed test node.

### Step 19: Add Operational Dashboard

For the hackathon, a full UI is optional. Add CloudWatch metrics instead:

- `PreflightRequests`
- `PreflightPass`
- `PreflightWarn`
- `PreflightFail`
- `FailedNodes`
- `SsmCommandFailures`
- `AverageCheckDurationMs`

Create a simple CloudWatch dashboard or document metric names for the demo.

## Demo Narrative

The demo should tell a simple story:

1. A user submits a distributed GPU training job.
2. The scheduler has selected 8 P5 nodes.
3. The agent runs a 30-second pre-flight.
4. One node reports only 7 GPUs and a recent XID event.
5. The agent blocks submission.
6. The agent recommends quarantining the node.
7. A replacement node passes.
8. The job proceeds.

This proves the core value:

> The agent prevented an expensive training job from starting on bad infrastructure.

## Open Questions

- Which scheduler should be the first integration target: Kueue, Slurm, Ray, or internal queue?
- Should AgentCore be required for MVP, or should the first version be a standalone Python service with optional AgentCore orchestration?
- What exact P5/P5en health thresholds should be used for NCCL, EFA, and NVLink?
- Which remediation actions are acceptable without human approval?
- How should job outcome data be captured from customer environments?
- What metadata must job submitters provide for the historical learning loop to work?
- How should the agent handle SSM-unreachable nodes: fail closed or warn?
- What is the minimum viable UI: CLI report, Slack message, or dashboard?

## Recommended Hackathon Scope

Build:

- Python CLI.
- Lambda-compatible Python handler.
- AWS SAM or CDK deployment.
- API Gateway endpoint for manual pre-flight requests.
- DynamoDB-backed job and node history.
- S3-backed JSON and markdown reports.
- CloudWatch Logs and basic custom metrics.
- Mock mode.
- Profile-aware rules.
- Fast pre-flight checks.
- Standard-check placeholders.
- Quarantine recommendation stub.
- AWS collectors for EC2, CloudWatch, and SSM.
- SSM probe execution if a managed test instance is available.
- EventBridge demo trigger if time permits.

Do not build:

- Autonomous replacement.
- Full scheduler integration.
- Full historical learning engine.
- Complex prediction model.
- Large frontend.
- Production admission webhook.
- Full Phase 2 or deep multi-node NCCL benchmarking.

## Success Criteria

The hackathon MVP is successful if it can:

- Deploy to AWS using SAM or CDK.
- Expose an API endpoint for pre-flight checks.
- Accept a job profile and a list of instances through the API.
- Run mock or real checks.
- Produce `GO`, `WARN`, or `FAIL`.
- Explain the decision with evidence.
- Recommend remediation.
- Store job and node history in DynamoDB.
- Store JSON and markdown reports in S3.
- Emit logs and basic metrics to CloudWatch.
- Demonstrate at least one prevented bad placement.
- Optionally run real SSM checks against one managed GPU or test EC2 instance.

## Final Recommendation

This idea makes sense if it is framed correctly. The system should not start as a magical autonomous infrastructure agent. It should start as a deterministic pre-flight health gate with an agentic explanation and learning layer.

The best first product wedge is GPU training reliability:

> Stop expensive distributed training jobs from starting on unhealthy or degraded EC2 GPU nodes.

Over time, the agent can mature into a historical, predictive, policy-aware reliability system that recommends placement and safely automates quarantine. That path is credible, useful, and compelling for customers who need HyperPod-like health discipline while retaining control of their own EC2 fleets.
