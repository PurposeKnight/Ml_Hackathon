from pathlib import Path

import numpy as np
import pytest

from pathsnap.data_pipeline.candidates import generate_candidates
from pathsnap.data_pipeline.labels import label_candidates, reference_arc_per_observation
from pathsnap.data_pipeline.loaders import DatasetLayout, load_trip
from pathsnap.data_pipeline.road_graph import RoadGraph
from pathsnap.ml_pipeline.models import model_factories


def test_reference_labels_do_not_assume_route_row_count() -> None:
    root = Path(__file__).parents[1] / "Student folder" / "Student folder"
    files = DatasetLayout(root).discover("train", require_route=True)[0]
    trip = load_trip(files, include_route=True)
    graph = RoadGraph.from_trip(trip)
    labels = reference_arc_per_observation(trip, graph)
    assert len(labels) == len(trip.track)
    assert set(labels).issubset(set(trip.route.tolist()))


def test_label_candidates_and_model_catalog() -> None:
    root = Path(__file__).parents[1] / "Student folder" / "Student folder"
    files = DatasetLayout(root).discover("train", require_route=True)[0]
    trip = load_trip(files, include_route=True)
    graph = RoadGraph.from_trip(trip)
    candidates = generate_candidates(trip, graph, radius_m=50, max_candidates=4)
    rows = label_candidates(trip, candidates, graph)
    assert rows
    assert {row["target"] for row in rows}.issubset({0, 1})
    try:
        factories = model_factories()
    except RuntimeError as exc:
        pytest.skip(str(exc))
    assert len(factories) == 5
