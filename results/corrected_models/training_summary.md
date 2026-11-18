# Corrected Bayesian-optimized experiment

| model                        |   cv_macro_f1 |   accuracy |   precision |   recall |   macro_f1 |   top1_accuracy_with_candidates |   top1_accuracy_all_observations |   candidate_miss_rate |   zero_candidate_observations |   total_observations |   candidate_rows |   log_loss |
|:-----------------------------|--------------:|-----------:|------------:|---------:|-----------:|--------------------------------:|---------------------------------:|----------------------:|------------------------------:|---------------------:|-----------------:|-----------:|
| baseline_logistic_regression |      0.729572 |   0.764837 |    0.549406 | 0.834611 |   0.74107  |                        0.763518 |                         0.763518 |              0.019833 |                             0 |                19160 |            67872 |   0.4628   |
| tuned_logistic_regression    |      0.733687 |   0.770126 |    0.55673  | 0.830351 |   0.745579 |                        0.764301 |                         0.764301 |              0.019833 |                             0 |                19160 |            67872 |   0.456162 |

Selected model: **tuned_logistic_regression**, chosen by mean 3-fold GroupKFold validation Macro F1 after Bayesian optimization. Negative sampling was used only for training folds/final fit; validation and student-test candidates were complete. Zero-candidate observations are reported separately and count as incorrect in all-observation Top-1 accuracy.
