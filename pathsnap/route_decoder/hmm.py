"""Emission and transition probabilities for candidate road segments."""

from __future__ import annotations

import math

import numpy as np

from pathsnap.data_pipeline.candidates import Candidate
from pathsnap.data_pipeline.road_graph import RoadGraph


def log_emission_probability(candidate: Candidate, classifier_probability: float, distance_scale_m: float = 25.0) -> float:
    """Combine classifier confidence with a distance likelihood in log space."""
    if distance_scale_m <= 0:
        raise ValueError("distance_scale_m must be positive")
    probability = float(np.clip(classifier_probability, 1e-9, 1.0))
    return math.log(probability) - float(candidate.distance_m) / distance_scale_m


def log_transition_probability(
    previous_arc: int,
    current_arc: int,
    graph: RoadGraph,
    displacement_m: float = 0.0,
    time_delta_s: float = 1.0,
    disconnected_penalty: float = 8.0,
) -> float:
    """Score directed continuity, allowing noisy/disconnected observations.

    Consecutive arcs are strongly preferred when the previous arc's destination
    equals the current arc's source.  Staying on one segment is also valid.  A
    finite fallback keeps Viterbi paths defined across GPS gaps and components.
    """
    if disconnected_penalty <= 0 or time_delta_s < 0:
        raise ValueError("invalid transition parameters")
    if previous_arc == current_arc:
        return -0.05
    previous_end = int(graph.arc_nodes[previous_arc, 1])
    current_start = int(graph.arc_nodes[current_arc, 0])
    if previous_end == current_start:
        expected = max(float(graph.arc_lengths_m[previous_arc]), 1.0)
        movement_error = abs(float(displacement_m) - expected) / max(expected, float(displacement_m), 1.0)
        return -0.25 - min(movement_error, 4.0) - 0.01 * min(time_delta_s, 100.0)
    gap_relaxation = min(max(float(time_delta_s) / 30.0, 0.0), 1.0)
    return -disconnected_penalty * (1.0 - 0.5 * gap_relaxation)
