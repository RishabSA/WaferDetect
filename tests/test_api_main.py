import base64

import numpy as np

from scripts.api.plots import field_png


def test_field_png_is_decodable() -> None:
    encoded = field_png(np.random.default_rng(0).random((32, 32)))
    decoded = base64.b64decode(encoded)
    assert decoded[:8] == b"\x89PNG\r\n\x1a\n"
