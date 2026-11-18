# Final submission checklist

## Repository evidence

- [x] Data loading, validation, preprocessing, and inventory source in `pathsnap/data_pipeline/`.
- [x] Eight-feature schema and candidate generation source in `pathsnap/data_pipeline/`.
- [x] Five model factories and corrected training/evaluation source in `pathsnap/ml_pipeline/`.
- [x] Corrected training-only negative sampling regression tests.
- [x] Corrected complete-candidate validation/student metrics.
- [x] Corrected Logistic Regression Bayesian optimization and raw Optuna trials.
- [x] HMM/Viterbi source and decoder tests.
- [x] FastAPI endpoints and startup model loading in `pathsnap/backend/`.
- [x] Folium and static visualization source/results.
- [x] Versioned tuned model and feature manifest.
- [x] CSV metrics, configurations, plots, label audit, and report.
- [x] Laptop 2 UI/API demonstration screenshot.

## Verification

```powershell
python -m pytest -q
```

Expected current result: `13 passed`.

Start Laptop 1 API with the corrected tuned artifact:

```powershell
$env:PATHSNAP_DATA_ROOT = "Student folder\Student folder"
$env:MODEL_PATH = "results\corrected_models\selected_model.joblib"
$env:API_HOST = "0.0.0.0"
$env:API_PORT = "8000"
$env:FRONTEND_ORIGIN = "http://<laptop-2-ip>:3000"
python -m uvicorn pathsnap.backend.main:app --host 0.0.0.0 --port 8000
```

From Laptop 2, verify `GET http://<laptop-1-ip>:8000/health`, then open the UI and run a trip prediction. The UI
must use Laptop 1's LAN address, not `localhost`.

## Known evaluation limitation

Evaluator ground-truth labels are intentionally not returned by Laptop 1, so evaluator accuracy and continuity appear
as N/A in the Laptop 2 interface. This is the documented zero-ground-truth-leakage policy, not a failed prediction.
