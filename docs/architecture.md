# PathSnap Laptop 1 architecture

## Mandatory requirements checklist

- Preserve the official 80 train / 10 student-test / 10 evaluator-test trip split and group CV by trip.
- Inspect raw data, quality, timestamps, geography, graph connectivity, and retain genuine EDA evidence.
- Generate plausible segment candidates and justified metric-distance/movement/connectivity features.
- Train and compare at least five distinct model families using identical permitted data and recorded seeds/configurations.
- Report classification, observation Top-1, candidate miss, log-loss, continuity, sequence, and timing metrics where applicable.
- Bayesian-optimize the selected model using group-aware CV; retain every trial and compare tuned/untuned models.
- Decode candidate sequences with an explained log-space HMM/Viterbi implementation and test edge cases.
- Compare classifier-only with classifier-plus-HMM results on permitted development data.
- Export the model and all preprocessing/configuration artifacts; never fabricate evidence.
- Provide FastAPI inference, safe server-side evaluation, restricted CORS, startup loading, logs, and ten-trip UI support.
- Keep evaluator reference data exclusively inside the evaluation component; never return it to Laptop 2.
- Generate required Folium layers/maps and maintain unit/integration tests and reproducible commands.
- Submit source, artifacts/configuration within size limits, evidence, public GitHub repository, and one verifiable report.

## Module contracts and implementation order

1. `data_pipeline`: discover/parse strict schemas; prediction loading defaults to no route; validate and inventory.
2. `road_graph`: construct directed NetworkX graph, segment geometry, connectivity, and spatial index.
3. `candidates`: return observation/candidate rows with stable trip, observation, and arc IDs; report misses separately.
4. `features`: metric geometric, heading, speed, time, rank, and connectivity features in a versioned schema.
5. `ml_pipeline`: build grouped folds, five sklearn models, calibrated candidate scores, metrics, logs, and artifacts.
6. `optimization`: persist Optuna study/trials and refit only after initial model comparison.
7. `route_decoder`: combine model emissions and network transitions in log space, then reconstruct segment geometry.
8. `backend`: startup service owns inference artifacts; evaluation service alone may read reference routes.
9. `visualization`: Folium maps accept reference data only when explicitly requested for permitted reporting.
10. `tests` and `results`: synthetic unit fixtures plus genuine, traceable experiment outputs.

Planned folders are `pathsnap/data_pipeline`, `pathsnap/ml_pipeline`, `pathsnap/route_decoder`,
`pathsnap/backend`, `pathsnap/visualization`, `configs`, `results`, `reports`, `docs`, and `tests`.

## Coordinate and API contract

All API coordinates use GeoJSON order `[longitude, latitude]`.

- `GET /health`: liveness only.
- `GET /api/status`: artifact/configuration readiness and model version; no private paths or labels.
- `GET /api/trips`: evaluator-safe trip IDs available for selection.
- `POST /api/predict` body: `{ "trip_id": "00000000" }`.
- Successful prediction: trip ID, status, per-observation predicted segment IDs (nullable under the documented
  no-candidate policy), predicted route coordinates, GPS coordinates, server-computed aggregate metrics, and timing.
- Never return route labels, reference coordinates, candidate labels, filesystem paths, or reference-bearing map HTML.

The API is bound to the configured LAN interface and uses only the configured `FRONTEND_ORIGIN` for CORS.

## First implementation task

Implement and test strict trip discovery, loaders with explicit reference-label access, validation, and reproducible
inventory outputs. This establishes the real schemas and leakage boundary before candidate-label design.
