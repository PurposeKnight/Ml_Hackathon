"""Versioned export/load helpers for model and preprocessing artifacts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def export_model(model: Any, output_path: str | Path, feature_names: tuple[str, ...], metadata: dict[str, Any] | None = None) -> Path:
    try:
        import joblib
    except ImportError as exc:
        raise RuntimeError("joblib is required to export model artifacts") from exc
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, destination)
    manifest = {
        "artifact_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "feature_names": list(feature_names),
        **(metadata or {}),
    }
    destination.with_suffix(destination.suffix + ".json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return destination


def load_model(path: str | Path):
    try:
        import joblib
    except ImportError as exc:
        raise RuntimeError("joblib is required to load model artifacts") from exc
    return joblib.load(path)
