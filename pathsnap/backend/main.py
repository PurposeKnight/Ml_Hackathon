"""FastAPI application entrypoint for Laptop 1."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .model_service import ModelService
from .schemas import PredictRequest, PredictResponse, StatusResponse

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model_service = ModelService(settings.data_root, settings.model_path)
    yield


app = FastAPI(title="PathSnap Laptop 1 API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["*"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/status", response_model=StatusResponse)
def status(request: Request) -> StatusResponse:
    service = getattr(request.app.state, "model_service", None)
    return StatusResponse(ready=service is not None, model_loaded=service is not None, model_version=service.manifest.get("artifact_version") if service else None)


@app.get("/api/trips", response_model=list[str])
def trips(request: Request) -> list[str]:
    return request.app.state.model_service.available_trips()


@app.post("/api/predict", response_model=PredictResponse)
def predict(payload: PredictRequest, request: Request) -> PredictResponse:
    try:
        result = request.app.state.model_service.predict(payload.trip_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown trip ID") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Prediction failed") from exc
    return PredictResponse.model_validate(result)
