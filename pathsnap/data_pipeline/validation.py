"""Schema and data-quality checks for loaded trips."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .loaders import TripData


@dataclass
class ValidationReport:
    trip_id: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors


def validate_trip(trip: TripData) -> ValidationReport:
    report = ValidationReport(trip.files.trip_id)
    lon, lat, timestamps = trip.track.T
    node_lon, node_lat = trip.nodes.T
    if not np.isfinite(trip.track).all() or not np.isfinite(trip.nodes).all():
        report.errors.append("GPS or node coordinates contain non-finite values")
    if np.any((lon < -180) | (lon > 180)) or np.any((node_lon < -180) | (node_lon > 180)):
        report.errors.append("Longitude outside [-180, 180]")
    if np.any((lat < -90) | (lat > 90)) or np.any((node_lat < -90) | (node_lat > 90)):
        report.errors.append("Latitude outside [-90, 90]")
    deltas = np.diff(timestamps)
    if np.any(deltas < 0):
        report.errors.append("Timestamps are not monotonically non-decreasing")
    if np.any(deltas == 0):
        report.warnings.append("Duplicate timestamps detected")
    if np.any(deltas > 30):
        report.warnings.append("Timestamp gap greater than 30 seconds detected")
    if np.any(trip.arcs < 0) or np.any(trip.arcs >= len(trip.nodes)):
        report.errors.append("Arc references a node outside the node table")
    if trip.route is not None and (np.any(trip.route < 0) or np.any(trip.route >= len(trip.arcs))):
        report.errors.append("Route references an arc outside the arc table")
    return report
