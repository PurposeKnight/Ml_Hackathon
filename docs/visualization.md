# Folium visualization evidence

`pathsnap.visualization.folium_maps.create_trip_map` generates layered Folium maps with:

- Blue GPS observations and trajectory.
- Optional gray road-network geometry clipped to the GPS extent.
- Red predicted route geometry.
- Optional green reference route for permitted development/reporting use only.
- Layer controls and a documented legend through layer names.

Representative output: `results/maps/trip_00000000.html`, generated from the student-test partition using the exported
tuned model. Evaluator reference data is never passed to this map in the inference workflow.
