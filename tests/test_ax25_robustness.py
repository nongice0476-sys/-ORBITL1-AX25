
import unittest

from src.ax25 import build_ui_frame
from src.ax25_transmitter import encode_hdlc
from src.ax25_hdlc import HDLCStreamDecoder


def frame(payload):
    return build_ui_frame("GROUND", "ORBITL-1", payload)


class TestAX25Robustness(unittest.TestCase):

    def test_binary_payload(self):
        original = frame(bytes(range(256)))
        recovered = HDLCStreamDecoder().feed(
            encode_hdlc(original)
        )
        self.assertEqual(recovered, [original[1:-3]])

    def test_corrupted_frame_recovery(self):
        a = frame(b"SEQ=1")
        bad = bytearray(frame(b"SEQ=2"))
        c = frame(b"SEQ=3")
        bad[19] ^= 1

        stream = (
            encode_hdlc(a)
            + encode_hdlc(bytes(bad))
            + encode_hdlc(c)
        )

        recovered = HDLCStreamDecoder().feed(stream)
        self.assertEqual(
            recovered, [a[1:-3], c[1:-3]]
        )

    def test_truncated_frame_with_reset(self):
        damaged = encode_hdlc(frame(b"SEQ=10"))
        valid = frame(b"SEQ=11")

        decoder = HDLCStreamDecoder()
        self.assertEqual(
            decoder.feed(damaged[:len(damaged)//2]), []
        )
        decoder.reset()
        self.assertEqual(
            decoder.feed(encode_hdlc(valid)),
            [valid[1:-3]]
        )

    def test_automatic_resynchronization(self):
        damaged = encode_hdlc(frame(b"SEQ=20"))
        valid = frame(b"SEQ=21")
        flag = [0, 1, 1, 1, 1, 1, 1, 0]

        stream = (
            damaged[:len(damaged)//2]
            + flag
            + encode_hdlc(valid)
        )

        self.assertEqual(
            HDLCStreamDecoder().feed(stream),
            [valid[1:-3]]
        )

    def test_noise_recovery(self):
        valid = frame(b"SEQ=30")
        noise = [1,0,1,0,0,1,1,0,0,0,1,0,1]

        self.assertEqual(
            HDLCStreamDecoder().feed(
                noise + encode_hdlc(valid)
            ),
            [valid[1:-3]]
        )

    def test_missing_opening_flag(self):
        bits = encode_hdlc(frame(b"SEQ=31"))

        self.assertEqual(
            HDLCStreamDecoder().feed(bits[8:]), []
        )

    def test_missing_closing_flag(self):
        bits = encode_hdlc(frame(b"SEQ=32"))

        self.assertEqual(
            HDLCStreamDecoder().feed(bits[:-8]), []
        )


if __name__ == "__main__":
    unittest.main()
