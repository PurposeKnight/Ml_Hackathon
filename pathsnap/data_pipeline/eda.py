"""Reproducible raw-dataset inventory and quality summary."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from .loaders import DatasetLayout, load_trip
from .road_graph import RoadGraph
from .validation import validate_trip


def inventory(dataset_root: str | Path) -> list[dict[str, Any]]:
    layout = DatasetLayout(dataset_root)
    records: list[dict[str, Any]] = []
    for partition in layout.partitions():
        for files in layout.discover(partition):
            trip = load_trip(files, include_route=files.route is not None)
            report = validate_trip(trip)
            graph = RoadGraph.from_trip(trip)
            deltas = np.diff(trip.track[:, 2])
            records.append({
                "partition": partition,
                "trip_id": files.trip_id,
                "gps_observations": len(trip.track),
                "nodes": len(trip.nodes),
                "arcs": len(trip.arcs),
                "route_arcs": len(trip.route) if trip.route is not None else 0,
                "track_bytes": files.track.stat().st_size,
                "nodes_bytes": files.nodes.stat().st_size,
                "arcs_bytes": files.arcs.stat().st_size,
                "route_bytes": files.route.stat().st_size if files.route is not None else 0,
                "gps_min_lon": float(np.min(trip.track[:, 0])),
                "gps_max_lon": float(np.max(trip.track[:, 0])),
                "gps_min_lat": float(np.min(trip.track[:, 1])),
                "gps_max_lat": float(np.max(trip.track[:, 1])),
                **{f"network_{key}": value for key, value in graph.connectivity_summary().items()},
                "missing_values": int(np.isnan(trip.track).sum() + np.isnan(trip.nodes).sum()),
                "median_interval_s": float(np.median(deltas)) if len(deltas) else None,
                "max_interval_s": float(np.max(deltas)) if len(deltas) else None,
                "valid": report.valid,
                "errors": " | ".join(report.errors),
                "warnings": " | ".join(report.warnings),
            })
    return records


def write_inventory(records: list[dict[str, Any]], output_dir: str | Path) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    fields = list(records[0]) if records else []
    with (target / "dataset_inventory.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    summary = {
        "partition_trip_counts": {p: sum(r["partition"] == p for r in records) for p in sorted({r["partition"] for r in records})},
        "total_trips": len(records),
        "invalid_trips": [r["trip_id"] for r in records if not r["valid"]],
        "records": records,
    }
    (target / "dataset_inventory.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--output-dir", default="results/eda")
    args = parser.parse_args()
    records = inventory(args.data_root)
    write_inventory(records, args.output_dir)
    print(json.dumps({"trips": len(records), "invalid": sum(not r["valid"] for r in records)}, indent=2))


if __name__ == "__main__":
    main()
