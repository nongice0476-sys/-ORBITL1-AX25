
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


def encode_hdlc_for_test(body: bytes):
    """Small independent test-frame generator."""
    flag = [0, 1, 1, 1, 1, 1, 1, 0]
    stuffed = []
    ones = 0

    for byte in body:
        for i in range(8):
            bit = (byte >> i) & 1
            stuffed.append(bit)

            if bit:
                ones += 1
                if ones == 5:
                    stuffed.append(0)
                    ones = 0
            else:
                ones = 0

    return flag + stuffed + flag


class TestHDLCStreamDecoder(unittest.TestCase):

    def make_frame(self, payload):
        return build_ui_frame(
            "GROUND", "ORBITL-1", payload
        )

    def test_single_frame(self):
        frame = self.make_frame(b"SEQ=1")
        decoder = HDLCStreamDecoder()

        result = decoder.feed(
            encode_hdlc_for_test(frame[1:-1])
        )

        self.assertEqual(result, [frame[1:-3]])

    def test_multiple_frames(self):
        frames = [
            self.make_frame(b"SEQ=1"),
            self.make_frame(b"SEQ=2"),
        ]

        stream = []
        for frame in frames:
            stream.extend(
                encode_hdlc_for_test(frame[1:-1])
            )

        decoder = HDLCStreamDecoder()
        result = decoder.feed(stream)

        self.assertEqual(
            result,
            [frame[1:-3] for frame in frames]
        )

    def test_corrupted_frame_rejected(self):
        frame = self.make_frame(b"SEQ=3")
        body = bytearray(frame[1:-1])

        body[18] ^= 0x01

        decoder = HDLCStreamDecoder()
        result = decoder.feed(
            encode_hdlc_for_test(body)
        )

        self.assertEqual(result, [])

    def test_invalid_bit_rejected(self):
        decoder = HDLCStreamDecoder()

        with self.assertRaises(ValueError):
            decoder.feed_bit(2)

    def test_chunked_stream(self):
        frame = self.make_frame(b"SEQ=4")
        stream = encode_hdlc_for_test(frame[1:-1])

        decoder = HDLCStreamDecoder()
        result = []

        for i in range(0, len(stream), 7):
            result.extend(
                decoder.feed(stream[i:i + 7])
            )

        self.assertEqual(result, [frame[1:-3]])


if __name__ == "__main__":
    unittest.main()
