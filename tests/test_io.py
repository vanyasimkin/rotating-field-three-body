import json

import pytest

from rotating_field_three_body.io import read_centers


def test_read_centers_rejects_nonfinite_json(tmp_path):
    path = tmp_path / "centers.json"
    path.write_text(json.dumps({"centers": [[0, 0, 0], [float("nan"), 1, 2]]}))
    with pytest.raises(ValueError, match="NaN or infinite"):
        read_centers(path)
