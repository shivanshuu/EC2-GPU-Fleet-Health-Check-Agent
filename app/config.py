import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_name: str = "EC2Check"
    aws_region: str = "local"
    aws_profile: str = "OAI"
    service_version: str = "0.1.0"
    report_dir: str = "reports"
    default_profile: str = "distributed-gpu"
    default_mode: str = "mock"


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("EC2CHECK_APP_NAME", "EC2Check"),
        aws_region=os.getenv("EC2CHECK_AWS_REGION", "local"),
        aws_profile=os.getenv("EC2CHECK_AWS_PROFILE", "OAI"),
        service_version=os.getenv("EC2CHECK_SERVICE_VERSION", "0.1.0"),
        report_dir=os.getenv("EC2CHECK_REPORT_DIR", "reports"),
        default_profile=os.getenv("EC2CHECK_DEFAULT_PROFILE", "distributed-gpu"),
        default_mode=os.getenv("EC2CHECK_DEFAULT_MODE", "mock"),
    )
