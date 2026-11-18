"""Candidate-level movement and geometric features."""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np

from .candidates import Candidate
from .loaders import TripData
from .road_graph import RoadGraph, project_lon_lat


FEATURE_NAMES = (
    "distance_m",
    "heading_difference_deg",
    "speed_mps",
    "time_delta_s",
    "candidate_rank",
    "segment_length_m",
    "movement_distance_m",
)


def _angle_difference(left: float, right: float) -> float:
    return abs((left - right + 180.0) % 360.0 - 180.0)


def candidate_feature_rows(trip: TripData, candidates: list[list[Candidate]], graph: RoadGraph | None = None) -> list[dict[str, float | int]]:
    graph = graph or RoadGraph.from_trip(trip)
    projected = project_lon_lat(trip.track[:, :2], graph.origin_lon, graph.origin_lat)
    timestamps = trip.track[:, 2]
    rows: list[dict[str, float | int]] = []
    for obs_id, observation_candidates in enumerate(candidates):
        if obs_id == 0:
            movement_distance = 0.0
            speed = 0.0
            time_delta = 0.0
            movement_heading = None
        else:
            displacement = projected[obs_id] - projected[obs_id - 1]
            movement_distance = float(np.linalg.norm(displacement))
            time_delta = max(float(timestamps[obs_id] - timestamps[obs_id - 1]), 0.0)
            speed = movement_distance / time_delta if time_delta > 0 else 0.0
            movement_heading = (math.degrees(math.atan2(displacement[0], displacement[1])) + 360.0) % 360.0
        for candidate in observation_candidates:
            heading_difference = 0.0 if movement_heading is None else _angle_difference(float(graph.arc_headings_deg[candidate.arc_id]), movement_heading)
            rows.append({
                "observation_id": obs_id,
                "arc_id": candidate.arc_id,
                "distance_m": candidate.distance_m,
                "heading_difference_deg": heading_difference,
                "speed_mps": speed,
                "time_delta_s": time_delta,
                "candidate_rank": candidate.rank,
                "segment_length_m": float(graph.arc_lengths_m[candidate.arc_id]),
                "movement_distance_m": movement_distance,
            })
    return rows


def rows_to_matrix(rows: Iterable[dict[str, float | int]]) -> np.ndarray:
    return np.asarray([[float(row[name]) for name in FEATURE_NAMES] for row in rows], dtype=np.float64)
