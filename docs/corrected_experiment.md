# Corrected five-model evaluation

This is the reproducible corrected baseline for PathSnap's first evaluation. The previous files under
`results/models/` are preserved for comparison; they are not overwritten.

## Methodology verified

- 80 training trips and 10 student-test trips; evaluator-test data was not read.
- Candidate generation is unchanged: 50 m radius and at most four candidates per GPS observation.
- The eight features and their order are recorded in `results/corrected_models/experiment_config.json`.
- Three-fold `GroupKFold` uses trip ID as the group, so a trip cannot occur in both sides of a fold.
- Negative sampling is applied only to each fold's training partition and to the final training fit. Validation and student-test use every generated candidate.
- `random_state=42` is used wherever the existing model definitions support it.
- Zero-candidate observations are counted separately and count as incorrect for the all-observation Top-1 metric. In this run: 0 of 19,160 student observations.

## Corrected results

The complete table is [model_comparison.csv](../results/corrected_models/model_comparison.csv). Values below are copied from that file (not rounded for selection):

| Model | CV Macro F1 | Student Macro F1 | Student Top-1 (all observations) | Log loss | Inference ms/candidate |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 0.729572 | 0.741070 | 0.763518 | 0.462800 | 0.001152 |
| HistGradientBoosting | 0.450623 | 0.472487 | 0.233925 | 3.565329 | 0.004352 |
| MLP | 0.450534 | 0.468910 | 0.234812 | 3.720350 | 0.000956 |
| KNN | 0.448107 | 0.464052 | 0.430271 | 15.542463 | 0.136254 |
| Random Forest | 0.446602 | 0.466644 | 0.325992 | 4.971794 | 0.003802 |

The baseline comparison selects Logistic Regression because it has the highest corrected GroupKFold Macro F1 (0.7295715568). The subsequent corrected Bayesian optimization improved that CV score to 0.7336865386 with `C=0.0010660012`, `class_weight=None`, and `max_iter=700`. The tuned artifact is now the selected model; its student Macro F1 is 0.745579 and complete-candidate Top-1 is 0.764301. The optimization comparison is [corrected_logistic_tuned_vs_baseline.csv](../results/corrected_models/corrected_logistic_tuned_vs_baseline.csv).

## Why the numbers changed

The old comparison evaluated a negatively sampled student set. The corrected comparison evaluates all 67,872 student candidate rows, so the class prior and ranking problem are different. The old and corrected files therefore must not be compared as if they used the same evaluation population. The corrected student Top-1 values are:

| Model | Old Top-1 | Corrected Top-1 |
|---|---:|---:|
| Logistic Regression | 0.817902 | 0.763518 |
| KNN | 0.818111 | 0.430271 |
| Random Forest | 0.836952 | 0.325992 |
| HistGradientBoosting | 0.849269 | 0.233925 |
| MLP | 0.851200 | 0.234812 |

## Label limitations

The route label is a heuristic: each GPS point is assigned to the nearest supplied route arc. The route file is an arc sequence, not GPS-row-aligned ground truth. Parallel/overlapping roads can be ambiguous, GPS noise or incomplete routes can produce large nearest-route distances, and repeated route arcs are allowed. The audit in [label_quality.csv](../results/corrected_models/label_quality.csv) records these cases. On the student set, the median-of-trip median nearest-route distance is 4.59 m, the median trip 95th-percentile distance is 15.77 m, 32.0% of observations have a nearest-vs-second distance margin of at most 2 m, and 0.14% are more than 50 m from the nearest route arc. These are quality indicators, not verified physical ground truth.

## Commands and artifacts

Run the corrected experiment (training) with:

```powershell
python -m pathsnap.ml_pipeline.corrected_experiment --data-root "Student folder\Student folder" --output-dir results\corrected_models --folds 3 --negatives-per-observation 1 --max-candidates 4
```

The generated deliverables are `model_comparison.csv`, `cross_validation_results.csv`, `experiment_config.json`,
`model_comparison.png`, `top1_accuracy_comparison.png`, `confusion_matrix.png`, `training_summary.md`,
`selected_model.joblib`, and `selected_model.joblib.json` under `results/corrected_models/`.

The selected artifact is versioned separately and was loaded successfully for inference; the existing
`pathsnap/ml_pipeline/artifacts/final_model.joblib` was not overwritten.
