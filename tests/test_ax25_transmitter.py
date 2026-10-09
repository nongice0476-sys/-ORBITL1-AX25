
import unittest

from src.ax25 import build_ui_frame
from src.ax25_hdlc import HDLCStreamDecoder
from src.ax25_transmitter import (
    bytes_to_bits,
    bit_stuff,
    encode_hdlc,
    nrzi_encode,
    nrzi_decode,
)


class TestAX25Transmitter(unittest.TestCase):

    def test_lsb_first(self):
        self.assertEqual(
            bytes_to_bits(b"\x03"),
            [1, 1, 0, 0, 0, 0, 0, 0],
        )

    def test_bit_stuffing(self):
        self.assertEqual(
            bit_stuff([1, 1, 1, 1, 1]),
            [1, 1, 1, 1, 1, 0],
        )

    def test_nrzi_known_vector(self):
        bits = [0, 1, 1, 0, 0, 1]
        expected = [1, 1, 1, 0, 1, 1]
        self.assertEqual(nrzi_encode(bits), expected)

    def test_nrzi_round_trip(self):
        bits = [0, 1, 0, 0, 1, 1, 1, 0]
        encoded = nrzi_encode(bits)
        self.assertEqual(nrzi_decode(encoded), bits)

    def test_complete_round_trip(self):
        frame = build_ui_frame(
            "GROUND", "ORBITL-1",
            b"SEQ=5;BAT=7.45V"
        )

        hdlc_bits = encode_hdlc(frame)
        encoded = nrzi_encode(hdlc_bits)
        recovered_bits = nrzi_decode(encoded)

        receiver = HDLCStreamDecoder()
        recovered_frames = receiver.feed(recovered_bits)

        self.assertEqual(
            recovered_frames,
            [frame[1:-3]],
        )


if __name__ == "__main__":
    unittest.main()
