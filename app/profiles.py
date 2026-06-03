import json
from pathlib import Path

from app.models import JobProfile


PROFILE_DIR = Path(__file__).resolve().parent.parent / "profiles"


def load_profile(profile: str | JobProfile) -> JobProfile:
    if isinstance(profile, JobProfile):
        return profile

    profile_path = Path(profile)
    if profile_path.suffix == ".json" and profile_path.exists():
        return _load_profile_file(profile_path)

    named_profile = PROFILE_DIR / f"{profile}.json"
    if named_profile.exists():
        return _load_profile_file(named_profile)

    if profile == "distributed-gpu":
        return JobProfile()

    raise ValueError(f"Unknown job profile: {profile}")


def _load_profile_file(path: Path) -> JobProfile:
    with path.open("r", encoding="utf-8") as profile_file:
        return JobProfile.model_validate(json.load(profile_file))
