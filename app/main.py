from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles

from app.config import Settings, get_settings
from app.aws_tools import AwsToolsUnavailable
from app.models import HealthResponse, Item, ItemCreate, JobHealthDecision, PreflightRequest, RegionResponse
from app.service import run_preflight
from app.store import InMemoryItemStore, item_store


app = FastAPI(
    title="EC2Check API",
    version="0.1.0",
    description="GPU fleet pre-flight health checks for EC2 training jobs.",
)


def get_item_store() -> InMemoryItemStore:
    return item_store


@app.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.service_version,
    )


@app.get("/ready", response_model=HealthResponse)
async def ready(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ready",
        service=settings.app_name,
        version=settings.service_version,
    )


@app.get("/regions/current", response_model=RegionResponse)
async def current_region(settings: Settings = Depends(get_settings)) -> RegionResponse:
    return RegionResponse(region=settings.aws_region)


@app.post("/v1/preflight-check", response_model=JobHealthDecision)
async def preflight_check(
    payload: PreflightRequest,
    settings: Settings = Depends(get_settings),
) -> JobHealthDecision:
    try:
        return await run_preflight(
            payload,
            report_dir=settings.report_dir,
            aws_profile=settings.aws_profile,
            aws_region=settings.aws_region,
        )
    except AwsToolsUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: ItemCreate,
    settings: Settings = Depends(get_settings),
    store: InMemoryItemStore = Depends(get_item_store),
) -> Item:
    item = Item(
        user_id=payload.user_id,
        payload=payload.payload,
        region=settings.aws_region,
    )
    return await store.create(item)


@app.get("/items/{item_id}", response_model=Item)
async def get_item(
    item_id: UUID,
    store: InMemoryItemStore = Depends(get_item_store),
) -> Item:
    item = await store.get(item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return item


app.mount("/", StaticFiles(directory="app/static", html=True), name="ui")
