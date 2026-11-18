# Corrected Bayesian optimization

Bayesian optimization was completed after the corrected five-model baseline. It optimizes the selected Logistic
Regression family rather than the historical HGB experiment. Optuna TPE uses seed 42 and 3-fold GroupKFold grouped by
trip ID. Each trial samples negatives only from its training fold; validation and student-test frames remain complete.

Search space:

- `C`: log-uniform from `1e-3` to `1e2`
- `class_weight`: `balanced` or `None`
- `max_iter`: 200–800 in steps of 100

The raw trial log is [corrected_logistic_optuna_trials.csv](../results/corrected_models/corrected_logistic_optuna_trials.csv).
The summary and exact best parameters are [corrected_logistic_optimization.json](../results/corrected_models/corrected_logistic_optimization.json),
and the complete comparison is [corrected_logistic_tuned_vs_baseline.csv](../results/corrected_models/corrected_logistic_tuned_vs_baseline.csv).

The corrected baseline remains the selected artifact unless the tuned model improves mean grouped validation Macro F1;
the selection decision is recorded in the JSON summary and model manifest. The earlier HGB Optuna outputs under
`results/optimization/` are preserved as historical evidence and are not mixed into this corrected comparison.

Reproduce with:

```powershell
python -m pathsnap.ml_pipeline.corrected_optimization `
  --data-root "Student folder\Student folder" `
  --output-dir results\corrected_models `
  --trials 12 `
  --folds 3 `
  --negatives-per-observation 1 `
  --max-candidates 4
```
