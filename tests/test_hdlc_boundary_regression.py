
import random
import unittest

from src.ax25 import build_ui_frame
from src.ax25_transmitter import encode_hdlc
from src.ax25_hdlc import HDLCStreamDecoder


class TestHDLCBoundaryRegression(unittest.TestCase):

    def test_frame12_closing_flag(self):
        rng = random.Random(20261009)

        for _ in range(13):
            size = rng.randint(0, 512)
            payload = rng.randbytes(size)

        frame = build_ui_frame(
            "GROUND", "ORBITL-1", payload
        )

        recovered = HDLCStreamDecoder().feed(
            encode_hdlc(frame)
        )

        self.assertEqual(
            recovered,
            [frame[1:-3]]
        )


if __name__ == "__main__":
    unittest.main()
