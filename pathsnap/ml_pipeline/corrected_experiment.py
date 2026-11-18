"""Corrected five-model experiment with fold-local training-only sampling.

This module intentionally does not tune or read evaluator-test data. It builds
complete candidate tables, samples only the training rows of each fold, and
evaluates every validation/student candidate row.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix, f1_score, log_loss, precision_score, recall_score
from sklearn.model_selection import GroupKFold

from pathsnap.data_pipeline.candidates import generate_candidates
from pathsnap.data_pipeline.features import FEATURE_NAMES, candidate_feature_rows, rows_to_matrix
from pathsnap.data_pipeline.labels import label_candidates, reference_arc_per_observation
from pathsnap.data_pipeline.loaders import DatasetLayout, load_trip
from pathsnap.data_pipeline.road_graph import RoadGraph
from pathsnap.ml_pipeline.artifacts import export_model, load_model
from pathsnap.ml_pipeline.models import model_factories


def complete_partition(root: Path, partition: str, max_candidates: int = 4) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return all candidate rows and per-observation coverage metadata."""
    rows: list[dict] = []
    observations: list[dict] = []
    for files in DatasetLayout(root).discover(partition, require_route=True):
        trip = load_trip(files, include_route=True)
        graph = RoadGraph.from_trip(trip)
        candidates = generate_candidates(trip, graph, radius_m=50.0, max_candidates=max_candidates)
        feature_rows = candidate_feature_rows(trip, candidates, graph)
        label_rows = label_candidates(trip, candidates, graph)
        references = reference_arc_per_observation(trip, graph)
        for observation_id, group in enumerate(candidates):
            reference = int(references[observation_id])
            observations.append({
                "trip_id": files.trip_id,
                "observation_id": observation_id,
                "has_candidates": bool(group),
                "candidate_miss": not any(candidate.arc_id == reference for candidate in group),
            })
        rows.extend({**features, **labels, "trip_id": files.trip_id} for features, labels in zip(feature_rows, label_rows, strict=True))
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError(f"No candidates found in {partition}")
    return frame.reset_index(drop=True), pd.DataFrame(observations)


def sample_training_rows(frame: pd.DataFrame, negatives_per_observation: int = 1) -> pd.DataFrame:
    """Keep all positives and deterministic negatives; training data only."""
    if negatives_per_observation < 0:
        raise ValueError("negatives_per_observation must be non-negative")
    negative_order = frame["target"].eq(0).groupby([frame["trip_id"], frame["observation_id"]]).cumsum()
    selected = (frame["target"] == 1) | (negative_order <= negatives_per_observation)
    return frame.loc[selected].reset_index(drop=True)


def _positive_scores(model, values: np.ndarray) -> np.ndarray:
    probabilities = model.predict_proba(values)
    classes = list(model.classes_)
    return probabilities[:, classes.index(1)] if 1 in classes else np.zeros(len(values))


def evaluate_candidate_rows(model, frame: pd.DataFrame, observations: pd.DataFrame) -> dict[str, float | int]:
    scores = _positive_scores(model, frame.loc[:, FEATURE_NAMES].to_numpy(dtype=float))
    predicted = (scores >= 0.5).astype(int)
    top = frame[["trip_id", "observation_id", "target"]].copy()
    top["score"] = scores
    best = top.loc[top.groupby(["trip_id", "observation_id"])["score"].idxmax()]
    observed = observations[observations["has_candidates"]]
    correct = float(best["target"].sum())
    total_observations = len(observations)
    candidate_observations = len(observed)
    misses = int(observations["candidate_miss"].sum())
    return {
        "accuracy": float((predicted == frame["target"].to_numpy()).mean()),
        "precision": float(precision_score(frame["target"], predicted, zero_division=0)),
        "recall": float(recall_score(frame["target"], predicted, zero_division=0)),
        "macro_f1": float(f1_score(frame["target"], predicted, average="macro", zero_division=0)),
        "top1_accuracy_with_candidates": float(correct / candidate_observations) if candidate_observations else 0.0,
        "top1_accuracy_all_observations": float(correct / total_observations) if total_observations else 0.0,
        "candidate_miss_rate": float(misses / total_observations) if total_observations else 0.0,
        "zero_candidate_observations": int((~observations["has_candidates"]).sum()),
        "total_observations": int(total_observations),
        "candidate_rows": int(len(frame)),
        "log_loss": float(log_loss(frame["target"], np.column_stack([1 - scores, scores]), labels=[0, 1])),
    }


def _plot_comparisons(summary: pd.DataFrame, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 5.5))
    labels = summary["model"].str.replace("_", " ").str.title()
    ax.bar(labels, summary["cv_macro_f1"], color="#2ca02c")
    ax.set_title("Corrected five-model grouped-CV Macro F1")
    ax.set_ylabel("Mean validation Macro F1")
    ax.set_ylim(0, 1)
    ax.tick_params(axis="x", rotation=30)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


def run(root: Path, output_dir: Path, seed: int = 42, folds: int = 3, negatives_per_observation: int = 1, max_candidates: int = 4) -> pd.DataFrame:
    train, train_observations = complete_partition(root, "train", max_candidates)
    student, student_observations = complete_partition(root, "student_test", max_candidates)
    values = train.loc[:, FEATURE_NAMES].to_numpy(dtype=float)
    groups = train["trip_id"].to_numpy()
    targets = train["target"].to_numpy()
    splitter = GroupKFold(n_splits=folds)
    fold_records: list[dict] = []
    summary_records: list[dict] = []
    for name, factory in model_factories(seed).items():
        fold_scores = []
        started = time.perf_counter()
        for fold, (train_index, validation_index) in enumerate(splitter.split(values, targets, groups), 1):
            fold_train = sample_training_rows(train.iloc[train_index], negatives_per_observation)
            model = clone(factory)
            model.fit(fold_train.loc[:, FEATURE_NAMES], fold_train["target"])
            validation_frame = train.iloc[validation_index]
            validation_observations = train_observations[train_observations["trip_id"].isin(validation_frame["trip_id"].unique())]
            metrics = evaluate_candidate_rows(model, validation_frame, validation_observations)
            fold_scores.append(metrics["macro_f1"])
            fold_records.append({"model": name, "fold": fold, "training_rows": len(fold_train), "validation_rows": len(validation_frame), **metrics})
        final_train = sample_training_rows(train, negatives_per_observation)
        final_model = clone(factory)
        final_model.fit(final_train.loc[:, FEATURE_NAMES], final_train["target"])
        inference_start = time.perf_counter()
        student_metrics = evaluate_candidate_rows(final_model, student, student_observations)
        inference_ms = (time.perf_counter() - inference_start) * 1000 / max(len(student), 1)
        summary_records.append({"model": name, "cv_macro_f1": float(np.mean(fold_scores)), **student_metrics, "inference_ms_per_candidate": inference_ms, "training_seconds": time.perf_counter() - started})
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = pd.DataFrame(summary_records).sort_values("cv_macro_f1", ascending=False).reset_index(drop=True)
    folds_frame = pd.DataFrame(fold_records)
    summary.to_csv(output_dir / "model_comparison.csv", index=False)
    folds_frame.to_csv(output_dir / "cross_validation_results.csv", index=False)
    config = {"seed": seed, "folds": folds, "feature_names": FEATURE_NAMES, "radius_m": 50.0, "max_candidates": max_candidates, "training_negatives_per_observation": negatives_per_observation, "validation_negative_sampling": None, "student_negative_sampling": None, "training_trips": 80, "student_test_trips": 10}
    (output_dir / "experiment_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    _plot_comparisons(summary, output_dir / "model_comparison.png")
    top1 = summary["top1_accuracy_all_observations"]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.bar(summary["model"].str.replace("_", " ").str.title(), top1, color="#9467bd")
    ax.set_title("Corrected student-test Top-1 accuracy (complete candidates)")
    ax.set_ylabel("Top-1 accuracy, zero-candidate observations count as incorrect")
    ax.set_ylim(0, 1)
    ax.tick_params(axis="x", rotation=30)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "top1_accuracy_comparison.png", dpi=180)
    plt.close(fig)
    selected = str(summary.iloc[0]["model"])
    final_model = model_factories(seed)[selected]
    final_train = sample_training_rows(train, negatives_per_observation)
    final_model.fit(final_train.loc[:, FEATURE_NAMES], final_train["target"])
    artifact_path = output_dir / "selected_model.joblib"
    export_model(final_model, artifact_path, FEATURE_NAMES, {"model_name": selected, "selection_metric": "mean_grouped_cv_macro_f1", "training_sampling": f"all positives plus {negatives_per_observation} negatives per observation", "candidate_radius_m": 50.0, "max_candidates": max_candidates})
    scores = _positive_scores(final_model, student.loc[:, FEATURE_NAMES].to_numpy(dtype=float))
    y_true = student["target"].to_numpy(dtype=int)
    y_pred = (scores >= 0.5).astype(int)
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1])
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ConfusionMatrixDisplay(matrix, display_labels=["Non-reference candidate", "Reference candidate"]).plot(ax=ax, cmap="Blues", values_format="d", colorbar=False)
    ax.set_title(f"Selected model confusion matrix — {selected}\ncomplete student-test candidates")
    fig.tight_layout()
    fig.savefig(output_dir / "confusion_matrix.png", dpi=180)
    plt.close(fig)
    (output_dir / "training_summary.md").write_text("# Corrected five-model experiment\n\n" + summary.to_markdown(index=False) + f"\n\nSelected model: **{selected}**, chosen by mean 3-fold GroupKFold validation Macro F1. Training negatives were sampled only inside each training fold/final fit; validation and student-test candidates were complete. Zero-candidate observations are reported separately and count as incorrect in `top1_accuracy_all_observations`.\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output-dir", default="results/corrected_models", type=Path)
    parser.add_argument("--folds", default=3, type=int)
    parser.add_argument("--negatives-per-observation", default=1, type=int)
    parser.add_argument("--max-candidates", default=4, type=int)
    args = parser.parse_args()
    print(run(args.data_root, args.output_dir, folds=args.folds, negatives_per_observation=args.negatives_per_observation, max_candidates=args.max_candidates).to_string(index=False))


if __name__ == "__main__":
    main()
