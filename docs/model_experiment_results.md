# Five-model experiment evidence (historical and corrected)

The original sampled-student run from `pathsnap.ml_pipeline.train_models` is retained below for historical comparison.
It must not be used as the corrected evaluation because its student candidate table was sampled differently.

The authoritative current result is [corrected_experiment.md](corrected_experiment.md) and
[results/corrected_models/model_comparison.csv](../results/corrected_models/model_comparison.csv). The corrected run
uses complete validation/student candidate sets, training-only negative sampling, three trip-grouped folds, a 50 m
radius, and four candidates per observation.

| Model | CV macro F1 | Student Top-1 | Student macro F1 | Log loss | Inference ms/candidate |
|---|---:|---:|---:|---:|---:|
| Logistic regression | 0.772715 | 0.817902 | 0.790613 | 0.470397 | 0.002449 |
| KNN | 0.765142 | 0.818111 | 0.795202 | 1.251689 | 0.232972 |
| Random forest | 0.779739 | 0.836952 | 0.811094 | 0.414801 | 0.010312 |
| HistGradientBoosting | **0.786321** | 0.849269 | 0.820325 | **0.385197** | 0.006072 |
| MLP | 0.784011 | **0.851200** | 0.812784 | 0.389745 | **0.001317** |

Candidate miss rate was `0.019833` for this candidate configuration. HistGradientBoosting is the initial tuning
candidate because it led grouped CV macro F1, student macro F1, and log loss; MLP led student Top-1 and inference
speed, so both trade-offs remain documented. Bayesian tuning must use training-trip grouped CV only and must compare
the tuned model against this exact baseline configuration.

The raw machine-readable evidence is [model_comparison.csv](../results/models/model_comparison.csv), with the exact
run settings in [experiment_config.json](../results/models/experiment_config.json).
