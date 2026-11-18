"""Generate first-evaluation plots from existing data and artifacts only.

This module deliberately contains no estimator ``fit`` calls, CV, optimization,
or model export. It loads the saved artifact and performs inference only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix

from pathsnap.backend.model_service import ModelService
from pathsnap.data_pipeline.candidates import generate_candidates
from pathsnap.data_pipeline.features import FEATURE_NAMES, candidate_feature_rows, rows_to_matrix
from pathsnap.data_pipeline.labels import reference_arc_per_observation
from pathsnap.data_pipeline.loaders import DatasetLayout, load_trip
from pathsnap.data_pipeline.road_graph import RoadGraph, project_lon_lat
from pathsnap.visualization.folium_maps import create_trip_map


def _student_trips(root: Path):
    layout = DatasetLayout(root)
    return [load_trip(files, include_route=True) for files in layout.discover("student_test", require_route=True)]


def plot_speed_distribution(trips, output: Path) -> None:
    speeds = []
    for trip in trips:
        projected = project_lon_lat(trip.track[:, :2], float(trip.track[:, 0].mean()), float(trip.track[:, 1].mean()))
        deltas = np.diff(projected, axis=0)
        dt = np.diff(trip.track[:, 2])
        valid = dt > 0
        speeds.extend((np.linalg.norm(deltas[valid], axis=1) / dt[valid]).tolist())
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.hist(speeds, bins=50, color="#1f77b4", alpha=0.85, edgecolor="white")
    ax.set_title("GPS movement speed distribution — student-test trips")
    ax.set_xlabel("Movement speed (m/s)")
    ax.set_ylabel("GPS intervals")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


def plot_distance_distribution(trips, output: Path) -> None:
    distances = []
    for trip in trips:
        graph = RoadGraph.from_trip(trip)
        candidates = generate_candidates(trip, graph, radius_m=50.0, max_candidates=8)
        distances.extend(candidate.distance_m for group in candidates for candidate in group)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.hist(distances, bins=50, color="#ff7f0e", alpha=0.85, edgecolor="white")
    ax.set_title("GPS-to-road candidate distance distribution — student-test trips")
    ax.set_xlabel("Point-to-segment distance (m)")
    ax.set_ylabel("Candidate segments")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


def plot_model_comparison(csv_path: Path, output: Path) -> None:
    frame = pd.read_csv(csv_path)
    required = {"model", "cv_macro_f1", "top1_accuracy"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"model comparison is missing columns: {sorted(missing)}")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    labels = frame["model"].str.replace("_", " ").str.title()
    axes[0].bar(labels, frame["cv_macro_f1"], color="#2ca02c")
    axes[0].set_title("Cross-validation Macro F1")
    axes[0].set_ylabel("Macro F1")
    axes[1].bar(labels, frame["top1_accuracy"], color="#9467bd")
    axes[1].set_title("Student-test observation Top-1 accuracy")
    axes[1].set_ylabel("Top-1 accuracy")
    for ax in axes:
        ax.tick_params(axis="x", rotation=35)
        ax.set_ylim(0, 1)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Five-model comparison from existing experiment results")
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


def plot_confusion_matrix(root: Path, model_path: Path, output: Path) -> dict[str, int]:
    import joblib

    model = joblib.load(model_path)
    y_true, y_pred = [], []
    for trip in _student_trips(root):
        graph = RoadGraph.from_trip(trip)
        candidates = generate_candidates(trip, graph, radius_m=50.0, max_candidates=8)
        rows = candidate_feature_rows(trip, candidates, graph)
        if not rows:
            continue
        probabilities = model.predict_proba(rows_to_matrix(rows))
        positive_index = list(model.classes_).index(1)
        predictions = (probabilities[:, positive_index] >= 0.5).astype(int)
        reference = reference_arc_per_observation(trip, graph)
        offset = 0
        for observation_id, group in enumerate(candidates):
            label = int(reference[observation_id])
            for candidate in group:
                y_true.append(int(candidate.arc_id == label))
                y_pred.append(int(predictions[offset]))
                offset += 1
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1])
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ConfusionMatrixDisplay(matrix, display_labels=["Non-reference candidate", "Heuristic reference candidate"]).plot(ax=ax, cmap="Blues", values_format="d", colorbar=False)
    ax.set_title("HistGradientBoosting candidate confusion matrix\nstudent-test inference; heuristic labels")
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)
    return {"true_negative": int(matrix[0, 0]), "false_positive": int(matrix[0, 1]), "false_negative": int(matrix[1, 0]), "true_positive": int(matrix[1, 1])}


def generate_all(data_root: Path, model_path: Path, comparison_csv: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    trips = _student_trips(data_root)
    plot_speed_distribution(trips, output_dir / "gps_speed_distribution.png")
    plot_distance_distribution(trips, output_dir / "gps_to_road_distance_distribution.png")
    plot_model_comparison(comparison_csv, output_dir / "five_model_comparison.png")
    confusion_counts = plot_confusion_matrix(data_root, model_path, output_dir / "histgradientboosting_confusion_matrix.png")
    map_trip = trips[0]
    graph = RoadGraph.from_trip(map_trip)
    service = ModelService(data_root, model_path)
    prediction = service.predict(map_trip.files.trip_id)
    create_trip_map(map_trip, graph, prediction["predicted_segments"], output_path=output_dir / "gps_matched_route_map.html")
    manifest = {"student_trip_for_map": map_trip.files.trip_id, "student_trips_used_for_distributions": len(trips), "confusion_matrix_counts": confusion_counts, "comparison_csv": str(comparison_csv), "model_path": str(model_path), "training_performed": False}
    (output_dir / "plot_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--comparison", required=True, type=Path)
    parser.add_argument("--output-dir", default="results/plots", type=Path)
    args = parser.parse_args()
    print(generate_all(args.data_root, args.model, args.comparison, args.output_dir))


if __name__ == "__main__":
    main()
