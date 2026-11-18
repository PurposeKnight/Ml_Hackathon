# PathSnap — Laptop 2 Technical Report Contributions

> **Section:** 7. API, UI and Deployment & Section 6. Geographical Visualisation  
> **Course:** UE24CS352A — Machine Learning  
> **Team Deliverable Reference:** Deliverables.pdf (Mandatory Report Components)

---

## 1. System Deployment Architecture & Separation of Concerns

PathSnap implements a strictly decoupled client-server architecture partitioned across two physical machines to prevent evaluator ground-truth leakage and maintain clean architectural separation:

```text
+---------------------------------------------------------------------------------+
|                                    LAPTOP 1                                     |
|                       (Machine Learning & API Server)                           |
|                                                                                 |
|   +-----------------------+     +-------------------+     +-----------------+   |
|   | Raw GPS Preprocessing | --> | Feature Extractor | --> | ML Classifier   |   |
|   +-----------------------+     +-------------------+     | (Emission Prob) |   |
|                                                           +-----------------+   |
|                                                                    |            |
|   +-----------------------+     +-------------------+              v            |
|   | Server Evaluation     | <-- | Viterbi Sequential| <-----------+             |
|   | (vs Ground Truth)     |     | Route Reconstruction                          |
|   +-----------------------+     +-------------------+                           |
|               |                                                                 |
|               v                                                                 |
|   +-------------------------------------------------------------------------+   |
|   |                     FastAPI HTTP Web Service (:8000)                    |   |
|   +-------------------------------------------------------------------------+   |
+----------------------------------------^----------------------------------------+
                                         |  HTTP / JSON Requests
                                         |  (/health, /api/trips, /api/predict)
                                         v
+---------------------------------------------------------------------------------+
|                                    LAPTOP 2                                     |
|                         (Evaluator User Interface Client)                       |
|                                                                                 |
|   +-------------------------------------------------------------------------+   |
|   |                       React 18 + Vite 5 Application                     |   |
|   +-------------------------------------------------------------------------+   |
|         |                                 |                        |            |
|         v                                 v                        v            |
|   +-----------------+           +-------------------+    +------------------+   |
|   | Backend Status  |           | Dynamic Trip      |    | Run Prediction   |   |
|   | & Health Monitor|           | Selector (10 trips|    | Controller       |   |
|   +-----------------+           +-------------------+    +------------------+   |
|                                                                    |            |
|         +----------------------------------------------------------+            |
|         |                                                                       |
|         v                                                          v            |
|   +---------------------------------------+              +------------------+   |
|   | High-Performance Leaflet Map          |              | Server Metrics   |   |
|   | - Blue: GPS Observations (with time)  |              | - Accuracy %     |   |
|   | - Red: HMM-Decoded Reconstructed Route|              | - Continuity %   |   |
|   | - Embedded Folium HTML View           |              | - Latency (ms)   |   |
|   +---------------------------------------+              +------------------+   |
+---------------------------------------------------------------------------------+
```

### Verification Against Academic Integrity Requirements
1. **Zero Ground-Truth Contamination:** Laptop 2 contains no code that parses `.route` files or reads reference road sequences. Accuracy is evaluated on Laptop 1.
2. **Zero Hardcoded Paths:** Every displayed trajectory is retrieved over the network dynamically from the API response payload.
3. **Full 10 Evaluation Trips Supported:** The trip selector dynamically queries `/api/trips` and loads any of the ten evaluation trips (`00000000`, `00000007`, `00000009`, `00000040`, `00000052`, `00000056`, `00000065`, `00000076`, `00000077`, `00000091`).

---

## 2. API Communication Protocol & Endpoint Contracts

All communications between Laptop 2 and Laptop 1 are stateless HTTP/JSON transactions:

| Endpoint | Method | Input Payload | Output Payload | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `/health` | `GET` | None | `{ status, version, model_loaded, hmm_ready }` | Connection status verification & readiness probe |
| `/api/trips` | `GET` | None | `{ trips: [{ trip_id, num_points }] }` | Dynamic retrieval of reserved evaluation trips |
| `/api/predict`| `POST`| `{ trip_id: "00000000" }` | `{ predicted_segments, predicted_route_coordinates, gps_coordinates, metrics, inference_time_ms }` | Triggers preprocessing, ML inference, Viterbi decoding & server-side evaluation |

### Coordinate Representation Standard
- **Leaflet & Frontend Layers:** Standard `[latitude, longitude]` decimal tuples (e.g., `[54.9635, 56.2515]`).
- **GeoJSON Compatibility:** Automatic normalization functions parse array formats and coordinate dictionaries into verified latitude-longitude bounds.

---

## 3. Geographical Visualization Architecture

The mapping system satisfies all requirements of **Section 6 (Geographical Visualisation Using Folium / Interactive Maps)**:
- **GPS Layer:** Blue circle markers (`#3b82f6`) with sequence index and timestamp tooltips.
- **Decoded Route Layer:** High-contrast red/rose polyline (`#e11d48`) representing the continuous sequence of road segments output by the Viterbi algorithm.
- **Origin & Destination:** Distinct green (`S`) and red (`E`) circular icon pins indicating trajectory endpoints.
- **Layer Controls:** Interactive checkboxes allow independent toggling of GPS observations, decoded route, and road networks.
- **Folium Map Support:** An integrated view switcher allows viewing either the client-side Leaflet visualization or the server-generated Folium HTML map within a sandboxed `iframe`.

---

## 4. Automated Testing & Verification Summary

The frontend suite contains unit and integration tests executing on Vitest:
- **`tests/coordinates.test.ts`:** Verifies coordinate sanitization, NaN/null filtering, bounding box calculation, and Haversine geodesic distance computation.
- **`tests/api.test.ts`:** Verifies request payload generation, API response parsing, and error-handling behavior for unreachable endpoints or missing trips.
- **Test Results:** 2 test suites, 9 unit tests passing with zero failures.
- **Production Build:** `vite build` completed successfully producing optimized, tree-shaken static assets (`dist/`).

