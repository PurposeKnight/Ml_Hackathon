"""Strict readers for the headerless PathSnap trip files.

IDs are positional: a node ID is its row in ``.nodes`` and an arc ID is its
row in ``.arcs``.  A ``.route`` is a chronological arc sequence and is not
assumed to align one-to-one with GPS observations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


PARTITIONS = ("train", "student_test", "evaluator_test")


class DataFormatError(ValueError):
    """Raised when a raw PathSnap file violates its documented schema."""


@dataclass(frozen=True)
class TripFiles:
    trip_id: str
    partition: str
    directory: Path
    track: Path
    nodes: Path
    arcs: Path
    route: Path | None


@dataclass(frozen=True)
class TripData:
    files: TripFiles
    track: np.ndarray
    nodes: np.ndarray
    arcs: np.ndarray
    route: np.ndarray | None


class DatasetLayout:
    """Discover partitions and trips without reading reference labels."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()
        if not self.root.is_dir():
            raise FileNotFoundError(f"Dataset root does not exist: {self.root}")

    def partitions(self) -> list[str]:
        return [name for name in PARTITIONS if (self.root / name).is_dir()]

    def discover(self, partition: str, require_route: bool = False) -> list[TripFiles]:
        if partition not in PARTITIONS:
            raise ValueError(f"Unknown partition {partition!r}; expected one of {PARTITIONS}")
        folder = self.root / partition
        if not folder.is_dir():
            return []
        trips: list[TripFiles] = []
        for directory in sorted((p for p in folder.iterdir() if p.is_dir()), key=lambda p: p.name):
            trip_id = directory.name
            required = {suffix: directory / f"{trip_id}.{suffix}" for suffix in ("track", "nodes", "arcs")}
            missing = [str(path) for path in required.values() if not path.is_file()]
            if missing:
                raise FileNotFoundError(f"Trip {trip_id} is missing required files: {missing}")
            route = directory / f"{trip_id}.route"
            if require_route and not route.is_file():
                raise FileNotFoundError(f"Trip {trip_id} is missing reference route: {route}")
            trips.append(TripFiles(trip_id, partition, directory, required["track"], required["nodes"], required["arcs"], route if route.is_file() else None))
        return trips


def _read_table(path: Path, columns: int, dtype: type[np.floating] | type[np.integer]) -> np.ndarray:
    rows: list[list[str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            values = raw.split()
            if not values:
                continue
            if len(values) != columns:
                raise DataFormatError(f"{path}:{line_number}: expected {columns} columns, found {len(values)}")
            rows.append(values)
    if not rows:
        raise DataFormatError(f"{path}: file contains no records")
    try:
        return np.asarray(rows, dtype=dtype)
    except ValueError as exc:
        raise DataFormatError(f"{path}: contains a value with the wrong type") from exc


def load_trip(files: TripFiles, include_route: bool = False) -> TripData:
    """Load one trip; reference routes require an explicit opt-in."""
    track = _read_table(files.track, 3, np.float64)
    nodes = _read_table(files.nodes, 2, np.float64)
    arcs = _read_table(files.arcs, 2, np.int64)
    route = None
    if include_route:
        if files.route is None:
            raise FileNotFoundError(f"No route is available for trip {files.trip_id}")
        route = _read_table(files.route, 1, np.int64).reshape(-1)
    return TripData(files, track, nodes, arcs, route)


def iter_loaded(trips: Iterable[TripFiles], include_route: bool = False) -> Iterable[TripData]:
    for trip in trips:
        yield load_trip(trip, include_route=include_route)
