# PathSnap

PathSnap is a trip-local GPS-to-road candidate ranking and route reconstruction system. The repository contains the
data pipeline, eight-feature extraction, five-model experiments, corrected evaluation, HMM/Viterbi decoder, FastAPI
service, Folium visualisations, tests, and auditable result artifacts.

## Environment

Python 3.11+ is required. The supplied development dataset is intentionally not committed; place it at
`Student folder/Student folder` or set `PATHSNAP_DATA_ROOT` to its location.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Verify the repository

```powershell
python -m pytest -q
```

The current suite covers loaders, candidate generation, feature schema, labels/models, corrected sampling, decoder,
and API contracts.

## Reproduce data processing

```powershell
python -m pathsnap.data_pipeline.eda --data-root "Student folder\Student folder" --output-dir results\eda
python -m pathsnap.data_pipeline.label_audit --data-root "Student folder\Student folder" --output results\corrected_models\label_quality.csv
```

## Corrected five-model baseline

The corrected experiment samples negatives only in training partitions. Validation and student-test evaluate every
candidate generated with a 50 m radius and four-candidate cap.

```powershell
python -m pathsnap.ml_pipeline.corrected_experiment `
  --data-root "Student folder\Student folder" `
  --output-dir results\corrected_models `
  --folds 3 `
  --negatives-per-observation 1 `
  --max-candidates 4
```

The verified selected artifact is `results/corrected_models/selected_model.joblib`; its feature manifest is beside it.
The prior artifacts under `pathsnap/ml_pipeline/artifacts/` and prior result CSVs remain available for comparison.

Corrected Bayesian optimization for the selected Logistic Regression model is reproducible with:

```powershell
python -m pathsnap.ml_pipeline.corrected_optimization `
  --data-root "Student folder\Student folder" `
  --output-dir results\corrected_models `
  --trials 12 `
  --folds 3 `
  --negatives-per-observation 1 `
  --max-candidates 4
```

Its trial log and tuned-vs-baseline comparison are saved beside the corrected model results.

To reproduce the development-only classifier versus HMM/Viterbi sequence comparison without training:

```powershell
python -m pathsnap.ml_pipeline.sequence_evaluation `
  --data-root "Student folder\Student folder" `
  --model results\corrected_models\selected_model.joblib `
  --output results\corrected_models\sequence_comparison.json `
  --max-candidates 4
```

## API

Use the corrected artifact explicitly when starting the service:

```powershell
$env:MODEL_PATH = "results/corrected_models/selected_model.joblib"
$env:PATHSNAP_DATA_ROOT = "Student folder\Student folder"
uvicorn pathsnap.backend.main:app --host 0.0.0.0 --port 8000
```

Endpoints are `/health`, `/api/status`, `/api/trips`, and `POST /api/predict` with `{ "trip_id": "..." }`.
Reference routes are not loaded by normal inference.

## Visualisations and report

The interactive Folium map is `results/plots/gps_matched_route_map.html`; static plots are in `results/plots/` and
`results/corrected_models/`. The reproducible technical report source and PDF are in `reports/`.

See [docs/corrected_experiment.md](docs/corrected_experiment.md) for the corrected methodology, model selection,
old-vs-corrected comparison, and heuristic-label limitations.
