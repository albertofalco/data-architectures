"""FastAPI app for deployment monitoring and lightweight prediction browsing."""

# ==================== IMPORTS ====================

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .services import (
    DeploymentAPIError,
    PredictionReadError,
    list_predictions,
    list_runs,
    load_deployment_config,
    load_run,
    model_summaries,
    run_inference_for_manifest,
    wide_prediction_preview,
)


# ==================== CONFIGURATION ====================

APP_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Data Architectures Deployment", version="0.1.0")
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
templates = Jinja2Templates(directory=APP_DIR / "templates")


# ==================== REQUEST MODELS ====================

class BatchInferenceRequest(BaseModel):
    """Request body for manifest-scoped inference."""

    manifest: str
    source: str | None = None
    models: list[str] | None = None
    skip_clickhouse: bool = False


# ==================== API ENDPOINTS ====================

@app.get("/health")
def health() -> dict[str, str]:
    """Return API health."""
    return {"status": "ok"}


@app.get("/api/runs")
def api_runs() -> list[dict[str, Any]]:
    """List inference runs."""
    try:
        return list_runs(load_deployment_config())
    except DeploymentAPIError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.get("/api/runs/{run_id}")
def api_run(run_id: str) -> dict[str, Any]:
    """Return one run manifest."""
    try:
        return load_run(load_deployment_config(), run_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}") from error
    except DeploymentAPIError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.get("/api/runs/{run_id}/model-summaries")
def api_run_model_summaries(run_id: str) -> list[dict[str, Any]]:
    """Return per-model prediction counts, timings, and TARGET metrics."""
    try:
        return model_summaries(load_deployment_config(), run_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}") from error
    except PredictionReadError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except DeploymentAPIError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.get("/api/predictions")
def api_predictions(
    run_id: str | None = None,
    model_name: str | None = None,
    limit: int = Query(default=100, ge=1, le=5000),
) -> list[dict[str, Any]]:
    """List local prediction rows."""
    try:
        return list_predictions(
            config=load_deployment_config(),
            run_id=run_id,
            model_name=model_name,
            limit=limit,
        )
    except PredictionReadError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.post("/api/inference/batch")
def api_inference_batch(payload: BatchInferenceRequest) -> dict[str, Any]:
    """Run manifest-scoped inference."""
    try:
        return run_inference_for_manifest(
            config=load_deployment_config(),
            manifest=payload.manifest,
            source=payload.source,
            models=payload.models,
            skip_clickhouse=payload.skip_clickhouse,
        )
    except DeploymentAPIError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """Render deployment home."""
    config = load_deployment_config()
    try:
        runs = list_runs(config)
    except DeploymentAPIError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "runs": runs,
            "config": config,
        },
    )


@app.get("/runs/{run_id}", response_class=HTMLResponse)
def run_detail(request: Request, run_id: str) -> HTMLResponse:
    """Render run details."""
    config = load_deployment_config()
    try:
        run = load_run(config, run_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}") from error
    except DeploymentAPIError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    try:
        predictions = wide_prediction_preview(config=config, run_id=run_id, limit=50)
        summaries = model_summaries(config=config, run_id=run_id)
    except PredictionReadError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except DeploymentAPIError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    return templates.TemplateResponse(
        "run_detail.html",
        {
            "request": request,
            "run": run,
            "model_summaries": summaries,
            "predictions": predictions,
        },
    )
