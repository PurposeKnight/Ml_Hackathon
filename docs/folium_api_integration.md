# Folium API integration

Laptop 1 now exposes an inference-only Folium map endpoint:

```text
GET http://<laptop-1-ip>:8000/api/trips/{trip_id}/map
```

For example:

```text
http://192.168.1.20:8000/api/trips/00000000/map
```

The endpoint loads the selected trip without its reference route, runs the existing model/HMM-Viterbi inference, and
passes the GPS trajectory, road network, and predicted segments to the existing
`pathsnap.visualization.folium_maps.create_trip_map` generator. It returns rendered `text/html` suitable for an iframe.
No reference route or ground-truth labels are loaded or included.

Laptop 2 can display it with:

```jsx
<iframe
  title="Folium route map"
  src={`${API_BASE_URL}/api/trips/${tripId}/map`}
  style={{ width: "100%", height: 600, border: 0 }}
/>
```

The existing `/health`, `/api/status`, `/api/trips`, and `/api/predict` endpoints remain unchanged. No model training or
ML artifacts are modified by map generation.
