# Deliverable 1 — Data processing and feature engineering

This deliverable is the shared Laptop 1 contract for downstream model and API work.

## Scope completed

- Discover `train`, `student_test`, and optional `evaluator_test` trip partitions.
- Parse headerless `.track`, `.nodes`, `.arcs`, and `.route` files with schema checks.
- Validate coordinate ranges, timestamp ordering/gaps, node references, and route references.
- Generate reproducible inventory outputs in `results/eda/`.
- Build trip-local directed road geometry using a local metric projection.
- Index arc midpoints with a KD-tree and compute exact point-to-segment distances.
- Generate ranked candidate arcs with a documented 50 m default search radius and max 8 candidates.
- Extract stable candidate features for classifier training and inference.

## Raw data contract

| File | Columns | Meaning |
|---|---:|---|
| `.track` | 3 | longitude, latitude, timestamp seconds |
| `.nodes` | 2 | longitude, latitude; row index is node ID |
| `.arcs` | 2 | from-node ID, to-node ID; row index is arc ID |
| `.route` | 1 | chronological reference arc IDs; not GPS-row aligned |

All API and internal coordinate arrays use `[longitude, latitude]` order.

## Feature schema

`pathsnap.data_pipeline.features.FEATURE_NAMES` defines the stable order:

1. `distance_m`
2. `heading_difference_deg`
3. `speed_mps`
4. `time_delta_s`
5. `candidate_rank`
6. `segment_length_m`
7. `movement_distance_m`
8. `network_connected_prev` (whether the candidate continues the nearest candidate from the prior observation)

Candidate records also preserve `trip_id`, `observation_id`, `arc_id`, rank, and projection fraction.
Observations with no candidates return an empty candidate list and are not silently assigned a road segment.

## Leakage boundary

Normal inference calls `load_trip(..., include_route=False)` and never read reference routes. Reference routes are
loaded only by the training/evaluation label helper and the server-side evaluator. This prevents evaluator labels from
entering feature generation, model inference, or the Laptop 2 response.

## Verified evidence

- Supplied development data: 80 training trips and 10 student-test trips.
- All 90 supplied trips passed the loader/validation inventory with no invalid trips.
- Inventory: `results/eda/dataset_inventory.csv` and `.json`.
- Real-trip smoke tests achieved 100% candidate coverage on sampled training and student-test trips at 50 m.
- Automated suite currently passes 10 tests.

## Reproduction commands

```powershell
python -m pathsnap.data_pipeline.eda --data-root "Student folder/Student folder" --output-dir results/eda
python -m pytest -q
```

The next deliverables consume this contract; they must not reinterpret route rows as GPS-row labels or change the
feature order without versioning the model artifact manifest.
