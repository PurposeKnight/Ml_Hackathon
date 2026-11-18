"""Corrected Bayesian optimization for the selected Logistic Regression model.

The candidate tables are complete. Optuna only sees grouped validation scores;
negative sampling is performed inside each fold's training partition.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from pathsnap.data_pipeline.features import FEATURE_NAMES
from pathsnap.ml_pipeline.artifacts import export_model
from pathsnap.ml_pipeline.corrected_experiment import complete_partition, evaluate_candidate_rows, sample_training_rows


def _model(params: dict, seed: int) -> Pipeline:
    return Pipeline([
        ("scale", StandardScaler()),
        ("model", LogisticRegression(
            C=float(params["C"]),
            class_weight=params["class_weight"],
            max_iter=int(params["max_iter"]),
            random_state=seed,
        )),
    ])


def run(root: Path, output_dir: Path, trials: int = 12, folds: int = 3, seed: int = 42, negatives_per_observation: int = 1, max_candidates: int = 4) -> dict:
    import optuna
    from sklearn.model_selection import GroupKFold

    train, train_observations = complete_partition(root, "train", max_candidates)
    student, student_observations = complete_partition(root, "student_test", max_candidates)
    splitter = GroupKFold(n_splits=folds)
    output_dir.mkdir(parents=True, exist_ok=True)
    fold_indices = list(splitter.split(train, train["target"], train["trip_id"]))

    def objective(trial: optuna.Trial) -> float:
        params = {
            "C": trial.suggest_float("C", 1e-3, 1e2, log=True),
            "class_weight": trial.suggest_categorical("class_weight", ["balanced", None]),
            "max_iter": trial.suggest_int("max_iter", 200, 800, step=100),
        }
        scores = []
        for train_index, validation_index in fold_indices:
            fold_train = sample_training_rows(train.iloc[train_index], negatives_per_observation)
            model = _model(params, seed)
            model.fit(fold_train.loc[:, FEATURE_NAMES], fold_train["target"])
            validation = train.iloc[validation_index]
            validation_obs = train_observations[train_observations["trip_id"].isin(validation["trip_id"].unique())]
            scores.append(evaluate_candidate_rows(model, validation, validation_obs)["macro_f1"])
        return float(np.mean(scores))

    sampler = optuna.samplers.TPESampler(seed=seed)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    started = time.perf_counter()
    study.optimize(objective, n_trials=trials)
    elapsed = time.perf_counter() - started
    study.trials_dataframe().to_csv(output_dir / "corrected_logistic_optuna_trials.csv", index=False)

    baseline_params = {"C": 1.0, "class_weight": "balanced", "max_iter": 400}
    tuned_params = study.best_params
    baseline_scores = []
    tuned_scores = []
    for train_index, validation_index in fold_indices:
        fold_train = sample_training_rows(train.iloc[train_index], negatives_per_observation)
        validation = train.iloc[validation_index]
        validation_obs = train_observations[train_observations["trip_id"].isin(validation["trip_id"].unique())]
        baseline = _model(baseline_params, seed)
        tuned = _model(tuned_params, seed)
        baseline.fit(fold_train.loc[:, FEATURE_NAMES], fold_train["target"])
        tuned.fit(fold_train.loc[:, FEATURE_NAMES], fold_train["target"])
        baseline_scores.append(evaluate_candidate_rows(baseline, validation, validation_obs)["macro_f1"])
        tuned_scores.append(evaluate_candidate_rows(tuned, validation, validation_obs)["macro_f1"])

    baseline_model = _model(baseline_params, seed)
    tuned_model = _model(tuned_params, seed)
    final_train = sample_training_rows(train, negatives_per_observation)
    baseline_model.fit(final_train.loc[:, FEATURE_NAMES], final_train["target"])
    tuned_model.fit(final_train.loc[:, FEATURE_NAMES], final_train["target"])
    baseline_student = evaluate_candidate_rows(baseline_model, student, student_observations)
    tuned_student = evaluate_candidate_rows(tuned_model, student, student_observations)
    comparison = pd.DataFrame([
        {"model": "baseline_logistic_regression", "cv_macro_f1": float(np.mean(baseline_scores)), **baseline_student},
        {"model": "tuned_logistic_regression", "cv_macro_f1": float(np.mean(tuned_scores)), **tuned_student},
    ])
    comparison.to_csv(output_dir / "corrected_logistic_tuned_vs_baseline.csv", index=False)
    selected = "tuned_logistic_regression" if comparison.loc[1, "cv_macro_f1"] > comparison.loc[0, "cv_macro_f1"] else "baseline_logistic_regression"
    selected_model = tuned_model if selected == "tuned_logistic_regression" else baseline_model
    export_model(selected_model, output_dir / "selected_model.joblib", FEATURE_NAMES, {"model_name": selected, "selection_metric": "mean_grouped_cv_macro_f1_after_bayesian_optimization", "candidate_radius_m": 50.0, "max_candidates": max_candidates, "training_sampling": f"all positives plus {negatives_per_observation} negatives per observation"})
    scores = selected_model.predict_proba(student.loc[:, FEATURE_NAMES])[:, list(selected_model.classes_).index(1)]
    matrix = confusion_matrix(student["target"], (scores >= 0.5).astype(int), labels=[0, 1])
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ConfusionMatrixDisplay(matrix, display_labels=["Non-reference candidate", "Reference candidate"]).plot(ax=ax, cmap="Blues", values_format="d", colorbar=False)
    ax.set_title(f"Selected model confusion matrix — {selected}\ncomplete student-test candidates")
    fig.tight_layout()
    fig.savefig(output_dir / "confusion_matrix.png", dpi=180)
    plt.close(fig)
    (output_dir / "training_summary.md").write_text(
        "# Corrected Bayesian-optimized experiment\n\n" + comparison.to_markdown(index=False) +
        f"\n\nSelected model: **{selected}**, chosen by mean 3-fold GroupKFold validation Macro F1 after Bayesian optimization. "
        "Negative sampling was used only for training folds/final fit; validation and student-test candidates were complete. "
        "Zero-candidate observations are reported separately and count as incorrect in all-observation Top-1 accuracy.\n",
        encoding="utf-8",
    )
    summary = {
        "method": "Optuna TPE with complete-candidate GroupKFold validation",
        "model": "logistic_regression",
        "trials": trials,
        "seed": seed,
        "folds": folds,
        "candidate_radius_m": 50.0,
        "max_candidates": max_candidates,
        "training_negatives_per_observation": negatives_per_observation,
        "validation_negative_sampling": None,
        "student_negative_sampling": None,
        "best_params": tuned_params,
        "best_trial_value": float(study.best_value),
        "baseline_cv_macro_f1": float(np.mean(baseline_scores)),
        "tuned_cv_macro_f1": float(np.mean(tuned_scores)),
        "selected_model_artifact": selected,
        "optimization_seconds": elapsed,
    }
    (output_dir / "corrected_logistic_optimization.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output-dir", default="results/corrected_models", type=Path)
    parser.add_argument("--trials", default=12, type=int)
    parser.add_argument("--folds", default=3, type=int)
    parser.add_argument("--negatives-per-observation", default=1, type=int)
    parser.add_argument("--max-candidates", default=4, type=int)
    args = parser.parse_args()
    print(json.dumps(run(args.data_root, args.output_dir, args.trials, args.folds, negatives_per_observation=args.negatives_per_observation, max_candidates=args.max_candidates), indent=2))


if __name__ == "__main__":
    main()
