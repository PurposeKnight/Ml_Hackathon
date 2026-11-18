"""Refit the tuned model, compare it with the untuned baseline, and export it."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from pathsnap.data_pipeline.features import FEATURE_NAMES
from pathsnap.ml_pipeline.artifacts import export_model
from pathsnap.ml_pipeline.train_models import build_dataset, evaluate_model


def finalize(root: Path, results_dir: Path, artifact_path: Path, folds: int = 3) -> pd.DataFrame:
    train = build_dataset(root, "train", max_candidates=4, negatives_per_observation=1)
    student = build_dataset(root, "student_test", max_candidates=4, negatives_per_observation=1)
    values_train = train.loc[:, FEATURE_NAMES].to_numpy(dtype=float)
    values_student = student.loc[:, FEATURE_NAMES].to_numpy(dtype=float)
    best_params = json.loads((results_dir / "best_params.json").read_text(encoding="utf-8"))["best_params"]
    baseline = HistGradientBoostingClassifier(max_iter=150, learning_rate=0.08, max_leaf_nodes=31, random_state=42)
    tuned = HistGradientBoostingClassifier(**best_params, random_state=42)
    records = []
    for name, model in (("untuned_hist_gradient_boosting", baseline), ("tuned_hist_gradient_boosting", tuned)):
        started = time.perf_counter()
        model.fit(values_train, train["target"])
        metrics = evaluate_model(model, student, values_student)
        records.append({"model": name, **metrics, "fit_seconds": time.perf_counter() - started})
        if name == "tuned_hist_gradient_boosting":
            export_model(model, artifact_path, FEATURE_NAMES, {"model_name": name, "parameters": best_params, "training_partition": "train", "evaluation_partition": "student_test"})
    output = pd.DataFrame(records)
    results_dir.mkdir(parents=True, exist_ok=True)
    output.to_csv(results_dir / "tuned_vs_untuned_student.csv", index=False)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--results-dir", default="results/optimization", type=Path)
    parser.add_argument("--artifact", default="pathsnap/ml_pipeline/artifacts/final_model.joblib", type=Path)
    args = parser.parse_args()
    print(finalize(args.data_root, args.results_dir, args.artifact).to_string(index=False))


if __name__ == "__main__":
    main()
