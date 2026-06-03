import argparse
import asyncio

from app.config import get_settings
from app.models import PreflightRequest
from app.service import run_preflight


def main() -> None:
    parser = argparse.ArgumentParser(description="Run GPU fleet pre-flight health checks.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Run a pre-flight check")
    check_parser.add_argument("--job-id", required=True)
    check_parser.add_argument("--profile", default="distributed-gpu")
    check_parser.add_argument("--instances", nargs="+", required=True)
    check_parser.add_argument("--mode", choices=["mock", "aws"], default="mock")
    check_parser.add_argument("--apply-actions", action="store_true")

    args = parser.parse_args()
    if args.command == "check":
        asyncio.run(_run_check(args))


async def _run_check(args: argparse.Namespace) -> None:
    settings = get_settings()
    request = PreflightRequest(
        job_id=args.job_id,
        profile=args.profile,
        instance_ids=args.instances,
        mode=args.mode,
        apply_actions=args.apply_actions,
    )
    decision = await run_preflight(request, report_dir=settings.report_dir)
    print(decision.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
