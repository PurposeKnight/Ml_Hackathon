"""The five baseline candidate-ranking models required by PathSnap."""

from __future__ import annotations

from typing import Any

def model_factories(seed: int = 42) -> dict[str, Any]:
    """Return reproducible models with probability outputs for HMM emissions."""
    try:
        from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.neighbors import KNeighborsClassifier
        from sklearn.neural_network import MLPClassifier
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:
        raise RuntimeError(
            "scikit-learn native extensions are unavailable in this Python environment; "
            "use a supported Python/scikit-learn installation to run model training"
        ) from exc
    return {
        "logistic_regression": Pipeline([
            ("scale", StandardScaler()),
            ("model", LogisticRegression(max_iter=400, class_weight="balanced", random_state=seed)),
        ]),
        "knn": Pipeline([
            ("scale", StandardScaler()),
            ("model", KNeighborsClassifier(n_neighbors=7, weights="distance", n_jobs=-1)),
        ]),
        "random_forest": RandomForestClassifier(
            n_estimators=40, min_samples_leaf=2, n_jobs=-1, class_weight="balanced_subsample", random_state=seed
        ),
        "hist_gradient_boosting": HistGradientBoostingClassifier(
            max_iter=150, learning_rate=0.08, max_leaf_nodes=31, random_state=seed
        ),
        "mlp": Pipeline([
            ("scale", StandardScaler()),
            ("model", MLPClassifier(hidden_layer_sizes=(32, 16), early_stopping=True, max_iter=60, random_state=seed)),
        ]),
    }
