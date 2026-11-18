# Bayesian optimization evidence

The historical initial model was HistGradientBoosting based on the original sampled-student five-model comparison. Optuna TPE searched
the following space using only training trips and three `GroupKFold` splits:

- `learning_rate`: log-uniform `[0.02, 0.2]`
- `max_iter`: integer `[80, 250]`
- `max_leaf_nodes`: integer `[8, 63]`
- `l2_regularization`: log-uniform `[1e-5, 10]`

Eight trials were executed with seed 42. The objective was mean validation macro F1. The best result was:

```text
CV macro F1: 0.7872393790512655
learning_rate: 0.0798261175712336
max_iter: 201
max_leaf_nodes: 9
l2_regularization: 6.598711072054068
```

The untuned HistGradientBoosting baseline had CV macro F1 `0.7863208265506461`, so the observed tuning improvement is
`0.0009185524506194` on the same grouped-CV objective. Student-test refitting and comparison must use the same
candidate configuration as the baseline; evaluator data is not used.

Raw evidence: [optuna_trials.csv](../results/optimization/optuna_trials.csv) and
[best_params.json](../results/optimization/best_params.json).

The final refit comparison on the student-test partition was:

| Model | Top-1 accuracy | Macro F1 | Log loss |
|---|---:|---:|---:|
| Untuned HGB | 0.849269 | 0.820325 | 0.385197 |
| Tuned HGB | **0.850104** | **0.821476** | **0.384484** |

The exported historical tuned artifact is [final_model.joblib](../pathsnap/ml_pipeline/artifacts/final_model.joblib), with its
feature and parameter manifest beside it. The corrected baseline deliberately selects Logistic Regression by complete-candidate
GroupKFold Macro F1 and does not rerun Bayesian optimization. Machine-readable comparison is
[tuned_vs_untuned_student.csv](../results/optimization/tuned_vs_untuned_student.csv).
