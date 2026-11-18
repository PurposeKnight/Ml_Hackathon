"""Nearby road-segment candidate generation with exact point-to-segment distance."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .loaders import TripData
from .road_graph import RoadGraph, project_lon_lat


@dataclass(frozen=True)
class Candidate:
    observation_id: int
    arc_id: int
    distance_m: float
    rank: int
    projection_fraction: float


def point_segment_distance(point: np.ndarray, starts: np.ndarray, ends: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    vectors = ends - starts
    denominator = np.einsum("ij,ij->i", vectors, vectors)
    numerator = np.einsum("ij,ij->i", point[None, :] - starts, vectors)
    fractions = np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator > 0)
    fractions = np.clip(fractions, 0.0, 1.0)
    projections = starts + fractions[:, None] * vectors
    return np.linalg.norm(projections - point[None, :], axis=1), fractions


def generate_candidates(
    trip: TripData,
    graph: RoadGraph | None = None,
    radius_m: float = 50.0,
    max_candidates: int = 8,
) -> list[list[Candidate]]:
    """Return candidates per GPS observation, ordered by metric distance.

    The midpoint index is a fast prefilter.  The exact point-to-segment distance
    is used for ranking, and the radius is applied to that exact distance.
    Observations with no nearby segment return an empty list.
    """
    if radius_m <= 0 or max_candidates <= 0:
        raise ValueError("radius_m and max_candidates must be positive")
    graph = graph or RoadGraph.from_trip(trip)
    points = project_lon_lat(trip.track[:, :2], graph.origin_lon, graph.origin_lat)
    output: list[list[Candidate]] = []
    prefilter_radius = radius_m + float(np.max(graph.arc_lengths_m, initial=0.0)) / 2.0
    for observation_id, point in enumerate(points):
        nearby = graph.midpoint_tree.query_ball_point(point, prefilter_radius)
        if not nearby:
            output.append([])
            continue
        indices = np.asarray(nearby, dtype=np.int64)
        distances, fractions = point_segment_distance(point, graph.arc_coordinates_m[indices, 0], graph.arc_coordinates_m[indices, 1])
        keep = np.flatnonzero(distances <= radius_m)
        order = keep[np.argsort(distances[keep])][:max_candidates]
        output.append([Candidate(observation_id, int(indices[i]), float(distances[i]), rank, float(fractions[i])) for rank, i in enumerate(order)])
    return output
