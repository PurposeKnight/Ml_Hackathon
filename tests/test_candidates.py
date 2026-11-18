from pathlib import Path

import numpy as np

from pathsnap.data_pipeline.candidates import generate_candidates, point_segment_distance
from pathsnap.data_pipeline.features import FEATURE_NAMES, candidate_feature_rows, rows_to_matrix
from pathsnap.data_pipeline.loaders import DatasetLayout, load_trip
from pathsnap.data_pipeline.road_graph import RoadGraph


def test_point_segment_distance_and_projection() -> None:
    distance, fractions = point_segment_distance(np.array([5.0, 2.0]), np.array([[0.0, 0.0]]), np.array([[10.0, 0.0]]))
    np.testing.assert_allclose(distance, [2.0])
    np.testing.assert_allclose(fractions, [0.5])


def test_candidates_have_stable_ids_and_features() -> None:
    root = Path(__file__).parents[1] / "Student folder" / "Student folder"
    files = DatasetLayout(root).discover("train")[0]
    trip = load_trip(files)
    graph = RoadGraph.from_trip(trip)
    candidates = generate_candidates(trip, graph, radius_m=100.0, max_candidates=3)
    rows = candidate_feature_rows(trip, candidates, graph)
    assert all(row["observation_id"] >= 0 and row["arc_id"] >= 0 for row in rows)
    assert set(FEATURE_NAMES).issubset(rows[0]) if rows else True
    matrix = rows_to_matrix(rows)
    assert matrix.shape[1] == len(FEATURE_NAMES) if rows else matrix.shape == (0,)


def test_connectivity_summary_on_synthetic_trip(tmp_path: Path) -> None:
    folder = tmp_path / "train" / "00000001"
    folder.mkdir(parents=True)
    (folder / "00000001.track").write_text("12 52 1\n12.001 52 2\n", encoding="utf-8")
    (folder / "00000001.nodes").write_text("12 52\n12.001 52\n13 53\n", encoding="utf-8")
    (folder / "00000001.arcs").write_text("0 1\n", encoding="utf-8")
    trip = load_trip(DatasetLayout(tmp_path).discover("train")[0])
    summary = RoadGraph.from_trip(trip).connectivity_summary()
    assert summary["arcs"] == 1
    assert summary["isolated_nodes"] == 1
    assert summary["weak_components"] == 2
