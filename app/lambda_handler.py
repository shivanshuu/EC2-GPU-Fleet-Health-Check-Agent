import asyncio
import json
from typing import Any

from app.config import get_settings
from app.models import PreflightRequest
from app.service import run_preflight


def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    del context
    payload = _payload_from_event(event)
    decision = asyncio.run(
        run_preflight(
            PreflightRequest.model_validate(payload),
            report_dir=get_settings().report_dir,
        )
    )
    return {
        "statusCode": 200,
        "headers": {"content-type": "application/json"},
        "body": decision.model_dump_json(),
    }


def _payload_from_event(event: dict[str, Any]) -> dict[str, Any]:
    if "detail" in event and isinstance(event["detail"], dict):
        return event["detail"]
    body = event.get("body")
    if isinstance(body, str):
        return json.loads(body)
    if isinstance(body, dict):
        return body
    return event
