"""Public API request and response schemas; no reference labels are exposed."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    trip_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")


class Metrics(BaseModel):
    accuracy: float | None = None
    route_continuity: float | None = None


class PredictResponse(BaseModel):
    trip_id: str
    status: str
    predicted_segments: list[int | None]
    predicted_route_coordinates: list[list[float]]
    gps_coordinates: list[list[float]]
    metrics: Metrics
    inference_time_ms: float


class StatusResponse(BaseModel):
    ready: bool
    model_loaded: bool
    model_version: int | None = None

