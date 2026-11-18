"""Grouped five-model candidate ranking experiments.

Run explicitly to generate genuine experiment outputs; no metrics are stored
in source code.  `.route` is loaded only in this training/evaluation module.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, log_loss, precision_score, recall_score
from sklearn.model_selection import GroupKFold
from sklearn.base import clone

from pathsnap.data_pipeline.candidates import generate_candidates
from pathsnap.data_pipeline.features import FEATURE_NAMES, candidate_feature_rows
from pathsnap.data_pipeline.labels import label_candidates
from pathsnap.data_pipeline.loaders import DatasetLayout, load_trip
from pathsnap.data_pipeline.road_graph import RoadGraph
from pathsnap.ml_pipeline.models import model_factories


def build_dataset(root: Path, partition: str, radius_m: float = 50.0, max_candidates: int = 8, negatives_per_observation: int = 3) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for files in DatasetLayout(root).discover(partition, require_route=True):
        trip = load_trip(files, include_route=True)
        graph = RoadGraph.from_trip(trip)
        candidates = generate_candidates(trip, graph, radius_m=radius_m, max_candidates=max_candidates)
        feature_rows = candidate_feature_rows(trip, candidates, graph)
        label_rows = label_candidates(trip, candidates, graph)
        for features, labels in zip(feature_rows, label_rows, strict=True):
            rows.append({**features, **labels, "trip_id": files.trip_id})
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError(f"No candidate rows found for partition {partition}")
    if negatives_per_observation < 0:
        raise ValueError("negatives_per_observation must be non-negative")
    # Keep all positives and a deterministic rank-ordered negative sample per
    # observation. This preserves the ranking task while keeping KNN tractable.
    frame["_negative_order"] = frame.groupby(["trip_id", "observation_id"])["target"].transform(lambda values: (values == 0).cumsum())
    selected = (frame["target"] == 1) | (frame["_negative_order"] <= negatives_per_observation)
    return frame.loc[selected].drop(columns="_negative_order").reset_index(drop=True)


def _predict_positive(model, values: np.ndarray) -> np.ndarray:
    probabilities = model.predict_proba(values)
    classes = list(model.classes_)
    return probabilities[:, classes.index(1)] if 1 in classes else np.zeros(len(values))


def observation_top1(frame: pd.DataFrame, scores: np.ndarray) -> tuple[float, float]:
    work = frame[["trip_id", "observation_id", "target", "candidate_miss"]].copy()
    work["score"] = scores
    best = work.loc[work.groupby(["trip_id", "observation_id"])["score"].idxmax()]
    return float(best["target"].mean()), float(work["candidate_miss"].groupby([work["trip_id"], work["observation_id"]]).first().mean())


def evaluate_model(model, frame: pd.DataFrame, values: np.ndarray) -> dict[str, float]:
    scores = _predict_positive(model, values)
    predicted = (scores >= 0.5).astype(int)
    top1, miss_rate = observation_top1(frame, scores)
    return {
        "accuracy": float((predicted == frame["target"].to_numpy()).mean()),
        "precision": float(precision_score(frame["target"], predicted, zero_division=0)),
        "recall": float(recall_score(frame["target"], predicted, zero_division=0)),
        "macro_f1": float(f1_score(frame["target"], predicted, average="macro", zero_division=0)),
        "top1_accuracy": top1,
        "candidate_miss_rate": miss_rate,
        "log_loss": float(log_loss(frame["target"], np.column_stack([1 - scores, scores]), labels=[0, 1])),
    }


def run_experiment(root: Path, output_dir: Path, seed: int = 42, folds: int = 5, negatives_per_observation: int = 3) -> pd.DataFrame:
    train = build_dataset(root, "train", negatives_per_observation=negatives_per_observation)
    student = build_dataset(root, "student_test", negatives_per_observation=negatives_per_observation)
    values_train = train.loc[:, FEATURE_NAMES].to_numpy(dtype=float)
    values_student = student.loc[:, FEATURE_NAMES].to_numpy(dtype=float)
    groups = train["trip_id"].to_numpy()
    splitter = GroupKFold(n_splits=folds)
    records: list[dict[str, float | str]] = []
    for name, factory in model_factories(seed).items():
        fold_scores: list[float] = []
        started = time.perf_counter()
        for train_index, validation_index in splitter.split(values_train, train["target"], groups):
            model = clone(factory)
            model.fit(values_train[train_index], train["target"].to_numpy()[train_index])
            fold_scores.append(evaluate_model(model, train.iloc[validation_index], values_train[validation_index])["macro_f1"])
        model = factory
        model.fit(values_train, train["target"])
        inference_started = time.perf_counter()
        metrics = evaluate_model(model, student, values_student)
        inference_ms = (time.perf_counter() - inference_started) * 1000 / max(len(student), 1)
        records.append({"model": name, "cv_macro_f1": float(np.mean(fold_scores)), **metrics, "inference_ms_per_candidate": inference_ms, "training_seconds": time.perf_counter() - started})
    output_dir.mkdir(parents=True, exist_ok=True)
    result = pd.DataFrame(records)
    result.to_csv(output_dir / "model_comparison.csv", index=False)
    (output_dir / "experiment_config.json").write_text(json.dumps({"seed": seed, "folds": folds, "feature_names": FEATURE_NAMES, "negatives_per_observation": negatives_per_observation}, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output-dir", default="results/models", type=Path)
    args = parser.parse_args()
    print(run_experiment(args.data_root, args.output_dir).to_string(index=False))


if __name__ == "__main__":
    main()
