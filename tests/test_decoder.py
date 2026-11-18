import numpy as np

from pathsnap.data_pipeline.candidates import Candidate
from pathsnap.route_decoder.hmm import log_emission_probability
from pathsnap.route_decoder.viterbi import viterbi_decode


def test_viterbi_prefers_connected_sequence_and_preserves_missing_observation() -> None:
    groups = [
        [Candidate(0, 1, 1.0, 0, 0.5), Candidate(0, 2, 1.0, 1, 0.5)],
        [Candidate(1, 3, 1.0, 0, 0.5), Candidate(1, 4, 1.0, 1, 0.5)],
        [],
        [Candidate(3, 7, 1.0, 0, 0.5)],
    ]
    emissions = [[-0.1, -0.2], [-0.2, -0.1], [], [-0.1]]

    def transition(previous: int, current: int, _: int) -> float:
        return 0.0 if (previous, current) == (1, 3) else -10.0

    result = viterbi_decode(groups, emissions, transition)
    assert result.predicted_arc_ids[:2] == [1, 3]
    assert result.predicted_arc_ids[2] is None
    assert result.predicted_arc_ids[3] == 7


def test_emission_penalizes_far_candidates() -> None:
    close = Candidate(0, 1, 2.0, 0, 0.2)
    far = Candidate(0, 2, 50.0, 1, 0.2)
    assert log_emission_probability(close, 0.8) > log_emission_probability(far, 0.8)
