from pathlib import Path

import numpy as np
import pytest

from pathsnap.data_pipeline.loaders import DataFormatError, DatasetLayout, load_trip
from pathsnap.data_pipeline.validation import validate_trip


def make_trip(root: Path, track: str = "12.0 52.0 1\n12.1 52.1 2\n") -> None:
    folder = root / "train" / "00000001"
    folder.mkdir(parents=True)
    (folder / "00000001.track").write_text(track, encoding="utf-8")
    (folder / "00000001.nodes").write_text("12.0 52.0\n12.1 52.1\n", encoding="utf-8")
    (folder / "00000001.arcs").write_text("0 1\n", encoding="utf-8")
    (folder / "00000001.route").write_text("0\n", encoding="utf-8")


def test_discovery_loading_and_explicit_route_access(tmp_path: Path) -> None:
    make_trip(tmp_path)
    files = DatasetLayout(tmp_path).discover("train", require_route=True)[0]
    inference_trip = load_trip(files)
    assert inference_trip.route is None
    labelled_trip = load_trip(files, include_route=True)
    np.testing.assert_array_equal(labelled_trip.arcs, [[0, 1]])
    np.testing.assert_array_equal(labelled_trip.route, [0])
    assert validate_trip(labelled_trip).valid


def test_rejects_wrong_column_count(tmp_path: Path) -> None:
    make_trip(tmp_path, track="12.0 52.0\n")
    files = DatasetLayout(tmp_path).discover("train")[0]
    with pytest.raises(DataFormatError, match="expected 3 columns"):
        load_trip(files)


def test_invalid_coordinates_and_arc_are_reported(tmp_path: Path) -> None:
    make_trip(tmp_path, track="12.0 95.0 2\n12.0 52.0 1\n")
    arc = tmp_path / "train" / "00000001" / "00000001.arcs"
    arc.write_text("0 4\n", encoding="utf-8")
    report = validate_trip(load_trip(DatasetLayout(tmp_path).discover("train")[0]))
    assert not report.valid
    assert any("Latitude" in issue for issue in report.errors)
    assert any("monotonically" in issue for issue in report.errors)
    assert any("outside the node table" in issue for issue in report.errors)
