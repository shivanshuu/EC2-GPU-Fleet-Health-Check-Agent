from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Decision(StrEnum):
    GO = "GO"
    WARN = "WARN"
    FAIL = "FAIL"


class CheckStatus(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class Severity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CheckDepth(StrEnum):
    PHASE_1_FAST = "PHASE_1_FAST"
    PHASE_2_LIGHT = "PHASE_2_LIGHT"
    FULL_PHASE_2 = "FULL_PHASE_2"


class ItemCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)


class Item(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    payload: dict[str, Any]
    region: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class RegionResponse(BaseModel):
    region: str


class JobProfile(BaseModel):
    name: str = "distributed-gpu"
    expected_gpu_count: int = 8
    requires_efa: bool = True
    requires_fsx: bool = True
    requires_nvlink: bool = True
    fast_check_timeout_seconds: int = 30
    standard_check_timeout_seconds: int = 300
    block_on_recent_critical_xid: bool = True
    warn_on_ecc_errors: bool = True
    minimum_free_disk_gb: int = 100


class PreflightRequest(BaseModel):
    job_id: str = Field(min_length=1, max_length=128)
    profile: str | JobProfile = "distributed-gpu"
    instance_ids: list[str] = Field(min_length=1)
    mode: Literal["mock", "aws"] = "mock"
    apply_actions: bool = False


class HealthCheckResult(BaseModel):
    instance_id: str
    check_name: str
    status: CheckStatus
    severity: Severity
    observed: str
    expected: str | None = None
    evidence: str
    remediation: str | None = None


class InstanceHealthReport(BaseModel):
    instance_id: str
    status: Decision
    risk_level: RiskLevel
    check_depth: CheckDepth
    checks: list[HealthCheckResult]
    recommended_action: str | None = None


class AggregateCounts(BaseModel):
    passed: int = 0
    warned: int = 0
    failed: int = 0


class JobHealthDecision(BaseModel):
    job_id: str
    profile: str
    decision: Decision
    summary: str
    aggregate_counts: AggregateCounts
    instances: list[InstanceHealthReport]
    recommended_action: str
    report_markdown: str
    report_uri: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
