"""Robust log-space Viterbi decoding over variable-size candidate sets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np

from pathsnap.data_pipeline.candidates import Candidate


TransitionFunction = Callable[[int, int, int], float]


@dataclass(frozen=True)
class ViterbiResult:
    predicted_arc_ids: list[int | None]
    log_probability: float
    backpointer_count: int


def viterbi_decode(
    candidate_groups: Sequence[Sequence[Candidate]],
    emission_log_probs: Sequence[Sequence[float]],
    transition_log_probability: TransitionFunction,
) -> ViterbiResult:
    """Decode one state per observation; empty groups produce a null output.

    The transition callback receives ``(previous_arc_id, current_arc_id,
    observation_index)``.  Missing observations reset the dynamic program,
    which avoids inventing a road segment where no candidate exists.
    """
    if len(candidate_groups) != len(emission_log_probs):
        raise ValueError("candidate and emission sequences must have equal length")
    decoded: list[int | None] = [None] * len(candidate_groups)
    total_log_probability = 0.0
    backpointer_count = 0
    previous_candidates: Sequence[Candidate] = []
    previous_scores = np.empty(0, dtype=float)
    previous_path: list[list[int]] = []
    for observation_index, (candidates, emissions) in enumerate(zip(candidate_groups, emission_log_probs, strict=True)):
        if len(candidates) != len(emissions):
            raise ValueError(f"observation {observation_index}: candidates and emissions differ in length")
        if not candidates:
            if previous_candidates:
                best_index = int(np.argmax(previous_scores))
                start = observation_index - len(previous_path[best_index])
                for offset, candidate_index in enumerate(previous_path[best_index]):
                    decoded[start + offset] = int(candidate_groups[start + offset][candidate_index].arc_id)
            previous_candidates = []
            previous_scores = np.empty(0, dtype=float)
            previous_path = []
            continue
        emission = np.asarray(emissions, dtype=float)
        if not np.isfinite(emission).all():
            raise ValueError(f"observation {observation_index}: emissions must be finite")
        if not previous_candidates:
            previous_scores = emission.copy()
            previous_path = [[i] for i in range(len(candidates))]
        else:
            scores = np.full(len(candidates), -np.inf, dtype=float)
            paths: list[list[int]] = []
            for current_index, current in enumerate(candidates):
                transitions = np.asarray([
                    previous_scores[previous_index] + transition_log_probability(previous.arc_id, current.arc_id, observation_index)
                    for previous_index, previous in enumerate(previous_candidates)
                ])
                best_previous = int(np.argmax(transitions))
                scores[current_index] = emission[current_index] + transitions[best_previous]
                paths.append(previous_path[best_previous] + [current_index])
                backpointer_count += 1
            previous_scores, previous_path = scores, paths
        previous_candidates = candidates
        best_index = int(np.argmax(previous_scores))
        total_log_probability = float(previous_scores[best_index])
        # Current best is sufficient for online use; final reconstruction below
        # uses the stored index path from the final contiguous segment.
    if previous_candidates:
        best_index = int(np.argmax(previous_scores))
        start = len(candidate_groups) - len(previous_path[best_index])
        for offset, candidate_index in enumerate(previous_path[best_index]):
            decoded[start + offset] = int(candidate_groups[start + offset][candidate_index].arc_id)
    return ViterbiResult(decoded, total_log_probability, backpointer_count)
