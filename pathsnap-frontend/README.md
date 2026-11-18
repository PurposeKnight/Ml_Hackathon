# PathSnap — Laptop 2: Evaluator Frontend & Visualization Client

> **Course:** UE24CS352A — Machine Learning  
> **Institution:** Department of Computer Science and Engineering, PES University, RR Campus  
> **Project:** PathSnap: Distributed Map-Matching & Route Reconstruction  
> **Role:** Laptop 2 (Evaluator-Facing User Interface & Geographical Route Visualization)

---

## 1. Project Overview

**PathSnap** is a distributed machine learning system that reconstructs realistic vehicle trajectories by matching noisy, urban GPS observations to a road network.

The system is deployed across **two physical laptops**:
- **Laptop 1 (Backend & Machine Learning):** Hosts raw data preprocessing, candidate road segment extraction, trained ML classifiers, Hidden Markov Model (HMM) emission/transition scoring, Viterbi decoding, FastAPI web services, and server-side evaluation against ground truth.
- **Laptop 2 (Evaluator User Interface):** Hosts the web-based evaluator interface, fetches the ten official evaluation trips, transmits prediction requests to Laptop 1, and renders the reconstructed routes on interactive Leaflet/Folium geographical maps alongside server-computed evaluation metrics.

---

## 2. Laptop 2 Responsibilities & Boundaries

In accordance with the **Academic Integrity & Plagiarism Policy**:
- **No Ground-Truth Leakage:** Laptop 2 does **not** store, read, or process `.route` ground-truth reference files.
- **No Client-Side ML:** Laptop 2 does not train models or execute HMM/Viterbi inference. All computational inference runs on Laptop 1.
- **No Hardcoded Predictions:** Every route coordinate and metric displayed is received dynamically from Laptop 1 via HTTP API calls.
- **Dynamic 10-Trip Support:** The interface dynamically populates and evaluates all ten official evaluation trips (`00000000`, `00000007`, `00000009`, `00000040`, `00000052`, `00000056`, `00000065`, `00000076`, `00000077`, `00000091`).

---

## 3. Technology Stack

- **UI Framework:** React 18, TypeScript, Tailwind CSS, Lucide React
- **Build Tool:** Vite 5
- **Geospatial Mapping:** Leaflet 1.9 (native interactive mapping) with embedded Folium HTML view support
- **HTTP Client:** Fetch API with dynamic timeout, retry, and AbortController cancellation
- **Testing:** Vitest & React Testing Library

---

## 4. Installation & Setup Instructions

### Prerequisites
- Node.js LTS (v18.0.0 or higher; v22.x recommended)
- npm (v9.0.0 or higher)
- Web browser (Chrome, Firefox, Edge)

### 1. Install Dependencies
```bash
cd pathsnap-frontend
npm install
```

### 2. Configure Laptop 1 API Endpoint
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` to point to Laptop 1's actual IP address:
```env
# Replace with Laptop 1's reachable IPv4 address
VITE_API_BASE_URL=http://192.168.1.10:8000
```
*(Note: You can also update the backend IP dynamically at runtime directly inside the UI without rebuilding!)*

### 3. Start Development Server
```bash
npm run dev
```
The interface will be accessible at:
```text
http://localhost:5173
```

### 4. Run Automated Frontend Tests
```bash
npm run test
```

---

## 5. Two-Laptop Network Setup

```text
               LOCAL WI-FI / ETHERNET ROUTER OR MOBILE HOTSPOT
                               (192.168.1.0/24)
                             /                  \
                            /                    \
              [192.168.1.10]                      [192.168.1.25]
                 LAPTOP 1                            LAPTOP 2
          FastAPI Server (:8000)               Vite Frontend (:5173)
```

### Step 1: Find Laptop 1 IP Address
- **Windows (Laptop 1):** Open Command Prompt and run `ipconfig`. Locate the **IPv4 Address** under your active Wi-Fi or Ethernet adapter (e.g., `192.168.1.10`).
- **Linux/macOS (Laptop 1):** Run `ip addr` or `ifconfig`.

### Step 2: Start Laptop 1 Backend
On Laptop 1, launch FastAPI binding to `0.0.0.0`:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
*(Or use the included reference backend: `python mock_server/mock_laptop1_backend.py`)*

### Step 3: Test Connection from Laptop 2
In Laptop 2's terminal or PowerShell:
```powershell
curl -I http://192.168.1.10:8000/health
```
If you receive `HTTP/1.1 200 OK`, the connection is successful.

### Step 4: Open Laptop 2 Evaluator Dashboard
Open `http://localhost:5173` on Laptop 2. The status indicator should turn **Green (Connected)**.

---

## 6. Shared API Contract

### Health Check: `GET /health`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model_loaded": true,
  "hmm_ready": true,
  "timestamp": 1700000000
}
```

### Evaluation Trips: `GET /api/trips`
```json
{
  "trips": [
    { "trip_id": "00000000", "num_points": 582 },
    { "trip_id": "00000007", "num_points": 412 },
    { "trip_id": "00000009", "num_points": 630 },
    { "trip_id": "00000040", "num_points": 510 },
    { "trip_id": "00000052", "num_points": 490 },
    { "trip_id": "00000056", "num_points": 380 },
    { "trip_id": "00000065", "num_points": 540 },
    { "trip_id": "00000076", "num_points": 475 },
    { "trip_id": "00000077", "num_points": 512 },
    { "trip_id": "00000091", "num_points": 460 }
  ]
}
```

### Run Prediction: `POST /api/predict`
**Request:**
```json
{
  "trip_id": "00000000"
}
```
**Response:**
```json
{
  "trip_id": "00000000",
  "status": "success",
  "predicted_segments": [17630, 17633, 211, 17638, 17645],
  "predicted_route_coordinates": [
    [54.9635, 56.2515],
    [54.9631, 56.2515]
  ],
  "gps_coordinates": [
    [54.963519, 56.251559, 1.0],
    [54.963143, 56.251523, 2.0]
  ],
  "metrics": {
    "accuracy": 0.912,
    "route_continuity": 0.948,
    "num_gps_points": 582,
    "num_predicted_segments": 48,
    "classifier_only_accuracy": 0.824,
    "hmm_accuracy": 0.912
  },
  "inference_time_ms": 142.5,
  "folium_html": null
}
```

---

## 7. Final Demonstration Step-by-Step Workflow

1. **Step 1:** Start the FastAPI server on **Laptop 1** (`--host 0.0.0.0 --port 8000`).
2. **Step 2:** Start the React frontend on **Laptop 2** (`npm run dev`).
3. **Step 3:** Open `http://localhost:5173` on Laptop 2 in Chrome/Firefox.
4. **Step 4:** Observe the **Backend Status** indicator:
   - Status badge turns green with measured round-trip latency.
   - Model and HMM readiness flags are displayed.
5. **Step 5:** The **Evaluation Trip** dropdown dynamically populates with the 10 official test trips from Laptop 1.
6. **Step 6:** Select a trip (e.g. `00000000`).
7. **Step 7:** Click **Run Prediction & Reconstruction**.
8. **Step 8:** The UI transitions into loading state with an active timer; point the evaluator to the **Laptop 1 terminal** to observe live incoming HTTP request logs and inference progress.
9. **Step 9:** Laptop 2 receives the reconstructed trajectory coordinates and evaluation metrics:
   - **Interactive Leaflet Map:** Displays blue GPS observation points, the reconstructed red road-matched route, and start/destination pins.
   - **Layer Controls:** Toggle GPS points, route polyline, and roads independently.
   - **Metrics Card:** Displays server-computed accuracy %, route continuity %, inference latency (ms), and segment counts.
10. **Step 10:** Select another trip (e.g. `00000007`) and repeat the process to prove the system works dynamically for all evaluation trips.

---

## 8. Common Troubleshooting & Solutions

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| **Backend Status: Disconnected** | Laptop 1 IP is incorrect or backend is not running | Click **Configure IP** in the UI, enter the correct `http://<LAPTOP_1_IP>:8000`, and click **Apply**. Verify Laptop 1 is running `uvicorn --host 0.0.0.0`. |
| **Connection Timed Out** | Windows Firewall blocking port 8000 on Laptop 1 | On Laptop 1, run `netsh advfirewall firewall add rule name="FastAPI 8000" dir=in action=allow protocol=TCP localport=8000` or allow Python in Windows Firewall. |
| **CORS Policy Error** | Laptop 1 does not allow Laptop 2's origin | Ensure `CORSMiddleware` in Laptop 1's FastAPI allows origins `["*"]` or `["http://localhost:5173", "http://<LAPTOP2_IP>:5173"]`. |
| **Leaflet Map Not Centered** | Missing coordinates | The map features auto-bounds fitting; click the **Maximize/Fit Bounds** button in the map toolbar. |

