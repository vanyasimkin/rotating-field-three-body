from pathlib import Path

import numpy as np

from rotating_field_three_body.api import predict_cluster_energy


class ZeroModel:
    def predict(self, x):
        return np.zeros(len(x))


def test_cluster_api_pair_plus_zero_triplets():
    root = Path(__file__).resolve().parents[1]
    pair_map = root / "data" / "scm_pair_orientation_map_lmax6_beta2p5.npz"
    d = 2.0e-6
    centers = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.4 * d, 0.0, 0.0],
            [0.3 * d, 1.5 * d, 0.2 * d],
            [0.8 * d, 0.4 * d, 1.3 * d],
        ]
    )
    payload = {
        "feature_mode": "invariant",
        "global_model": ZeroModel(),
        "compact_model": ZeroModel(),
        "compact_cutoff": 1.8,
        "target_scale": 1e21,
        "feature_names": [],
    }
    result = predict_cluster_energy(
        centers,
        diameter=d,
        pair_map=pair_map,
        model=payload,
        check_domain=True,
    )
    assert result["n_pairs"] == 6
    assert result["n_triplets"] == 4
    assert np.isclose(result["triplet_energy_J"], 0.0)
    assert np.isclose(result["pair_plus_ml3b_J"], result["pair_energy_J"])
