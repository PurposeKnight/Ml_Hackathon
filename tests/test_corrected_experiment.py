import pandas as pd

from pathsnap.ml_pipeline.corrected_experiment import sample_training_rows


def test_negative_sampling_keeps_all_positives_and_is_training_only() -> None:
    frame = pd.DataFrame({
        "trip_id": ["a"] * 4,
        "observation_id": [0] * 4,
        "target": [1, 0, 0, 0],
    })
    sampled = sample_training_rows(frame, negatives_per_observation=1)
    assert sampled["target"].tolist() == [1, 0]
    assert len(sampled) < len(frame)
    # Evaluation callers use the unsampled frame directly.
    assert len(frame) == 4
