# Heuristic label review

Training labels are created by assigning each GPS point to the closest geometry among the supplied route arcs. This is
appropriate for candidate supervision because `.route` is an arc sequence and is not GPS-row aligned, but it is a
proxy—not independently verified ground truth.

The audit records nearest-route distance, second-best distance margin, candidate misses, repeated route arcs, and far
points. Interpretations:

- Small nearest-vs-second distance margins indicate parallel/overlapping or ambiguous road geometry.
- Large nearest distances indicate GPS noise, route limitations, or a route that does not explain the observation.
- Candidate misses indicate the 50 m candidate radius or candidate cap cannot represent the heuristic label.
- Route-row counts may differ from GPS counts and repeated arc IDs are allowed.

Run:

```powershell
python -m pathsnap.data_pipeline.label_audit --data-root "Student folder/Student folder"
```

The generated [label_quality.csv](../results/corrected_models/label_quality.csv) is an audit of limitations, not a claim that the
heuristic labels are perfect physical ground truth.
