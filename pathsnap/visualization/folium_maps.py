"""Folium maps for permitted development/reporting visualizations."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import folium

from pathsnap.data_pipeline.loaders import TripData
from pathsnap.data_pipeline.road_graph import RoadGraph


def create_trip_map(
    trip: TripData,
    graph: RoadGraph,
    predicted_segments: Iterable[int | None] | None = None,
    reference_segments: Iterable[int] | None = None,
    output_path: str | Path | None = None,
    max_network_arcs: int = 5000,
) -> folium.Map:
    """Create a layered map; reference layers are opt-in for development only."""
    center = [float(trip.track[:, 1].mean()), float(trip.track[:, 0].mean())]
    fmap = folium.Map(location=center, zoom_start=13, control_scale=True)
    gps_layer = folium.FeatureGroup(name="GPS observations", show=True)
    folium.PolyLine(trip.track[:, [1, 0]].tolist(), color="#1f77b4", weight=3, opacity=0.8).add_to(gps_layer)
    for longitude, latitude, _ in trip.track[:: max(1, len(trip.track) // 100)]:
        folium.CircleMarker([latitude, longitude], radius=2, color="#1f77b4").add_to(gps_layer)
    gps_layer.add_to(fmap)
    network_layer = folium.FeatureGroup(name="Road network", show=False)
    # Limit display geometry to a deterministic subset around the GPS extent.
    min_lon, max_lon = trip.track[:, 0].min(), trip.track[:, 0].max()
    min_lat, max_lat = trip.track[:, 1].min(), trip.track[:, 1].max()
    visible = []
    for arc_id, (source, target) in enumerate(graph.arc_nodes):
        endpoints = graph.node_coordinates[[source, target]]
        if (endpoints[:, 0].max() >= min_lon and endpoints[:, 0].min() <= max_lon and endpoints[:, 1].max() >= min_lat and endpoints[:, 1].min() <= max_lat):
            visible.append(arc_id)
        if len(visible) >= max_network_arcs:
            break
    for arc_id in visible:
        source, target = graph.arc_nodes[arc_id]
        folium.PolyLine(graph.node_coordinates[[source, target]][:, [1, 0]].tolist(), color="#999999", weight=1, opacity=0.45).add_to(network_layer)
    network_layer.add_to(fmap)
    if predicted_segments is not None:
        predicted_layer = folium.FeatureGroup(name="Predicted route", show=True)
        for arc_id in dict.fromkeys(item for item in predicted_segments if item is not None):
            source, target = graph.arc_nodes[arc_id]
            folium.PolyLine(graph.node_coordinates[[source, target]][:, [1, 0]].tolist(), color="#d62728", weight=4, opacity=0.9).add_to(predicted_layer)
        predicted_layer.add_to(fmap)
    if reference_segments is not None:
        reference_layer = folium.FeatureGroup(name="Reference route (development only)", show=False)
        for arc_id in dict.fromkeys(reference_segments):
            source, target = graph.arc_nodes[arc_id]
            folium.PolyLine(graph.node_coordinates[[source, target]][:, [1, 0]].tolist(), color="#2ca02c", weight=4, opacity=0.8).add_to(reference_layer)
        reference_layer.add_to(fmap)
    folium.LayerControl(collapsed=False).add_to(fmap)
    if output_path is not None:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        fmap.save(str(destination))
    return fmap
