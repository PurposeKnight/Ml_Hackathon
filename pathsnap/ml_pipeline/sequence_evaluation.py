"""Inference-only classifier versus HMM/Viterbi evaluation on student trips."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from pathsnap.data_pipeline.candidates import generate_candidates
from pathsnap.data_pipeline.features import FEATURE_NAMES, candidate_feature_rows
from pathsnap.data_pipeline.labels import reference_arc_per_observation
from pathsnap.data_pipeline.loaders import DatasetLayout, load_trip
from pathsnap.data_pipeline.road_graph import RoadGraph
from pathsnap.route_decoder.hmm import log_emission_probability, log_transition_probability
from pathsnap.route_decoder.viterbi import viterbi_decode


def _continuity(predicted: list[int | None], graph: RoadGraph) -> tuple[float, int, int]:
    connected = 0
    eligible = 0
    for previous, current in zip(predicted, predicted[1:]):
        if previous is None or current is None:
            continue
        eligible += 1
        if previous == current or graph.arc_nodes[previous, 1] == graph.arc_nodes[current, 0]:
            connected += 1
    return (connected / eligible if eligible else 0.0, connected, eligible)


def run(data_root: Path, model_path: Path, output_path: Path, max_candidates: int = 4) -> dict:
    model = joblib.load(model_path)
    positive_column = list(model.classes_).index(1)
    records: list[dict] = []
    inference_seconds = 0.0
    candidate_count = 0
    observation_count = 0
    zero_candidates = 0
    candidate_misses = 0
    for files in DatasetLayout(data_root).discover("student_test", require_route=True):
        trip = load_trip(files, include_route=True)
        graph = RoadGraph.from_trip(trip)
        candidates = generate_candidates(trip, graph, radius_m=50.0, max_candidates=max_candidates)
        rows = candidate_feature_rows(trip, candidates, graph)
        frame = pd.DataFrame(rows)
        started = time.perf_counter()
        probabilities = model.predict_proba(frame.loc[:, FEATURE_NAMES])[:, positive_column] if rows else np.empty(0)
        inference_seconds += time.perf_counter() - started
        candidate_count += len(rows)
        observation_count += len(candidates)
        references = reference_arc_per_observation(trip, graph)
        zero_candidates += sum(not group for group in candidates)
        candidate_misses += sum(not any(candidate.arc_id == int(reference) for candidate in group) for group, reference in zip(candidates, references, strict=True))
        grouped_scores: list[list[float]] = []
        offset = 0
        classifier_only: list[int | None] = []
        for group in candidates:
            scores = probabilities[offset:offset + len(group)].tolist()
            offset += len(group)
            grouped_scores.append(scores)
            classifier_only.append(group[int(np.argmax(scores))].arc_id if scores else None)
        def transition(previous: int, current: int, observation_index: int) -> float:
            delta = float(trip.track[observation_index, 2] - trip.track[max(observation_index - 1, 0), 2])
            return log_transition_probability(previous, current, graph, time_delta_s=max(delta, 0.0))
        emissions = [[log_emission_probability(candidate, score) for candidate, score in zip(group, scores, strict=True)] for group, scores in zip(candidates, grouped_scores, strict=True)]
        decoded = viterbi_decode(candidates, emissions, transition).predicted_arc_ids
        classifier_correct = sum(predicted is not None and int(predicted) == int(reference) for predicted, reference in zip(classifier_only, references, strict=True))
        hmm_correct = sum(predicted is not None and int(predicted) == int(reference) for predicted, reference in zip(decoded, references, strict=True))
        classifier_continuity, classifier_connected, classifier_eligible = _continuity(classifier_only, graph)
        hmm_continuity, hmm_connected, hmm_eligible = _continuity(decoded, graph)
        records.append({
            "trip_id": files.trip_id,
            "observations": len(candidates),
            "candidate_rows": len(rows),
            "classifier_top1_accuracy": classifier_correct / len(candidates) if candidates else 0.0,
            "hmm_top1_accuracy": hmm_correct / len(candidates) if candidates else 0.0,
            "classifier_route_continuity": classifier_continuity,
            "hmm_route_continuity": hmm_continuity,
            "classifier_continuity_eligible_edges": classifier_eligible,
            "hmm_continuity_eligible_edges": hmm_eligible,
            "classifier_connected_edges": classifier_connected,
            "hmm_connected_edges": hmm_connected,
        })
    frame = pd.DataFrame(records)
    aggregate = {
        "partition": "student_test",
        "trips": len(frame),
        "observations": observation_count,
        "candidate_rows": candidate_count,
        "zero_candidate_observations": zero_candidates,
        "candidate_misses": candidate_misses,
        "candidate_miss_rate": candidate_misses / observation_count if observation_count else 0.0,
        "classifier_top1_accuracy": float(frame["classifier_top1_accuracy"].mul(frame["observations"]).sum() / observation_count),
        "hmm_top1_accuracy": float(frame["hmm_top1_accuracy"].mul(frame["observations"]).sum() / observation_count),
        "classifier_route_continuity": float(frame["classifier_connected_edges"].sum() / frame["classifier_continuity_eligible_edges"].sum()),
        "hmm_route_continuity": float(frame["hmm_connected_edges"].sum() / frame["hmm_continuity_eligible_edges"].sum()),
        "classifier_continuity_eligible_edges": int(frame["classifier_continuity_eligible_edges"].sum()),
        "hmm_continuity_eligible_edges": int(frame["hmm_continuity_eligible_edges"].sum()),
        "inference_ms_per_candidate": inference_seconds * 1000.0 / max(candidate_count, 1),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path.with_name("sequence_comparison_by_trip.csv"), index=False)
    output_path.write_text(json.dumps(aggregate, indent=2), encoding="utf-8")
    return aggregate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--model", default="results/corrected_models/selected_model.joblib", type=Path)
    parser.add_argument("--output", default="results/corrected_models/sequence_comparison.json", type=Path)
    parser.add_argument("--max-candidates", default=4, type=int)
    args = parser.parse_args()
    print(json.dumps(run(args.data_root, args.model, args.output, args.max_candidates), indent=2))


if __name__ == "__main__":
    main()
