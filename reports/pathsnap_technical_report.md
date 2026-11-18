# PathSnap technical report

## 1. System overview

PathSnap maps GPS observations to directed road-segment candidates, scores candidates with five supervised models,
and optionally reconstructs a continuous route with a log-space HMM/Viterbi decoder. The repository separates data
loading, graph construction, candidates, features, model experiments, decoding, API inference, and visualisation.

## 2. Dataset processing and feature engineering

The loader validates headerless `.track`, `.nodes`, `.arcs`, and `.route` files, checks coordinates, timestamps,
node/arc references, and keeps the official 80 training / 10 student-test split. Route rows are reference arcs and are
not assumed to be GPS-row aligned. A local metric projection supports exact point-to-segment distances. Candidate
generation uses a 50 m radius and four-candidate cap for the corrected experiment.

The stable feature order is: distance, heading difference, speed, time delta, candidate rank, segment length,
movement distance, and previous-network connectivity. Missing candidates remain empty groups rather than being assigned
an invented segment.

## 3. Corrected model evaluation

Three-fold GroupKFold groups by trip ID. Negative sampling is used only on each training fold and final training fit;
validation and student-test candidate tables are complete. The student set contains 19,160 observations and 67,872
candidate rows. No student observation had zero candidates in this run. The full corrected table is in
`results/corrected_models/model_comparison.csv`.

The selected model is Logistic Regression because it has the highest corrected CV Macro F1 (0.7295715568). It also
has the strongest student Macro F1 and Top-1 accuracy in the complete-candidate evaluation. The prior sampled-student
results under `results/models/` are preserved but are not directly comparable because their evaluation population was
different.

## 4. Model-specific interpretation

Logistic Regression provides a calibrated linear baseline and was fastest among the practical models. KNN is a local
similarity baseline but its inference cost and log loss are high. Random Forest captures nonlinear interactions but
did not generalise as well on the complete candidate set. HistGradientBoosting and MLP achieved high recall but poor
candidate-level calibration and lower Top-1 ranking after negative sampling was removed from evaluation.

## 5. Bayesian optimisation

The repository contains the earlier eight-trial Optuna HGB study and its raw evidence under `results/optimization/`.
That study is retained for reproducibility. It was run before the corrected complete-candidate baseline and is not used
to override the corrected model selection. No new Bayesian search was performed during the correction.

## 6. HMM/Viterbi route reconstruction

Hidden states are candidate arc IDs. Emissions combine classifier positive probability with a distance likelihood in
log space. Transitions reward staying on an arc or moving to a directed-connected arc and apply a finite penalty to
disconnected transitions. Empty candidate groups emit null predictions and reset the dynamic program, so missing GPS
matches do not create invented roads. Unit tests cover variable candidate groups and disconnected observations.

## 7. Geographical evidence

The Folium map layers GPS observations, road network, and predicted route with layer controls. The interactive map is
`results/plots/gps_matched_route_map.html`; static trajectory, speed, distance, model-comparison, and confusion-matrix
plots are committed in `results/plots/` and `results/corrected_models/`.

## 8. Limitations and reproducibility

Reference labels are a nearest-route-arc heuristic, not independently surveyed ground truth. Small nearest-vs-second
distance margins are ambiguous on parallel roads; large distances can reflect GPS noise or incomplete route geometry;
repeated arcs are allowed. The audit is in `results/corrected_models/label_quality.csv`. All reported metrics are read
from committed CSV evidence, and the selected model plus feature schema are load-tested before deployment.
