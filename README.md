# EC2Check GPU Fleet Health Agent

EC2Check is a GPU fleet pre-flight health agent for EC2 training jobs. It checks candidate instances before a job starts and returns an evidence-backed `GO`, `WARN`, or `FAIL` decision.

The current MVP supports mock checks so the workflow can be demoed without live GPU instances. AWS mode is intentionally stubbed behind a small tool boundary for EC2, CloudWatch, and SSM integration.

## Run Locally

```bash
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload
```

Useful endpoints:

- `GET http://127.0.0.1:8000/health`
- `GET http://127.0.0.1:8000/ready`
- `GET http://127.0.0.1:8000/regions/current`
- `POST http://127.0.0.1:8000/v1/preflight-check`
- `GET http://127.0.0.1:8000/docs`

## CLI Demo

```bash
python3 -m app.cli check \
  --job-id demo-001 \
  --profile distributed-gpu \
  --instances i-good001 i-badgpu123 \
  --mode mock
```

Mock instance name hints:

- `badgpu` or an ID ending in `123` simulates a missing GPU.
- `efa` simulates EFA failure.
- `fsx` simulates FSx failure.
- `xid` simulates a recent critical XID event.
- `warn` simulates an old noncritical XID warning.
- `ec2fail` simulates EC2 status check failure.

## API Example

```bash
curl -X POST http://127.0.0.1:8000/v1/preflight-check \
  -H 'content-type: application/json' \
  -d @examples/sample-request.json
```

For real AWS metadata checks, set `mode` to `aws` in the request body. AWS mode
uses the AWS CLI with profile `OAI` by default and clears shell-level
`AWS_REGION` overrides so the profile region can be used. If the target instance
is online in SSM, AWS mode also runs a short `AWS-RunShellScript` probe for
`nvidia-smi` GPU count, `fi_info -p efa` EFA functionality, and recent NVIDIA
XID kernel log events.

## Tests

```bash
python3 -m unittest discover -s tests
```

## Configuration

Environment variables use the `EC2CHECK_` prefix.

```bash
EC2CHECK_AWS_REGION=us-east-1
EC2CHECK_AWS_PROFILE=OAI
EC2CHECK_SERVICE_VERSION=0.1.0
EC2CHECK_REPORT_DIR=reports
EC2CHECK_DEFAULT_PROFILE=distributed-gpu
EC2CHECK_DEFAULT_MODE=mock
```

See `plan.md` for the broader product and AWS deployment roadmap.
