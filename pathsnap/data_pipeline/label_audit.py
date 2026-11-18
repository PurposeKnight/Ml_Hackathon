"""Audit heuristic GPS-to-reference-route labels without changing them."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from .candidates import generate_candidates, point_segment_distance
from .loaders import DatasetLayout, load_trip
from .road_graph import RoadGraph, project_lon_lat


def audit_trip(trip, ambiguity_margin_m: float = 2.0, far_distance_m: float = 50.0) -> dict[str, float | int | str]:
    if trip.route is None:
        raise ValueError("label audit requires a reference route")
    graph = RoadGraph.from_trip(trip)
    route_ids = np.asarray(trip.route, dtype=np.int64)
    route_segments = graph.arc_coordinates_m[route_ids]
    points = project_lon_lat(trip.track[:, :2], graph.origin_lon, graph.origin_lat)
    nearest, second = [], []
    for point in points:
        distances, _ = point_segment_distance(point, route_segments[:, 0], route_segments[:, 1])
        ordered = np.sort(distances)
        nearest.append(float(ordered[0]))
        second.append(float(ordered[1]) if len(ordered) > 1 else float(ordered[0]))
    nearest = np.asarray(nearest)
    margins = np.asarray(second) - nearest
    candidates = generate_candidates(trip, graph, radius_m=50.0, max_candidates=8)
    labels = []
    for point_index, point in enumerate(points):
        distances, _ = point_segment_distance(point, route_segments[:, 0], route_segments[:, 1])
        labels.append(int(route_ids[int(np.argmin(distances))]))
    misses = sum(not any(candidate.arc_id == label for candidate in group) for label, group in zip(labels, candidates, strict=True))
    return {
        "trip_id": trip.files.trip_id,
        "gps_observations": len(points),
        "route_rows": len(route_ids),
        "unique_route_arcs": len(np.unique(route_ids)),
        "median_nearest_distance_m": float(np.median(nearest)),
        "p95_nearest_distance_m": float(np.percentile(nearest, 95)),
        "max_nearest_distance_m": float(np.max(nearest)),
        "ambiguous_margin_le_2m": int(np.count_nonzero(margins <= ambiguity_margin_m)),
        "far_nearest_gt_50m": int(np.count_nonzero(nearest > far_distance_m)),
        "candidate_misses_at_50m": int(misses),
        "candidate_miss_rate": float(misses / len(points)) if len(points) else 0.0,
    }


def audit_dataset(root: Path) -> list[dict[str, float | int | str]]:
    records = []
    layout = DatasetLayout(root)
    for partition in ("train", "student_test"):
        for files in layout.discover(partition, require_route=True):
            records.append({"partition": partition, **audit_trip(load_trip(files, include_route=True))})
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output", default="results/labels/label_quality.csv", type=Path)
    args = parser.parse_args()
    records = audit_dataset(args.data_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    print(f"audited {len(records)} trips -> {args.output}")


if __name__ == "__main__":
    main()
