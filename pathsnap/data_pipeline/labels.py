"""Training-only association of GPS observations with supplied reference routes."""

from __future__ import annotations

import numpy as np

from .candidates import Candidate, point_segment_distance
from .loaders import TripData
from .road_graph import RoadGraph, project_lon_lat


def reference_arc_per_observation(trip: TripData, graph: RoadGraph | None = None) -> np.ndarray:
    """Map each GPS point to the nearest geometry in the chronological route.

    This is deliberately a training/evaluation helper.  It does not assume a
    route row corresponds to a GPS row and is never called by inference code.
    """
    if trip.route is None:
        raise ValueError("A reference route is required to construct labels")
    graph = graph or RoadGraph.from_trip(trip)
    route_ids = np.asarray(trip.route, dtype=np.int64)
    route_segments = graph.arc_coordinates_m[route_ids]
    points = project_lon_lat(trip.track[:, :2], graph.origin_lon, graph.origin_lat)
    labels = np.empty(len(points), dtype=np.int64)
    for index, point in enumerate(points):
        distances, _ = point_segment_distance(point, route_segments[:, 0], route_segments[:, 1])
        labels[index] = route_ids[int(np.argmin(distances))]
    return labels


def label_candidates(trip: TripData, candidates: list[list[Candidate]], graph: RoadGraph | None = None) -> list[dict[str, float | int]]:
    """Add a binary candidate target while retaining reference-miss metadata."""
    graph = graph or RoadGraph.from_trip(trip)
    reference = reference_arc_per_observation(trip, graph)
    rows: list[dict[str, float | int]] = []
    for observation_id, observation_candidates in enumerate(candidates):
        reference_arc = int(reference[observation_id])
        for candidate in observation_candidates:
            rows.append({
                "observation_id": candidate.observation_id,
                "arc_id": candidate.arc_id,
                "distance_m": candidate.distance_m,
                "candidate_rank": candidate.rank,
                "reference_arc_id": reference_arc,
                "target": int(candidate.arc_id == reference_arc),
                "candidate_miss": int(not any(c.arc_id == reference_arc for c in observation_candidates)),
            })
    return rows
