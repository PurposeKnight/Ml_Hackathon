"""Environment-backed backend configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_root: Path = Path(os.getenv("PATHSNAP_DATA_ROOT", "Student folder/Student folder"))
    model_path: Path = Path(os.getenv("MODEL_PATH", "pathsnap/ml_pipeline/artifacts/final_model.joblib"))
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

