# Folium visualization evidence

`pathsnap.visualization.folium_maps.create_trip_map` generates layered Folium maps with:

- Blue GPS observations and trajectory.
- Optional gray road-network geometry clipped to the GPS extent.
- Red predicted route geometry.
- Optional green reference route for permitted development/reporting use only.
- Layer controls and a documented legend through layer names.

Representative outputs are `results/maps/trip_00000000.html` and
`results/plots/gps_matched_route_map.html`. The former is the historical student-test demonstration; the latter is
the first-evaluation visualisation pack. Evaluator reference data is never passed to the normal inference workflow.
