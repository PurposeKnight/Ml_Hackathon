"""Startup-loaded inference service for one Laptop 1 process."""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from pathsnap.data_pipeline.candidates import generate_candidates
from pathsnap.data_pipeline.features import FEATURE_NAMES, candidate_feature_rows, rows_to_matrix
from pathsnap.data_pipeline.loaders import DatasetLayout, load_trip
from pathsnap.data_pipeline.road_graph import RoadGraph, unproject_xy
from pathsnap.route_decoder.hmm import log_emission_probability, log_transition_probability
from pathsnap.route_decoder.viterbi import viterbi_decode
from pathsnap.visualization.folium_maps import create_trip_map


class ModelService:
    def __init__(self, data_root: Path, model_path: Path) -> None:
        import joblib
        self.data_root = data_root
        self.model_path = model_path
        self.model = joblib.load(model_path)
        manifest_path = model_path.with_suffix(model_path.suffix + ".json")
        self.manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}

    def available_trips(self) -> list[str]:
        layout = DatasetLayout(self.data_root)
        partition = "evaluator_test" if "evaluator_test" in layout.partitions() else "student_test"
        return [files.trip_id for files in layout.discover(partition)]

    def predict(self, trip_id: str) -> dict:
        started = time.perf_counter()
        layout = DatasetLayout(self.data_root)
        partition = "evaluator_test" if "evaluator_test" in layout.partitions() else "student_test"
        files = next((item for item in layout.discover(partition) if item.trip_id == trip_id), None)
        if files is None:
            raise KeyError(trip_id)
        trip = load_trip(files, include_route=False)
        graph = RoadGraph.from_trip(trip)
        candidates = generate_candidates(trip, graph, radius_m=50.0, max_candidates=4)
        rows = candidate_feature_rows(trip, candidates, graph)
        scores = self.model.predict_proba(rows_to_matrix(rows)) if rows else np.empty((0, 2))
        positive_column = list(self.model.classes_).index(1)
        grouped_scores: list[list[float]] = []
        offset = 0
        for group in candidates:
            grouped_scores.append(scores[offset:offset + len(group), positive_column].tolist())
            offset += len(group)
        def transition(previous: int, current: int, observation_index: int) -> float:
            delta = float(trip.track[observation_index, 2] - trip.track[max(observation_index - 1, 0), 2])
            return log_transition_probability(previous, current, graph, time_delta_s=max(delta, 0.0))
        emissions = [[log_emission_probability(candidate, score) for candidate, score in zip(group, values, strict=True)] for group, values in zip(candidates, grouped_scores, strict=True)]
        decoded = viterbi_decode(candidates, emissions, transition).predicted_arc_ids
        route_coordinates: list[list[float]] = []
        for arc_id in decoded:
            if arc_id is None:
                continue
            route_coordinates.extend(graph.node_coordinates[graph.arc_nodes[arc_id]].tolist())
        gps_coordinates = trip.track[:, :2].tolist()
        return {
            "trip_id": trip_id,
            "status": "success",
            "predicted_segments": decoded,
            "predicted_route_coordinates": route_coordinates,
            "gps_coordinates": gps_coordinates,
            "metrics": {"accuracy": None, "route_continuity": None},
            "inference_time_ms": (time.perf_counter() - started) * 1000,
        }

    def folium_map_html(self, trip_id: str) -> str:
        """Render an inference-only Folium map with no reference-route data."""
        prediction = self.predict(trip_id)
        layout = DatasetLayout(self.data_root)
        partition = "evaluator_test" if "evaluator_test" in layout.partitions() else "student_test"
        files = next((item for item in layout.discover(partition) if item.trip_id == trip_id), None)
        if files is None:
            raise KeyError(trip_id)
        trip = load_trip(files, include_route=False)
        graph = RoadGraph.from_trip(trip)
        fmap = create_trip_map(trip, graph, predicted_segments=prediction["predicted_segments"])
        return fmap.get_root().render()

