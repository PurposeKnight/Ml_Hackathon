"""Directed road-network geometry and spatial indexing for one trip."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import networkx as nx
from scipy.spatial import cKDTree

from .loaders import TripData


EARTH_RADIUS_M = 6_371_008.8


@dataclass(frozen=True)
class RoadGraph:
    """A trip-local graph with metric coordinates and an arc midpoint index."""

    node_coordinates: np.ndarray  # [node, lon, lat]
    arc_nodes: np.ndarray  # [arc, from_node, to_node]
    arc_coordinates_m: np.ndarray  # [arc, endpoint, x/y]
    arc_lengths_m: np.ndarray
    arc_headings_deg: np.ndarray
    midpoint_tree: cKDTree
    origin_lon: float
    origin_lat: float

    @classmethod
    def from_trip(cls, trip: TripData) -> "RoadGraph":
        lon0 = float(np.mean(trip.nodes[:, 0]))
        lat0 = float(np.mean(trip.nodes[:, 1]))
        xy = project_lon_lat(trip.nodes, lon0, lat0)
        arc_nodes = np.asarray(trip.arcs, dtype=np.int64)
        endpoints = xy[arc_nodes]
        delta = endpoints[:, 1] - endpoints[:, 0]
        lengths = np.linalg.norm(delta, axis=1)
        headings = (np.degrees(np.arctan2(delta[:, 0], delta[:, 1])) + 360.0) % 360.0
        midpoints = endpoints.mean(axis=1)
        return cls(trip.nodes.copy(), arc_nodes, endpoints, lengths, headings, cKDTree(midpoints), lon0, lat0)

    def connectivity_summary(self) -> dict[str, int]:
        """Return directed/weak connectivity facts for EDA and diagnostics."""
        graph = nx.DiGraph()
        graph.add_nodes_from(range(len(self.node_coordinates)))
        graph.add_edges_from((int(source), int(target)) for source, target in self.arc_nodes)
        weak_components = list(nx.weakly_connected_components(graph))
        return {
            "nodes": graph.number_of_nodes(),
            # Preserve the raw segment count even when duplicate node pairs
            # collapse in the simple NetworkX connectivity projection.
            "arcs": int(len(self.arc_nodes)),
            "unique_directed_edges": graph.number_of_edges(),
            "isolated_nodes": sum(1 for node in graph if graph.degree(node) == 0),
            "weak_components": len(weak_components),
            "largest_weak_component_nodes": max((len(component) for component in weak_components), default=0),
        }


def project_lon_lat(coordinates: np.ndarray, origin_lon: float, origin_lat: float) -> np.ndarray:
    """Approximate local metric projection, suitable for a trip-sized extent."""
    values = np.asarray(coordinates, dtype=float)
    scale_x = np.cos(np.radians(origin_lat)) * EARTH_RADIUS_M * np.pi / 180.0
    scale_y = EARTH_RADIUS_M * np.pi / 180.0
    return np.column_stack(((values[:, 0] - origin_lon) * scale_x, (values[:, 1] - origin_lat) * scale_y))


def unproject_xy(xy: np.ndarray, origin_lon: float, origin_lat: float) -> np.ndarray:
    values = np.asarray(xy, dtype=float)
    scale_x = np.cos(np.radians(origin_lat)) * EARTH_RADIUS_M * np.pi / 180.0
    scale_y = EARTH_RADIUS_M * np.pi / 180.0
    return np.column_stack((values[:, 0] / scale_x + origin_lon, values[:, 1] / scale_y + origin_lat))
