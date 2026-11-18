"""Optuna Bayesian optimization with trip-grouped cross-validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


def optimize_hist_gradient_boosting(values, targets, groups, output_dir: str | Path, n_trials: int = 25, seed: int = 42) -> dict[str, Any]:
    """Optimize HGB parameters; returns a persisted, auditable study summary."""
    try:
        import optuna
        from sklearn.ensemble import HistGradientBoostingClassifier
        from sklearn.metrics import f1_score
        from sklearn.model_selection import GroupKFold
    except ImportError as exc:
        raise RuntimeError("Optuna and a working scikit-learn installation are required for Bayesian optimization") from exc
    values = np.asarray(values, dtype=float)
    targets = np.asarray(targets, dtype=int)
    groups = np.asarray(groups)
    splitter = GroupKFold(n_splits=5)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed))

    def objective(trial):
        model = HistGradientBoostingClassifier(
            learning_rate=trial.suggest_float("learning_rate", 0.02, 0.2, log=True),
            max_iter=trial.suggest_int("max_iter", 80, 250),
            max_leaf_nodes=trial.suggest_int("max_leaf_nodes", 8, 63),
            l2_regularization=trial.suggest_float("l2_regularization", 1e-5, 10.0, log=True),
            random_state=seed,
        )
        scores = []
        for train_index, validation_index in splitter.split(values, targets, groups):
            model.fit(values[train_index], targets[train_index])
            scores.append(f1_score(targets[validation_index], model.predict(values[validation_index]), average="macro", zero_division=0))
        return float(np.mean(scores))

    study.optimize(objective, n_trials=n_trials)
    study.trials_dataframe().to_csv(output / "optuna_trials.csv", index=False)
    summary = {"best_value": study.best_value, "best_params": study.best_params, "n_trials": len(study.trials), "seed": seed}
    import json
    (output / "best_params.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
