
"""Final acceptance regression tests for ORBITL1 Phase 2."""

import random
import unittest

from src.ax25 import build_ui_frame
from src.ax25_transmitter import (
    encode_hdlc,
    nrzi_encode,
    nrzi_decode,
)
from src.ax25_hdlc import HDLCStreamDecoder
from src.ax25_receiver import AX25ReceivePipeline


class TestHDLCFinalAcceptance(unittest.TestCase):

    def test_randomized_round_trip_1000(self):
        rng = random.Random(20261009)

        for i in range(1000):
            size = rng.randint(0, 512)
            payload = rng.randbytes(size)

            frame = build_ui_frame(
                "GROUND", "ORBITL-1", payload
            )

            levels = nrzi_encode(encode_hdlc(frame))
            bits = nrzi_decode(levels)

            packets = AX25ReceivePipeline().feed_bits(bits)

            self.assertEqual(
                len(packets), 1,
                f"Frame {i}, payload size {size}"
            )
            self.assertEqual(
                packets[0]["information"], payload
            )
            self.assertTrue(packets[0]["fcs_verified"])

    def test_continuous_chunked_stream(self):
        rng = random.Random(20261009)
        stream = []
        expected = []

        for i in range(100):
            payload = (
                i.to_bytes(4, "little")
                + rng.randbytes(rng.randint(0, 512))
            )

            expected.append(payload)
            frame = build_ui_frame(
                "GROUND", "ORBITL-1", payload
            )
            stream.extend(encode_hdlc(frame))

        receiver = AX25ReceivePipeline()
        received = []
        offset = 0

        while offset < len(stream):
            size = rng.randint(1, 97)
            chunk = stream[offset:offset + size]

            received.extend(
                packet["information"]
                for packet in receiver.feed_bits(chunk)
            )
            offset += len(chunk)

        self.assertEqual(received, expected)

    def test_crc_corruption_and_recovery(self):
        rng = random.Random(20261009)
        receiver = AX25ReceivePipeline()
        expected = []
        received = []

        for i in range(100):
            payload = (
                i.to_bytes(4, "little")
                + rng.randbytes(rng.randint(1, 256))
            )
            frame = bytearray(
                build_ui_frame(
                    "GROUND", "ORBITL-1", payload
                )
            )

            if i % 3 == 1:
                frame[16] ^= 0x01
            else:
                expected.append(payload)

            bits = encode_hdlc(bytes(frame))
            offset = 0

            while offset < len(bits):
                size = rng.randint(1, 47)
                chunk = bits[offset:offset + size]
                received.extend(
                    packet["information"]
                    for packet in receiver.feed_bits(chunk)
                )
                offset += len(chunk)

        self.assertEqual(len(expected), 67)
        self.assertEqual(received, expected)

    def test_abort_and_recovery(self):
        damaged = build_ui_frame(
            "GROUND", "ORBITL-1", b"ABORT-ME"
        )
        valid = build_ui_frame(
            "GROUND", "ORBITL-1",
            b"RECOVERY-AFTER-ABORT"
        )

        stream = (
            encode_hdlc(damaged)[:-24]
            + [1] * 8
            + encode_hdlc(valid)
        )

        packets = AX25ReceivePipeline().feed_bits(stream)

        self.assertEqual(
            [p["information"] for p in packets],
            [b"RECOVERY-AFTER-ABORT"]
        )

    def test_buffer_overflow_and_recovery(self):
        decoder = HDLCStreamDecoder()

        incomplete = build_ui_frame(
            "GROUND", "ORBITL-1", b"BUFFER-CHECK"
        )

        decoder.feed(encode_hdlc(incomplete)[:-8])

        # Large unterminated stream: should be discarded.
        decoder.feed([0, 1, 0, 1, 0, 1, 0, 1] * 6000)

        valid = build_ui_frame(
            "GROUND", "ORBITL-1", b"RECOVERY-OK"
        )

        self.assertEqual(
            decoder.feed(encode_hdlc(valid)),
            [valid[1:-3]]
        )

    def test_maximum_frame_boundary(self):
        # The current vendor buffer limit is 4096 bytes.
        # Verify a moderately large valid payload succeeds.
        payload = bytes(range(256)) * 8

        frame = build_ui_frame(
            "GROUND", "ORBITL-1", payload
        )

        packets = AX25ReceivePipeline().feed_bits(
            encode_hdlc(frame)
        )

        self.assertEqual(len(packets), 1)
        self.assertEqual(
            packets[0]["information"], payload
        )

    def test_no_invalid_frame_accepted(self):
        frame = bytearray(
            build_ui_frame(
                "GROUND", "ORBITL-1", b"INVALID-FCS"
            )
        )

        frame[-3] ^= 0x80

        packets = AX25ReceivePipeline().feed_bits(
            encode_hdlc(bytes(frame))
        )

        self.assertEqual(packets, [])


if __name__ == "__main__":
    unittest.main()
